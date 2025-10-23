import os
import requests
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get('OPENROUTER_API_KEY')
if not API_KEY:
    raise RuntimeError('OPENROUTER_API_KEY not set')

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'HTTP-Referer': 'https://github.com/GpmarquesUK/FlashSoft',
    'X-Title': 'flashsoft-autobot-mvp',
}

def call_model(
    model: str,
    messages: List[Dict[str, str]],
    *,
    max_tokens: int = 4096,
    max_output_tokens: int | None = None,
    temperature: float = 0.2,
) -> str:
    payload = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
    }
    if max_output_tokens is not None:
        payload['max_output_tokens'] = max_output_tokens
    resp = requests.post('https://openrouter.ai/api/v1/chat/completions', headers=HEADERS, json=payload, timeout=240)
    resp.raise_for_status()
    data = resp.json()
    content = data['choices'][0]['message'].get('content', '')
    if not content:
        raise RuntimeError(f"Empty content from model {model}: {data}")
    return content.strip()
