from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterable


class JSONLLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, payload: dict) -> None:
        payload = {"ts": time.time(), **payload}
        with self.path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


class MetricsCollector:
    def __init__(self, path: Path) -> None:
        self.logger = JSONLLogger(path)

    def record(self, metric: str, value: float, **extra: Any) -> None:
        self.logger.log({"metric": metric, "value": value, **extra})


class CompositeLogger:
    def __init__(self, *loggers: JSONLLogger) -> None:
        self.loggers = loggers

    def log(self, payload: dict) -> None:
        for logger in self.loggers:
            logger.log(payload)
