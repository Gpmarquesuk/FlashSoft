import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('OPENROUTER_API_KEY')
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/GpmarquesUK/FlashSoft",
    "X-Title": "flashsoft-autobot-mvp",
}
payload = {
    "model": "x-ai/grok-4",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10,
}
resp = requests.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=payload)
print('status', resp.status_code)
print('response', resp.text)
