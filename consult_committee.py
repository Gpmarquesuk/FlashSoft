#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Consulta junta de especialistas sobre flexibilização de JSON parsing
"""
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from llm_client import chat

consultation = json.loads(Path('docs/consultation_json_flexibility.json').read_text())

models = {
    'grok': 'x-ai/grok-beta',
    'gemini': 'google/gemini-2.0-flash-thinking-exp:free',
    'gpt4o': 'openai/gpt-4o',
    'claude': 'anthropic/claude-3.5-sonnet'
}

system = '''You are a senior software architect specializing in AI agent systems. 
Analyze the consultation document and provide:
1. Direct answers to each question (Q1-Q5)
2. Recommended implementation strategy
3. Risk assessment (HIGH/MEDIUM/LOW)
4. Expected improvement in success rate

Be concise but technical. Focus on pragmatic solutions for AI-to-AI communication.'''

user = f'''CONSULTATION:
{json.dumps(consultation, indent=2)}

Provide your expert analysis focusing on AI-to-AI communication tolerance.'''

print('=' * 80)
print('JUNTA DE ESPECIALISTAS - ANALISE DE FLEXIBILIZACAO JSON')
print('=' * 80)

for name, model in models.items():
    try:
        print(f'\n>>> {name.upper()} ({model})\n')
        print('-' * 80)
        response = chat(model, system, user, max_tokens=1000, temperature=0.3)
        print(response)
        print('\n' + '-' * 80)
        
        # Salvar resposta
        output_file = Path(f'logs/consult_{name}.txt')
        output_file.write_text(response, encoding='utf-8')
        print(f'OK - Salvo em: {output_file}')
        
    except Exception as e:
        print(f'ERRO: {e}')
        print('-' * 80)

print('\nConsulta concluida! Respostas salvas em logs/consult_*.txt')
