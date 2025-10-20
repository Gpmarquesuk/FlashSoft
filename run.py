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
    state.log({"event": "router_models", "models": router.models, "fallbacks": router.fallbacks})

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

    review_md = run_reviewer(router, repo_path, context="MVP 4 nÃ³s")
    write_review(repo_path, review_md)
    commit_push(repo_path, f"[autobot] add REVIEW.md - {run_id}", branch)
    state.log({"event": "reviewer_done"})

    pr_body = run_pr_integrator(router, pr_title=f"Autobot PR {run_id}", pr_body=review_md)
    pr_number = open_pr(branch, f"Autobot PR {run_id}", pr_body)
    state.log({"event": "pr_opened", "pr_number": pr_number})
    print(f"PR aberto: #{pr_number}")

if __name__ == "__main__":
    main()
