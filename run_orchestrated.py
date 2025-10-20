import argparse, sys, os
from orchestrator_sentry import Orchestrator

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--branch", required=True)
    args = ap.parse_args()

    orch = Orchestrator(repo_dir=".")
    code = orch.run(spec_path=args.spec, branch=args.branch, max_attempts=3)
    sys.exit(code)

if __name__ == "__main__":
    main()
