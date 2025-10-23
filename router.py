import os
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from llm_client import chat, chat_json

BUDGET_TOKENS = int(os.getenv("MAX_TOKENS_TOTAL", "220000"))
_TRUTHY = {"1", "true", "t", "yes", "y", "on"}

FREE_MODEL_DEFAULTS = {
    "architect": "deepseek/deepseek-chat-v3.1:free",
    "planner": "deepseek/deepseek-chat-v3.1:free",
    "decomposer": "deepseek/deepseek-r1:free",
    "tester": "deepseek/deepseek-r1:free",
    "reviewer": "google/gemma-2-9b-it:free",
    "qa": "mistralai/mistral-small-24b-instruct-2501:free",
    "pr": "mistralai/mistral-small-24b-instruct-2501:free",
    "assistant": "deepseek/deepseek-chat-v3.1:free",
    "release": "mistralai/mistral-small-3.2-24b-instruct:free",
    "supervisor": "deepseek/deepseek-r1:free",
}

FREE_FALLBACK_DEFAULTS = {
    "architect": "qwen/qwen-2.5-coder-32b-instruct:free",
    "planner": "qwen/qwen-2.5-coder-32b-instruct:free",
    "decomposer": "mistralai/mistral-7b-instruct:free",
    "tester": "qwen/qwen3-coder:free",
    "reviewer": "deepseek/deepseek-r1-distill-llama-70b:free",
    "qa": "google/gemma-3n-e4b-it:free",
    "pr": "deepseek/deepseek-r1:free",
    "assistant": "qwen/qwen-2.5-coder-32b-instruct:free",
    "release": "deepseek/deepseek-r1:free",
    "supervisor": "qwen/qwen-2.5-coder-32b-instruct:free",
}

FREE_COMMITTEE_DEFAULTS = {
    "architect": ["qwen/qwen-2.5-coder-32b-instruct:free"],
    "planner": ["deepseek/deepseek-r1:free"],
    "decomposer": ["mistralai/mistral-7b-instruct:free"],
    "tester": ["mistralai/mistral-7b-instruct:free"],
    "reviewer": ["google/gemma-3n-e4b-it:free"],
    "qa": ["qwen/qwen-2.5-coder-32b-instruct:free"],
    "pr": ["mistralai/mistral-small-3.2-24b-instruct:free"],
    "assistant": ["deepseek/deepseek-r1:free"],
    "release": ["mistralai/mistral-small-24b-instruct-2501:free"],
    "supervisor": ["mistralai/mistral-small-24b-instruct-2501:free"],
}


class Router:
    """
    Multi-model routing layer that can rotate between specialists for each node.

    Committees may be configured via environment variables like
    `MODEL_PLANNER_COMMITTEE` = "modelA,modelB". The router tries each entry
    in order and promotes the first successful specialist so future calls
    start with the best performer.
    """

    def __init__(self, event_logger: Optional[Callable[[dict], None]] = None):
        self.models = {
            "architect": os.getenv(
                "MODEL_ARCHITECT",
                os.getenv("MODEL_PLANNER", "anthropic/claude-sonnet-4.5"),
            ),
            "planner": os.getenv("MODEL_PLANNER", "anthropic/claude-sonnet-4.5"),
            "decomposer": os.getenv(
                "MODEL_DECOMPOSER",
                os.getenv("MODEL_ASSISTANT", "anthropic/claude-sonnet-4.5"),
            ),
            "tester": os.getenv("MODEL_TESTER", "openai/gpt-4o"),
            "reviewer": os.getenv("MODEL_REVIEWER", "x-ai/grok-4"),
            "qa": os.getenv("MODEL_QA", "anthropic/claude-sonnet-4.5"),
            "pr": os.getenv("MODEL_PR", "google/gemini-2.5-pro"),
            "assistant": os.getenv("MODEL_ASSISTANT", os.getenv("MODEL_PLANNER", "anthropic/claude-sonnet-4.5")),
            "release": os.getenv("MODEL_RELEASE", "google/gemini-2.5-pro"),
            "supervisor": os.getenv("MODEL_SUPERVISOR", "openai/gpt-5-codex"),
        }
        self.fallbacks = {
            "architect": os.getenv(
                "MODEL_FALLBACK_ARCHITECT",
                os.getenv("MODEL_FALLBACK_PLANNER", "google/gemini-2.5-pro"),
            ),
            "planner": os.getenv("MODEL_FALLBACK_PLANNER", "google/gemini-2.5-pro"),
            "decomposer": os.getenv(
                "MODEL_FALLBACK_DECOMPOSER",
                os.getenv("MODEL_FALLBACK_ASSISTANT", "google/gemini-2.5-pro"),
            ),
            "tester": os.getenv("MODEL_FALLBACK_TESTER", "x-ai/grok-4-fast"),
            "reviewer": os.getenv("MODEL_FALLBACK_REVIEWER", "openai/o3-mini"),
            "qa": os.getenv("MODEL_FALLBACK_QA", "google/gemini-2.5-pro"),
            "pr": os.getenv("MODEL_FALLBACK_PR", "openai/gpt-4o"),
            "assistant": os.getenv(
                "MODEL_FALLBACK_ASSISTANT", os.getenv("MODEL_FALLBACK_PLANNER", "google/gemini-2.5-pro")
            ),
            "release": os.getenv("MODEL_FALLBACK_RELEASE", "google/gemini-2.5-pro"),
            "supervisor": os.getenv("MODEL_FALLBACK_SUPERVISOR", "anthropic/claude-sonnet-4.5"),
        }
        self.profile = "standard"
        if self._use_free_models():
            self.profile = "free"
            self._apply_free_profile()

        self.committees = {role: self._build_committee(role) for role in self.models}
        self.err_count: Dict[str, Dict[str, int]] = {
            role: defaultdict(int) for role in self.models
        }
        self.success_count = defaultdict(int)
        self.tokens_per_node = defaultdict(int)
        self.model_success: Dict[str, Dict[str, int]] = {
            role: defaultdict(int) for role in self.models
        }
        self.tokens_spent = 0
        self._log_event = event_logger

        self._emit(
            {
                "event": "router_committee",
                "profile": self.profile,
                "committees": self.committees,
                "budget_tokens": BUDGET_TOKENS,
            }
        )

    def _use_free_models(self) -> bool:
        val = os.getenv("USE_FREE_MODELS", "0").strip().lower()
        return val in _TRUTHY

    def _apply_free_profile(self):
        for role in self.models:
            primary = os.getenv(
                f"MODEL_{role.upper()}_FREE", FREE_MODEL_DEFAULTS.get(role, "")
            )
            fallback = os.getenv(
                f"MODEL_FALLBACK_{role.upper()}_FREE",
                FREE_FALLBACK_DEFAULTS.get(role, ""),
            )
            if primary:
                self.models[role] = primary
            if fallback:
                self.fallbacks[role] = fallback

    def _emit(self, payload: dict):
        if self._log_event:
            self._log_event(payload)

    def _build_committee(self, role: str) -> List[str]:
        extras: List[str] = []
        if self.profile == "free":
            free_key = f"MODEL_{role.upper()}_COMMITTEE_FREE"
            extras_env = os.getenv(free_key, "")
            if extras_env.strip():
                extras.extend(m.strip() for m in extras_env.split(",") if m.strip())
            else:
                extras.extend(FREE_COMMITTEE_DEFAULTS.get(role, []))
        else:
            env_key = f"MODEL_{role.upper()}_COMMITTEE"
            extras_env = os.getenv(env_key, "")
            if extras_env.strip():
                extras.extend(m.strip() for m in extras_env.split(",") if m.strip())

        lineup: List[str] = []
        primary = self.models.get(role)
        if primary:
            lineup.append(primary)

        for model in extras:
            if model not in lineup:
                lineup.append(model)

        fallback = self.fallbacks.get(role)
        if fallback and fallback not in lineup:
            lineup.append(fallback)

        return lineup

    def estimate_tokens(self, text: str, completion_max: int) -> int:
        return int(len(text) / 4) + completion_max

    def promote_model(self, role: str, model: Optional[str], reason: Optional[str] = None):
        if not model:
            return
        committee = self.committees.setdefault(role, [])
        if committee and committee[0] == model:
            self.models[role] = model
            if reason:
                self._emit(
                    {
                        "event": "router_model_promoted",
                        "node": role,
                        "model": model,
                        "reason": reason,
                        "committee": list(committee),
                    }
                )
            return
        if model in committee:
            committee.remove(model)
        committee.insert(0, model)
        self.models[role] = model
        self._emit(
            {
                "event": "router_model_promoted",
                "node": role,
                "model": model,
                "reason": reason or "committee_reorder",
                "committee": list(committee),
            }
        )

    def call(
        self,
        node: str,
        system: str,
        user: str,
        max_completion: int = 2000,
        force_json: bool = False,
    ) -> str:
        if self.tokens_spent > BUDGET_TOKENS:
            raise RuntimeError(f"Budget de tokens excedido: {self.tokens_spent}")

        attempts = self.committees.get(node) or [self.models.get(node)]
        last_error: Optional[str] = None

        for idx, model_to_use in enumerate(attempts):
            if not model_to_use:
                continue

            est = self.estimate_tokens(system + user, max_completion)
            try:
                if force_json:
                    out = chat_json(
                        model_to_use, system, user, max_tokens=max_completion
                    )
                else:
                    out = chat(model_to_use, system, user, max_tokens=max_completion)
                self.tokens_spent += est
                self.tokens_per_node[node] += est
                self.success_count[node] += 1
                self.model_success[node][model_to_use] += 1
                self._emit(
                    {
                        "event": "router_model_attempt",
                        "node": node,
                        "model": model_to_use,
                        "success": True,
                        "attempt": idx + 1,
                        "force_json": force_json,
                        "tokens_spent": self.tokens_spent,
                    }
                )
                self.promote_model(node, model_to_use)
                return out
            except Exception as exc:
                self.tokens_spent += est
                self.tokens_per_node[node] += est
                err_msg = str(exc)
                last_error = err_msg
                self.err_count[node][model_to_use] += 1
                self._emit(
                    {
                        "event": "router_model_attempt",
                        "node": node,
                        "model": model_to_use,
                        "success": False,
                        "attempt": idx + 1,
                        "force_json": force_json,
                        "error": err_msg[:4000],
                        "tokens_spent": self.tokens_spent,
                    }
                )
                continue

        raise RuntimeError(f"Nenhum modelo disponível para '{node}'. Último erro: {last_error}")

    def committee_snapshot(self) -> Dict[str, List[str]]:
        return {k: list(v) for k, v in self.committees.items()}

    def metrics(self) -> Dict[str, Any]:
        return {
            "tokens_spent": self.tokens_spent,
            "tokens_per_node": {
                node: self.tokens_per_node.get(node, 0) for node in self.models
            },
            "success_count": {node: self.success_count.get(node, 0) for node in self.models},
            "error_count": {node: dict(errors) for node, errors in self.err_count.items()},
            "model_success": {node: dict(successes) for node, successes in self.model_success.items()},
        }
