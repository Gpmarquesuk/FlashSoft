import os, sys, json, time, uuid, subprocess
from pathlib import Path
from datetime import datetime

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

class Orchestrator:
    def __init__(self, repo_dir: str):
        self.repo = Path(repo_dir).resolve()
        self.logs = self.repo / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)

    # ---------- helpers ----------
    def _ensure_files(self):
        """Garante que prompts/planner_coder.md exista (cria default se faltar)."""
        prompts = self.repo / "prompts"
        prompts.mkdir(parents=True, exist_ok=True)
        planner_md = prompts / "planner_coder.md"
        if not planner_md.exists() or planner_md.stat().st_size < 40:
            planner_md.write_text(DEFAULT_PLANNER_PROMPT, encoding="utf-8")

    def _latest_run_log(self):
        files = sorted(self.logs.glob("run-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0] if files else None

    def _parse_outcome(self, log_path: Path):
        pr = None; pytest_ok = None; events = []
        try:
            for line in log_path.read_text(encoding="utf-8").splitlines():
                try:
                    obj = json.loads(line)
                    ev = obj.get("event"); 
                    if ev: events.append(ev)
                    if ev == "pr_opened": pr = obj.get("pr_number")
                    if ev == "pytest_result": pytest_ok = obj.get("ok")
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
        lines = []
        lines.append(f"# Orchestrator Report — {datetime.utcnow().isoformat()}Z")
        lines.append(f"- run_id: `{run_id}`")
        lines.append(f"- outlog: `{outlog.name if outlog else '-'}`")
        lines.append("## Decisions")
        for i, d in enumerate(decisions, 1):
            lines.append(f"{i}. action={d['action']} reason={d['reason']}")
        lines.append("## Outcome")
        lines.append(json.dumps(outcome, ensure_ascii=False, indent=2))
        md.write_text("\n".join(lines), encoding="utf-8")

    # ---------- policy ----------
    def _decide(self, combined_text: str, outcome: dict, context: dict):
        text = (combined_text or ""); t = text.lower()
        events = outcome.get("events") or []

        # (A) branch já existe
        if ("already exists" in t and "branch" in t) or ("fatal:" in t and "branch named" in t and "already exists" in t):
            return "new_branch_suffix", "branch exists -> add timestamp"

        # (B) push rejeitado
        if "failed to push" in t or "fetch first" in t:
            return "git_sync", "push rejected -> fetch+rebase"

        # (C) planner não-JSON
        if "jsondecodeerror" in t or "saída sem json" in t or "resposta sem json" in t:
            if not context.get("forced_json"):
                return "force_json", "planner returned non-JSON -> FORCE_JSON=1"

        # (D) pytest fail
        if "pytest" in t and "failed" in t:
            return "retry", "pytest failed -> retry once"

        # (E) early-crash: sem progresso
        if events and set(events).issubset({"router_models", "start"}):
            if not context.get("forced_json"):
                return "force_json", "early crash/no progress -> FORCE_JSON=1"
            if not context.get("switched_planner"):
                return "switch_planner", "still no progress after FORCE_JSON -> switch planner to fallback"
            return "retry_unknown", "still no progress after switch -> retry"

        # (F) fallback
        return "retry_unknown", "fallback attempt"

    # ---------- loop ----------
    def run(self, spec_path: str, branch: str, max_attempts: int = 3, extra_env: dict | None = None):
        self._ensure_files()  # <<< garante prompt do planner

        run_label = f"orch-{int(time.time())}-{uuid.uuid4().hex[:6]}"
        decisions = []
        ctx = {"forced_json": False, "switched_planner": False}

        env_base = os.environ.copy()
        if extra_env: env_base.update(extra_env)

        fallback_planner = os.getenv("MODEL_FALLBACK_PLANNER", "google/gemini-2.5-pro")
        cur_branch = branch
        outlog = None

        for attempt in range(1, max_attempts + 1):
            env = env_base.copy()
            if ctx["forced_json"]: env["FORCE_JSON"] = "1"
            if ctx["switched_planner"]: env["MODEL_PLANNER"] = fallback_planner

            cmd = [sys.executable, "run.py", "--spec", spec_path, "--branch", cur_branch]
            proc = subprocess.run(cmd, cwd=self.repo, capture_output=True, text=True)
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")

            outlog = self.logs / f"ORCH_{run_label}_out.txt"
            with outlog.open("a", encoding="utf-8") as f:
                f.write(f"\n===== attempt {attempt} =====\n{combined}\n")

            latest = self._latest_run_log()
            outcome = self._parse_outcome(latest) if latest else {}

            if outcome.get("pr"):
                self._write_report(run_label, decisions, outcome, outlog)
                print(f"[orch] SUCCESS: PR #{outcome['pr']}  (attempt {attempt})")
                return 0

            action, reason = self._decide(combined, outcome, ctx)
            decisions.append({"action": action, "reason": reason})

            if action == "force_json":
                ctx["forced_json"] = True; continue
            if action == "switch_planner":
                ctx["switched_planner"] = True; continue
            if action == "new_branch_suffix":
                ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                cur_branch = f"{branch}-{ts}"; continue
            if action == "git_sync":
                self._git_sync(); continue
            # retry/retry_unknown => segue loop

        latest = self._latest_run_log()
        outcome = self._parse_outcome(latest) if latest else {}
        self._write_report(run_label, decisions, outcome, outlog)
        print("[orch] FAILED after attempts:", max_attempts)
        return 1
