import subprocess
from router import Router

def git_diff(repo_path: str) -> str:
    out = subprocess.check_output(["git", "-C", repo_path, "diff"], text=True, encoding="utf-8")
    return out

def run_reviewer(router: Router, repo_path: str, context: str = "") -> str:
    with open("prompts/reviewer.md", "r", encoding="utf-8") as f:
        system = f.read()
    diff = git_diff(repo_path)
    user = f"""Diff a revisar (unified diff):

```diff
{diff}
```

Contexto:
{context}

Produza Markdown curto seguindo o formato pedido.
"""
    out = router.call("reviewer", system, user, max_completion=1500)
    return out
