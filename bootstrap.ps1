param(
  [string]$RepoPath = "C:\Users\gpmar\Documents\FlashSoft",
  [bool]$CommitPush = $true,
  [bool]$Overwrite = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $RepoPath)) { throw "RepoPath não existe: $RepoPath" }
Set-Location $RepoPath

Write-Host "bootstrap.ps1 iniciado no diretório: $RepoPath" -ForegroundColor Cyan

function Write-File {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Content,
    [bool]$Overwrite = $true
  )
  $dir = Split-Path -Path $Path
  if ($dir -and -not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
  if (-not $Overwrite -and (Test-Path $Path)) { return }
  $Content | Out-File -FilePath $Path -Encoding UTF8 -Force
}

function Ensure-Dirs {
  [CmdletBinding()]
  param()
  @(
    "prompts",
    "nodes",
    "examples\specs",
    ".github\workflows",
    "logs"
  ) | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
  }
}

function Write-GitIgnore {
  [CmdletBinding()]
  param()
  $content = @'
.venv/
__pycache__/
*.pyc
.env
logs/
.tmp/
'@
  Write-File -Path ".gitignore" -Content $content -Overwrite $true
}

function Write-Requirements {
  [CmdletBinding()]
  param()
  $content = @'
openai>=1.45.0
python-dotenv>=1.0.1
PyGithub>=2.3.0
GitPython>=3.1.43
PyYAML>=6.0.2
tenacity>=8.3.0
rich>=13.7.1
pytest>=8.3.3
requests>=2.32.3
'@
  Write-File -Path "requirements.txt" -Content $content -Overwrite $true
}

function Write-Prompts {
  [CmdletBinding()]
  param()

  $planner = @'
Você é o PlannerCoder. Entrada: spec.yaml e snapshot do repo. Saída: JSON com patches e um test_plan.
Formato obrigatório:
{
  "patches": [
    {"path": "src/...", "content": "arquivo completo"}
  ],
  "test_plan": "casos de teste e critérios de aceitação"
}
Regras:
- Arquivos completos, não difs.
- Sem nada fora do JSON.
- Compilar e importar corretamente.
- Se a spec pedir, atualize README e CHANGELOG.
'@
  Write-File -Path "prompts\planner_coder.md" -Content $planner -Overwrite $true

  $tester = @'
Você é o Tester. Entrada: test_plan e lista de arquivos modificados. Saída: JSON com patches de testes.
Formato:
{
  "patches": [
    {"path": "tests/test_xxx.py", "content": "arquivo completo"}
  ]
}
Regras:
- Use pytest.
- Casos positivos e negativos.
- Sem nada fora do JSON.
'@
  Write-File -Path "prompts\tester.md" -Content $tester -Overwrite $true

  $reviewer = @'
Você é o Reviewer adversarial. Entrada: diff textual e contexto. Saída: Markdown curto com achados e sugestões patch-ready.
Formato:
# Review
- Risco 1: ...
- Risco 2: ...
## Sugestões de patch
(Se útil, inclua um trecho em formato diff)
Regras:
- Procure problemas de lógica, segurança, compatibilidade e performance.
- Sinalize onde faltam testes.
'@
  Write-File -Path "prompts\reviewer.md" -Content $reviewer -Overwrite $true
}

function Write-ExampleSpec {
  [CmdletBinding()]
  param()
  $spec = @'
feature: "add hello util and expose CLI"
acceptance:
  - running `python -m src.hello` prints "hello"
  - pytest passes
changes:
  summary: "create src/hello.py and update README"
  constraints:
    style: "pep8"
    min_coverage: 0.0
notes: |
  Keep it simple. No external deps.
'@
  Write-File -Path "examples\specs\sample_spec.yaml" -Content $spec -Overwrite $true
}

function Write-SmokeOpenRouter {
  [CmdletBinding()]
  param()
  $content = @'
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
)
model = os.getenv("MODEL_REVIEWER", "x-ai/grok-4-fast")
resp = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "Você é um verificador de ambiente"},
        {"role": "user", "content": "Responda com exatamente: OK"}
    ],
    temperature=0,
    max_tokens=5
)
print(resp.choices[0].message.content.strip())
'@
  Write-File -Path "smoke_openrouter.py" -Content $content -Overwrite $true
}

function Write-LLMClient {
  [CmdletBinding()]
  param()
  $content = @'
import os, json, re
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from openai import OpenAI

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES_PER_CALL", "2"))

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY ausente")

client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=BASE_URL)

def _headers():
    return {
        "HTTP-Referer": "https://example.com",
        "X-Title": "flashsoft-autobot-mvp"
    }

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential_jitter(1, 4))
def chat(model: str, system: str, user: str, temperature: float = 0.2, max_tokens: int = 2000) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        extra_headers=_headers(),
        timeout=TIMEOUT
    )
    return resp.choices[0].message.content

def safe_json_extract(text: str):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("Saída sem JSON")
    return json.loads(m.group(0))
'@
  Write-File -Path "llm_client.py" -Content $content -Overwrite $true
}

function Write-Router {
  [CmdletBinding()]
  param()
  $content = @'
import os
from llm_client import chat

BUDGET_TOKENS = int(os.getenv("MAX_TOKENS_TOTAL", "220000"))

class Router:
    def __init__(self):
        self.models = {
            "planner": os.getenv("MODEL_PLANNER", "anthropic/claude-sonnet-4.5"),
            "tester": os.getenv("MODEL_TESTER", "openai/gpt-4o"),
            "reviewer": os.getenv("MODEL_REVIEWER", "x-ai/grok-4-fast"),
            "pr": os.getenv("MODEL_PR", "google/gemini-2.5-pro"),
        }
        self.fallbacks = {
            "planner": os.getenv("MODEL_FALLBACK_PLANNER", "google/gemini-2.5-pro"),
            "tester": os.getenv("MODEL_FALLBACK_TESTER", "x-ai/grok-4-fast"),
            "reviewer": os.getenv("MODEL_FALLBACK_REVIEWER", "openai/o3-mini"),
            "pr": os.getenv("MODEL_FALLBACK_PR", "openai/gpt-4o"),
        }
        self.err_count = {k: 0 for k in self.models}
        self.tokens_spent = 0

    def estimate_tokens(self, text: str, completion_max: int) -> int:
        return int(len(text) / 4) + completion_max

    def call(self, node: str, system: str, user: str, max_completion: int = 2000) -> str:
        if self.tokens_spent > BUDGET_TOKENS:
            raise RuntimeError(f"Budget de tokens excedido: {self.tokens_spent}")
        primary = self.models[node]
        fallback = self.fallbacks[node]
        model_to_use = primary if self.err_count[node] < 3 else fallback
        try:
            est = self.estimate_tokens(system + user, max_completion)
            out = chat(model_to_use, system, user, max_tokens=max_completion)
            self.tokens_spent += est
            return out
        except Exception:
            self.err_count[node] += 1
            if self.err_count[node] >= 3 and model_to_use != fallback:
                out = chat(fallback, system, user, max_tokens=max_completion)
                self.tokens_spent += self.estimate_tokens(system + user, max_completion)
                return out
            raise
'@
  Write-File -Path "router.py" -Content $content -Overwrite $true
}

function Write-Patcher {
  [CmdletBinding()]
  param()
  $content = @'
import pathlib

def apply_patches(repo_root: str, patches: list):
    for p in patches:
        path = pathlib.Path(repo_root) / p["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(p["content"])

def write_review(repo_root: str, review_md: str):
    path = pathlib.Path(repo_root) / "REVIEW.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(review_md)
'@
  Write-File -Path "patcher.py" -Content $content -Overwrite $true
}

function Write-State {
  [CmdletBinding()]
  param()
  $content = @'
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
'@
  Write-File -Path "state.py" -Content $content -Overwrite $true
}

function Write-GitHubIntegration {
  [CmdletBinding()]
  param()
  $content = @'
import os, pathlib
from git import Repo
from github import Github

REPO_FULL = os.getenv("GITHUB_REPO_FULL")
BASE_BRANCH = os.getenv("GITHUB_BASE_BRANCH", "main")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def clone_repo(workdir: str) -> str:
    url = f"https://{GITHUB_TOKEN}:x-oauth-basic@github.com/{REPO_FULL}.git"
    local = pathlib.Path(workdir) / "repo"
    if local.exists():
        return str(local)
    Repo.clone_from(url, str(local))
    return str(local)

def create_branch(repo_path: str, new_branch: str):
    repo = Repo(repo_path)
    repo.git.fetch("--all")
    repo.git.checkout(BASE_BRANCH)
    repo.git.pull("origin", BASE_BRANCH)
    repo.git.checkout("-b", new_branch)

def commit_push(repo_path: str, message: str, branch: str):
    repo = Repo(repo_path)
    repo.git.add(all=True)
    if repo.is_dirty():
        repo.index.commit(message)
    origin = repo.remote(name="origin")
    origin.push(refspec=f"{branch}:{branch}")

def open_pr(branch: str, title: str, body: str):
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(REPO_FULL)
    pr = repo.create_pull(title=title, body=body, head=branch, base=BASE_BRANCH)
    return pr.number
'@
  Write-File -Path "github_integration.py" -Content $content -Overwrite $true
}

function Write-Nodes {
  [CmdletBinding()]
  param()

  $planner = @'
import yaml, json
from pathlib import Path
from router import Router
from llm_client import safe_json_extract

def run_planner_coder(router: Router, repo_path: str, spec_path: str) -> dict:
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    file_list = []
    for p in Path(repo_path).rglob("*.py"):
        rel = str(p.relative_to(repo_path))
        if rel.startswith(".venv") or rel.startswith(".git"):
            continue
        if len(file_list) > 60:
            break
        file_list.append(rel)

    with open("prompts/planner_coder.md", "r", encoding="utf-8") as f:
        system = f.read()

    user = f"""SPEC:
{yaml.safe_dump(spec, sort_keys=False)}
REPO_FILES:
{json.dumps(file_list, ensure_ascii=False, indent=2)}
Responda estritamente no JSON exigido.
"""
    out = router.call("planner", system, user, max_completion=3000)
    data = safe_json_extract(out)
    assert "patches" in data and "test_plan" in data, "JSON inválido do PlannerCoder"
    return data
'@
  Write-File -Path "nodes\planner_coder.py" -Content $planner -Overwrite $true

  $tester = @'
import json
from router import Router
from llm_client import safe_json_extract

def run_tester(router: Router, patches: list, test_plan: str) -> dict:
    files = [p["path"] for p in patches]
    with open("prompts/tester.md", "r", encoding="utf-8") as f:
        system = f.read()
    user = f"""Arquivos a serem testados:
{json.dumps(files, ensure_ascii=False)}
Plano de testes:
{test_plan}
Responda somente com o JSON esperado.
"""
    out = router.call("tester", system, user, max_completion=2500)
    data = safe_json_extract(out)
    assert "patches" in data, "JSON inválido do Tester"
    return data
'@
  Write-File -Path "nodes\tester.py" -Content $tester -Overwrite $true

  $reviewer = @'
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
'@
  Write-File -Path "nodes\reviewer.py" -Content $reviewer -Overwrite $true

  $pr = @'
from router import Router

def run_pr_integrator(router: Router, pr_title: str, pr_body: str) -> str:
    return pr_body
'@
  Write-File -Path "nodes\pr_integrator.py" -Content $pr -Overwrite $true
}

function Write-Utils {
  [CmdletBinding()]
  param()
  $content = @'
import time

def new_run_id(prefix="run"):
    return f"{prefix}-{int(time.time())}"
'@
  Write-File -Path "utils.py" -Content $content -Overwrite $true
}

function Write-Run {
  [CmdletBinding()]
  param()
  $content = @'
import os, argparse, subprocess
from dotenv import load_dotenv
load_dotenv()

from state import RunState
from router import Router
from github_integration import clone_repo, create_branch, commit_push, open_pr
from patcher import apply_patches, write_review
from nodes.planner_coder import run_planner_coder
from nodes.tester import run_tester
from nodes.reviewer import run_reviewer
from nodes.pr_integrator import run_pr_integrator
from utils import new_run_id

def run_pytests(repo_path: str):
    try:
        out = subprocess.run(["pytest", "-q"], cwd=repo_path, capture_output=True, text=True, timeout=300)
        ok = out.returncode == 0
        return ok, out.stdout + "\n" + out.stderr
    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="caminho para spec.yaml")
    parser.add_argument("--branch", default=None, help="nome da branch a criar")
    args = parser.parse_args()

    run_id = new_run_id()
    state = RunState(run_id)
    router = Router()

    workdir = os.getenv("WORKDIR", "/tmp/autobot_work")
    os.makedirs(workdir, exist_ok=True)
    repo_path = clone_repo(workdir)
    branch = args.branch or f"autobot/{run_id}"
    create_branch(repo_path, branch)

    state.log({"event": "start", "run_id": run_id, "branch": branch})

    data = run_planner_coder(router, repo_path, args.spec)
    patches = data["patches"]
    test_plan = data["test_plan"]
    state.log({"event": "planner_coder_done", "patch_count": len(patches)})

    apply_patches(repo_path, patches)

    tests = run_tester(router, patches, test_plan)
    test_patches = tests["patches"]
    apply_patches(repo_path, test_patches)
    state.log({"event": "tester_done", "test_patch_count": len(test_patches)})

    ok, test_output = run_pytests(repo_path)
    state.log({"event": "pytest_result", "ok": ok, "output": test_output[:6000]})

    commit_push(repo_path, f"[autobot] apply patches and tests - {run_id}", branch)

    review_md = run_reviewer(router, repo_path, context="MVP 4 nós")
    write_review(repo_path, review_md)
    commit_push(repo_path, f"[autobot] add REVIEW.md - {run_id}", branch)
    state.log({"event": "reviewer_done"})

    pr_body = run_pr_integrator(router, pr_title=f"Autobot PR {run_id}", pr_body=review_md)
    pr_number = open_pr(branch, f"Autobot PR {run_id}", pr_body)
    state.log({"event": "pr_opened", "pr_number": pr_number})
    print(f"PR aberto: #{pr_number}")

if __name__ == "__main__":
    main()
'@
  Write-File -Path "run.py" -Content $content -Overwrite $true
}

function Write-CI {
  [CmdletBinding()]
  param()
  $content = @'
name: autotest
on:
  pull_request:
    branches: [ "main" ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt || true
      - run: pip install pytest || true
      - run: pytest -q
'@
  Write-File -Path ".github\workflows\ci.yml" -Content $content -Overwrite $true
}

function Write-Docker {
  [CmdletBinding()]
  param()
  $docker = @'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "run.py", "--spec", "examples/specs/sample_spec.yaml"]
'@
  Write-File -Path "Dockerfile" -Content $docker -Overwrite $true

  $make = @'
run:
	python run.py --spec examples/specs/sample_spec.yaml

docker-build:
	docker build -t flashsoft-autobot .

docker-run:
	docker run --rm -it --env-file .env flashsoft-autobot
'@
  Write-File -Path "Makefile" -Content $make -Overwrite $true
}

function Git-CommitPush {
  [CmdletBinding()]
  param()
  try {
    git add .
    git commit -m "[flashsoft] bootstrap MVP 4-nodes via OpenRouter" | Out-Null
    git push origin main
    Write-Host "Commit e push realizados." -ForegroundColor Green
  } catch {
    Write-Host "Aviso: falha ao fazer push. Verifique credenciais." -ForegroundColor Yellow
  }
}

function Bootstrap-Project {
  [CmdletBinding()]
  param()
  Ensure-Dirs
  Write-GitIgnore
  Write-Requirements
  Write-Prompts
  Write-ExampleSpec
  Write-SmokeOpenRouter
  Write-LLMClient
  Write-Router
  Write-Patcher
  Write-State
  Write-GitHubIntegration
  Write-Nodes
  Write-Utils
  Write-Run
  Write-CI
  Write-Docker
  Write-Host "Arquivos do MVP escritos com sucesso." -ForegroundColor Green
}

# Execução
Bootstrap-Project
if ($CommitPush) { Git-CommitPush }
Write-Host "bootstrap.ps1 finalizado." -ForegroundColor Cyan
