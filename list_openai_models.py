#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lista TODOS os modelos OpenAI no OpenRouter"""
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY')
)

models = client.models.list()
openai_models = [m for m in models.data if m.id.startswith('openai/')]

print("TODOS OS MODELOS OPENAI DISPONIVEIS NO OPENROUTER:")
print("="*60)
for m in sorted(openai_models, key=lambda x: x.id):
    print(f"  {m.id}")
    
print("\n" + "="*60)
print("RECOMENDACAO: Procure por o1, o3, gpt-4-turbo, ou codex")
