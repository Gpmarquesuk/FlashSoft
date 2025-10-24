import os, json, re
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from openai import OpenAI

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "90"))  # 90s (mais agressivo)
MAX_RETRIES = int(os.getenv("MAX_RETRIES_PER_CALL", "1"))  # APENAS 1 retry no tenacity

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY ausente")

# Client simples - sem customização de httpx
# O client global foi removido. Uma nova instância é criada em cada chamada de chat/chat_json
# para garantir que não haja estado compartilhado ou conexões reutilizadas que possam causar hangs.
# client = OpenAI(...)

def _headers():
    return {
        "HTTP-Referer": "https://github.com/GpmarquesUK/FlashSoft",
        "X-Title": "flashsoft-autobot-mvp"
    }

def _find_json_balanced(s: str):
    """Encontra o primeiro objeto JSON balanceado."""
    stack = 0
    start = None
    for i, ch in enumerate(s):
        if ch == "{":
            if stack == 0:
                start = i
            stack += 1
        elif ch == "}":
            if stack > 0:
                stack -= 1
                if stack == 0 and start is not None:
                    cand = s[start:i+1]
                    try:
                        return json.loads(cand)
                    except Exception:
                        pass
    return None

def safe_json_extract(text: str):
    """Extrator tolerante: tenta JSON puro, bloco ```json, balanceado, e por fim o maior bloco."""
    if not text:
        raise ValueError("Saída vazia")
    t = text.strip()

    # 1) JSON puro
    try:
        return json.loads(t)
    except Exception:
        pass

    # 2) bloco ```json ... ```
    m = re.search(r"```json\s*(.+?)\s*```", t, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # 3) balanceado
    obj = _find_json_balanced(t)
    if obj is not None:
        return obj

    # 4) primeiro {...} como fallback
    m = re.search(r"\{.*\}", t, re.DOTALL)
    if m:
        return json.loads(m.group(0))

    raise ValueError("Saída sem JSON")

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential_jitter(1, 2))
def chat(model: str, system: str, user: str, temperature: float = 0.2, max_tokens: int = 8192) -> str:
    """Instancia um novo cliente para cada chamada para evitar problemas de conexão."""
    client = OpenAI(
        api_key=OPENROUTER_API_KEY, 
        base_url=BASE_URL,
        timeout=TIMEOUT,
        max_retries=0 # Desabilitar retry do SDK, usar o do Tenacity
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        extra_headers=_headers()
    )
    return resp.choices[0].message.content

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential_jitter(1, 2))
def chat_json(model: str, system: str, user: str, temperature: float = 0.0, max_tokens: int = 8192) -> str:
    """Pede JSON nativo e também instancia um cliente novo."""
    client = OpenAI(
        api_key=OPENROUTER_API_KEY, 
        base_url=BASE_URL,
        timeout=TIMEOUT,
        max_retries=0 # Desabilitar retry do SDK, usar o do Tenacity
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        extra_headers=_headers()
    )
    return resp.choices[0].message.content
