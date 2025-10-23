import os
import requests

api_key = os.environ.get('OPENROUTER_API_KEY')
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/GpmarquesUK/FlashSoft",
    "X-Title": "flashsoft-autobot-mvp",
}
resp = requests.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=60)
resp.raise_for_status()
ids = [m['id'] for m in resp.json()['data'] if 'grok' in m['id']]
print(ids)
