import time

def new_run_id(prefix="run"):
    return f"{prefix}-{int(time.time())}"
