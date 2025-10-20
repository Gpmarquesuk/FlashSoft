import os, sys, json, time, uuid, subprocess, re
from pathlib import Path
from datetime import datetime

class Orchestrator:
    """
    Orquestrador sentinela:
      - Executa run.py como subprocesso
      - Observa logs em ./logs/run-*.jsonl
      - Detecta falhas comuns e toma decisões:
          * JSON/planner: define FORCE_JSON=1 e reexecuta
          * Branch já existe: cria sufixo -<timestamp>
          * Push reject: git fetch + pull --rebase e reexecuta push
          * Pytest fail: reexecuta uma vez (deixa detalhes no log)
      - Para quando abre PR com sucesso ou após max tentativas
      - Escreve relatório em logs/ORCH_<run>.md
    """
    def __init__(self, repo_dir: str):
        self.repo = Path(repo_dir).resolve()
        self.logs = self.repo / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)

    def _logfile_latest(self):
        files = sorted(self.logs.glob("run-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0] if files else None

    def _parse_run_outcome(self, log_path: Path):
        pr = None
        pytest_ok = None
        events = []
        try:
            for line in log_path.read_text(encoding="utf-8").splitlines():
                try:
                    obj = json.loads(line)
                    events.append(obj.get("event"))
                    if obj.get("event") == "pr_opened":
                        pr = obj.get("pr_number")
                    if obj.get("event") == "pytest_result":
                        pytest_ok = obj.get("ok")
                except Exception:
                    pass
        except Exception:
            pass
        return {"pr": pr, "pytest_ok": pytest_ok, "events": events}

    def _git_sync(self):
        subprocess.run(["git", "fetch", "origin"], cwd=self.repo, check=False)
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=self.repo, check=False)

    def _decide_from_text(self, text: str):
        t = text or ""
        if "branch named" in t and "already exists" in t:
            return ("new_branch_suffix", {})
        if "JSONDecodeError" in t or "Saída sem JSON" in t or "Resposta sem JSON" in t:
            return ("force_json", {})
        if "failed to push some refs" in t or "fetch first" in t:
            return ("git_sync", {})
        if "pytest" in t and "failed" in t.lower():
            return ("retry", {})
        return ("unknown", {})

    def _write_report(self, run_id: str, decisions: list, outcome: dict):
        md = self.logs / f"ORCH_{run_id}.md"
        lines = []
        lines.append(f"# Orchestrator Report — {datetime.utcnow().isoformat()}Z")
        lines.append(f"- run_id: `{run_id}`")
        lines.append("## Decisions")
        for i, d in enumerate(decisions, 1):
            lines.append(f"{i}. action={d['action']} reason={d['reason']}")
        lines.append("## Outcome")
        lines.append(json.dumps(outcome, ensure_ascii=False, indent=2))
        md.write_text("\n".join(lines), encoding="utf-8")

    def run(self, spec_path: str, branch: str, max_attempts: int = 3, extra_env: dict | None = None):
        run_label = f"orch-{int(time.time())}-{uuid.uuid4().hex[:6]}"
        decisions = []
        env_base = os.environ.copy()
        if extra_env:
            env_base.update(extra_env)

        cur_branch = branch
        force_json = False

        for attempt in range(1, max_attempts + 1):
            env = env_base.copy()
            if force_json:
                env["FORCE_JSON"] = "1"

            cmd = [sys.executable, "run.py", "--spec", spec_path, "--branch", cur_branch]
            proc = subprocess.run(cmd, cwd=self.repo, capture_output=True, text=True)
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            combined = stdout + "\n" + stderr

            latest = self._logfile_latest()
            outcome = self._parse_run_outcome(latest) if latest else {}

            # Sucesso se abriu PR
            if outcome.get("pr"):
                self._write_report(run_label, decisions, outcome)
                print(f"[orch] SUCCESS: PR #{outcome['pr']}  (attempt {attempt})")
                return 0

            # Falhou -> decidir
            action, params = self._decide_from_text(combined)
            if action == "new_branch_suffix":
                ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                cur_branch = f"{branch}-{ts}"
                decisions.append({"action": action, "reason": "branch already exists -> add timestamp"})
                continue
            if action == "force_json":
                force_json = True
                decisions.append({"action": action, "reason": "planner returned non-JSON -> FORCE_JSON=1"})
                continue
            if action == "git_sync":
                self._git_sync()
                decisions.append({"action": action, "reason": "push rejected/fetch first -> git fetch+rebase"})
                continue
            if action == "retry":
                decisions.append({"action": action, "reason": "pytest failure -> retry once"})
                continue

            # unknown -> uma última tentativa cega
            decisions.append({"action": "retry_unknown", "reason": "fallback attempt"})
            time.sleep(2)

        # Exausto
        latest = self._logfile_latest()
        outcome = self._parse_run_outcome(latest) if latest else {}
        self._write_report(run_label, decisions, outcome)
        print("[orch] FAILED after attempts:", max_attempts)
        return 1
