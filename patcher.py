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
