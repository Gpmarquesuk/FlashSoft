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
