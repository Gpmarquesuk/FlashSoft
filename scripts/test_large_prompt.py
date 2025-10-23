import os
import textwrap
import requests
from dotenv import load_dotenv

load_dotenv()
api_key=os.environ['OPENROUTER_API_KEY']
headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json","HTTP-Referer":"https://github.com/GpmarquesUK/FlashSoft","X-Title":"flashsoft-autobot-mvp"}
prompt=textwrap.dedent('''
Summarize this spec.
''')
resp=requests.post('https://openrouter.ai/api/v1/chat/completions',headers=headers,json={"model":"x-ai/grok-4","messages":[{"role":"user","content":prompt}]})
print(resp.status_code)
print(resp.text)
