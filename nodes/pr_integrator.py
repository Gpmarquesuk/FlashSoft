from router import Router


def run_pr_integrator(router: Router, pr_title: str, default_body: str, metadata: dict | None = None) -> str:
    metadata = metadata or {}
    system = (
        'You are the release manager at FlashSoft. Produce a concise PR body in Markdown summarizing the change, '
        'referencing automated test and QA results, and highlighting risks and next steps. Keep it under 350 words.'
    )
    user = (
        f'PR Title: {pr_title}\n\n'
        f'Default body supplied by tooling:\n{default_body}\n\n'
        f'Run metadata (JSON):\n{metadata}'
    )
    try:
        return router.call('release', system, user, max_completion=600)
    except Exception:
        return default_body
