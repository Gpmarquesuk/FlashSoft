import json, time, pathlib

class RunState:
    def __init__(self, run_id: str, logdir: str = "./logs"):
        self.run_id = run_id
        self.path = pathlib.Path(logdir)
        self.path.mkdir(parents=True, exist_ok=True)
        self.file = self.path / f"{run_id}.jsonl"

    def log(self, event: dict):
        event["ts"] = time.time()
        with open(self.file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
