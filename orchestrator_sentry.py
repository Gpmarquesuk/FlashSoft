import os
import sys
import json
import time
import uuid
import subprocess
import traceback
from pathlib import Path
from datetime import datetime

import yaml
from dotenv import load_dotenv

load_dotenv()

from llm_client import safe_json_extract
from router import Router
DEFAULT_PLANNER_PROMPT = """You are Planner-Coder. Read SPEC and current repo file list.
Return STRICT JSON ONLY with:
{
  "patches": [
    {"path": "<relative path>", "op": "upsert", "content": "<full file content>"},
    {"path": "<relative path>", "op": "delete"}
  ],
  "test_plan": ["pytest test names or descriptions"]
}
No prose, no Markdown, JSON object only.
"""

SUPERVISOR_SYSTEM_PROMPT = (
    "You are GPT-5 Thinker, the senior supervisor of the FlashSoft factory. "
    "Based on the latest run logs, choose the best next action for the orchestrator. "
    "Respond STRICT JSON with keys {\"action\": <choice>, \"reason\": <string>} where action is one of: "
    "force_json, switch_planner, new_branch_suffix, git_sync, retry, retry_unknown."
)


class Orchestrator:
    def __init__(self, repo_dir: str):
        self.repo = Path(repo_dir).resolve()
        self.logs = self.repo / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)
        self.supervisor_router = Router()

    # -------- infra util --------
    def _ensure_files(self):
        prompts = self.repo / "prompts"
        prompts.mkdir(parents=True, exist_ok=True)
        planner_md = prompts / "planner_coder.md"
        if not planner_md.exists() or planner_md.stat().st_size < 40:
            planner_md.write_text(DEFAULT_PLANNER_PROMPT, encoding="utf-8")

    def _precheck_spec(self, spec_path: str):
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
            return True, ""
        except Exception as e:
            return False, f"YAML invalid: {e}"

    def _latest_run_log(self) -> Path | None:
        files = sorted(self.logs.glob("run-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0] if files else None

    def _parse_outcome(self, log_path: Path):
        pr = None
        pytest_ok = None
        events = []
        try:
            for line in log_path.read_text(encoding="utf-8").splitlines():
                try:
                    obj = json.loads(line)
                    ev = obj.get("event")
                    if ev:
                        events.append(ev)
                    if ev == "pr_opened":
                        pr = obj.get("pr_number")
                    if ev == "pytest_result":
                        pytest_ok = obj.get("ok")
                except Exception:
                    pass
        except Exception:
            pass
        return {"pr": pr, "pytest_ok": pytest_ok, "events": events}

    def _git_sync(self):
        subprocess.run(["git", "fetch", "origin"], cwd=self.repo, check=False)
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=self.repo, check=False)

    def _write_report(self, run_id: str, decisions: list, outcome: dict, outlog):
        md = self.logs / f"ORCH_{run_id}.md"
        lines = [
            f"# Orchestrator Report - {datetime.utcnow().isoformat()}Z",
            f"- run_id: {run_id}",
            f"- outlog: {outlog.name if outlog else '-'}",
            "## Decisions",
        ]
        for i, d in enumerate(decisions, 1):
            lines.append(f"{i}. action={d['action']} reason={d['reason']}")
        lines.append("## Outcome")
        lines.append(json.dumps(outcome, ensure_ascii=False, indent=2))
        md.write_text("\n".join(lines), encoding="utf-8")

    # -------- decision policy --------
    def _decide(self, combined_text: str, outcome: dict, context: dict):
        text = combined_text or ""
        t = text.lower()
        events = outcome.get("events") or []
        if ("already exists" in t and "branch" in t) or (
            "fatal:" in t and "branch named" in t and "already exists" in t
        ):
            return "new_branch_suffix", "branch exists -> add timestamp"
        if "failed to push" in t or "fetch first" in t:
            return "git_sync", "push rejected -> fetch+rebase"
        if "jsondecodeerror" in t or "saida sem json" in t or "resposta sem json" in t:
            if not context.get("forced_json"):
                return "force_json", "planner non-JSON -> FORCE_JSON=1"
        if "pytest" in t and "failed" in t:
            return "retry", "pytest failed -> retry once"
        if events and set(events).issubset({"router_models", "start"}):
            if not context.get("forced_json"):
                return "force_json", "early-crash/no progress -> FORCE_JSON=1"
            if not context.get("switched_planner"):
                return "switch_planner", "no progress after FORCE_JSON -> switch planner to fallback"
            return "retry_unknown", "still no progress after switch -> retry"
        return "retry_unknown", "fallback attempt"

    def _supervisor_decision(self, attempt: int, combined_text: str, outcome: dict, context: dict):
        allowed = [
            "force_json",
            "switch_planner",
            "new_branch_suffix",
            "git_sync",
            "retry",
            "retry_unknown",
        ]
        payload = {
            "attempt": attempt,
            "tail": (combined_text or "")[-2000:],
            "outcome": outcome,
            "context": context,
            "allowed_actions": allowed,
        }
        try:
            response = self.supervisor_router.call(
                "supervisor",
                SUPERVISOR_SYSTEM_PROMPT,
                json.dumps(payload, ensure_ascii=False, indent=2),
                max_completion=400,
                force_json=True,
            )
            data = safe_json_extract(response)
            action = data.get("action")
            reason = data.get("reason", "")
            if action in allowed:
                return action, reason or "supervisor decision"
        except Exception:
            pass
        return None, None

    # -------- run loop --------
    def run(self, spec_path: str, branch: str, max_attempts: int | None = None, extra_env: dict | None = None):
        self._ensure_files()
        ok, msg = self._precheck_spec(spec_path)
        if not ok:
            print("[orch] SPEC invalid:", msg)
            return 2

        run_label = f"orch-{int(time.time())}-{uuid.uuid4().hex[:6]}"
        decisions = []
        ctx = {"forced_json": False, "switched_planner": False}
        env_base = os.environ.copy()
        if extra_env:
            env_base.update(extra_env)
        fallback_planner = os.getenv("MODEL_FALLBACK_PLANNER", "google/gemini-2.5-pro")
        cur_branch = branch
        outlog = None
        max_attempts = max_attempts or int(os.getenv("ORCH_MAX_ATTEMPTS", "6"))

        for attempt in range(1, max_attempts + 1):
            env = env_base.copy()
            if ctx["forced_json"]:
                env["FORCE_JSON"] = "1"
            if ctx["switched_planner"]:
                env["MODEL_PLANNER"] = fallback_planner

            cmd = [sys.executable, "run.py", "--spec", spec_path, "--branch", cur_branch]
            proc = subprocess.run(cmd, cwd=self.repo, capture_output=True, text=True)
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")

            outlog = self.logs / f"ORCH_{run_label}_out.txt"
            with outlog.open("a", encoding="utf-8") as f:
                f.write(f"\n===== attempt {attempt} =====\n{combined}\n")

            latest = self._latest_run_log()
            outcome = self._parse_outcome(latest) if latest else {}

            try:
                tail = "\n".join((combined.strip().splitlines() or [])[-20:])
                if tail:
                    print(f"[orch][attempt {attempt}] tail:\n{tail}\n")
            except Exception:
                pass

            if outcome.get("pr"):
                self._write_report(run_label, decisions, outcome, outlog)
                print(f"[orch] SUCCESS: PR #{outcome['pr']}  (attempt {attempt})")
                return 0

            supervisor_action, supervisor_reason = self._supervisor_decision(
                attempt, combined, outcome, ctx
            )
            if supervisor_action:
                action, reason = supervisor_action, supervisor_reason
            else:
                action, reason = self._decide(combined, outcome, ctx)

            decisions.append({"action": action, "reason": reason})
            if action == "force_json":
                ctx["forced_json"] = True
                continue
            if action == "switch_planner":
                ctx["switched_planner"] = True
                continue
            if action == "new_branch_suffix":
                ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                cur_branch = f"{branch}-{ts}"
                continue
            if action == "git_sync":
                self._git_sync()
                continue
            # for retry / retry_unknown we just loop automatically

        latest = self._latest_run_log()
        outcome = self._parse_outcome(latest) if latest else {}
        self._write_report(run_label, decisions, outcome, outlog)
        if outlog and outlog.exists():
            try:
                print("[orch] last outlog tail:")
                print("\n".join(outlog.read_text(encoding="utf-8").splitlines()[-40:]))
            except Exception:
                pass
        print("[orch] FAILED after attempts:", max_attempts)
        return 1
