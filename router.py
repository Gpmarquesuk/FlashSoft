import os
from llm_client import chat, chat_json

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

    def call(self, node: str, system: str, user: str, max_completion: int = 2000, force_json: bool = False) -> str:
        if self.tokens_spent > BUDGET_TOKENS:
            raise RuntimeError(f"Budget de tokens excedido: {self.tokens_spent}")
        primary = self.models[node]
        fallback = self.fallbacks[node]
        model_to_use = primary if self.err_count[node] < 3 else fallback
        try:
            est = self.estimate_tokens(system + user, max_completion)
            if force_json:
                out = chat_json(model_to_use, system, user, max_tokens=max_completion)
            else:
                out = chat(model_to_use, system, user, max_tokens=max_completion)
            self.tokens_spent += est
            return out
        except Exception:
            self.err_count[node] += 1
            if self.err_count[node] >= 3 and model_to_use != fallback:
                if force_json:
                    out = chat_json(fallback, system, user, max_tokens=max_completion)
                else:
                    out = chat(fallback, system, user, max_tokens=max_completion)
                self.tokens_spent += self.estimate_tokens(system + user, max_completion)
                return out
            raise
