import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
)
model = os.getenv("MODEL_REVIEWER", "x-ai/grok-4-fast")
resp = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "VocÃª Ã© um verificador de ambiente"},
        {"role": "user", "content": "Responda com exatamente: OK"}
    ],
    temperature=0,
    max_tokens=5
)
print(resp.choices[0].message.content.strip())
