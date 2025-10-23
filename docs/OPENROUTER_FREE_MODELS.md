# OpenRouter Free Model Reference

Last refreshed: 2025-10-21  
Source: `https://openrouter.ai/api/v1/models` (filtered where `pricing.prompt==0` and `pricing.completion==0`)

| Category | Model ID | Context Length | Notes |
| --- | --- | --- | --- |
| **General chat / planning** | `deepseek/deepseek-chat-v3.1:free` | 163 840 | Strong reasoning, may require “free endpoints may publish prompts”. |
| | `deepseek/deepseek-r1:free` | 163 840 | High-quality reasoning; occasionally rate-limited. |
| | `qwen/qwen-2.5-coder-32b-instruct:free` | 32 768 | Reliable JSON responses; good fallback planner/coder. |
| | `openai/gpt-oss-20b:free` | 131 072 | Open-source OSS variant (beta). |
| **Coding / testing** | `mistralai/mistral-7b-instruct:free` | 32 768 | Fast responses; good for tester node. |
| | `qwen/qwen3-coder:free` | 262 144 | Large context coder, handles long diffs. |
| | `z-ai/glm-4.5-air:free` | 131 072 | Balanced general-purpose coding. |
| **Review / critique** | `google/gemma-2-9b-it:free` | 8 192 | Light-weight reviewer. |
| | `google/gemma-3n-e4b-it:free` | 8 192 | Better detail, still zero cost. |
| | `deepseek/deepseek-r1-distill-llama-70b:free` | 8 192 | Strong reasoning, short context. |
| **PR / summarisation** | `mistralai/mistral-small-24b-instruct-2501:free` | 32 768 | Fluent summariser for PR bodies. |
| | `mistralai/mistral-small-3.2-24b-instruct:free` | 131 072 | Larger context summarisation. |
| **Vision / multimodal** | `qwen/qwen2.5-vl-32b-instruct:free` | 16 384 | Supports image+text; useful for overlay QA. |
| | `google/gemini-2.0-flash-exp:free` | 1 048 576 | High-context multimodal; free preview tier. |
| **Specialised / research** | `alibaba/tongyi-deepresearch-30b-a3b:free` | 131 072 | Deep research agent (slow). |
| | `tngtech/deepseek-r1t2-chimera:free` | 163 840 | Optimised for reflective reasoning. |
| **Small footprint** | `nvidia/nemotron-nano-9b-v2:free` | 128 000 | Lower latency, good on slim specs. |
| | `meta-llama/llama-3.3-8b-instruct:free` | 128 000 | Lightweight meta llama variant. |

### Usage tips
- **Privacy toggles**: ensure “Enable free endpoints that may publish prompts” is ON in OpenRouter account settings, otherwise most free endpoints return 404.
- **Rate limits**: free tiers can rate-limit aggressively. Keep committees with at least three entries so the router can rotate models.
- **Environment variables**: add `MODEL_<ROLE>_FREE` and `MODEL_<ROLE>_COMMITTEE_FREE` in `.env` to map each node to your preferred set.
- **Observability**: check `logs/run-*.jsonl` for `router_model_attempt` events to see which free model handled each call (success vs fallback).

> For the full raw list (dozens of entries) rerun `python scripts/list_openrouter_free_models.py` using the same filtering logic above. *** End Patch
