import time


def new_run_id(prefix: str = "run") -> str:
    """Generate a monotonic, timestamp-based run identifier."""
    return f"{prefix}-{int(time.time())}"
