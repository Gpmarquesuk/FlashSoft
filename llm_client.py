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
        raise ValueError("SaÃ­da sem JSON")
    return json.loads(m.group(0))
