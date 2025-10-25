#!/usr/bin/env python3
"""Re-analisa debate anterior com parser de votos corrigido."""

import json
import sys
sys.path.insert(0, '.')
from saci_v1 import _extract_votes

# Ler log do debate
with open('logs/saci_debate_1761333464.json', 'r', encoding='utf-8') as f:
    debate = json.load(f)

print('='*80)
print('RE-ANALISE DO DEBATE COM PARSER CORRIGIDO')
print('='*80)

for rodada in debate['rodadas']:
    print(f"\nRODADA {rodada['numero']}:")
    votos = _extract_votes(rodada['respostas'])
    for model, voto in votos.items():
        print(f'  {model}: {voto}')
    
    # Contar votos
    contagem = {}
    for v in votos.values():
        if v != 'unclear':
            contagem[v] = contagem.get(v, 0) + 1
    
    print(f'\n  Contagem: {contagem}')
    if contagem:
        max_voto = max(contagem, key=contagem.get)
        print(f'  Majoritario: {max_voto} ({contagem[max_voto]}/4 = {contagem[max_voto]/4*100:.0f}%)')

print('\n' + '='*80)
print('CONCLUSAO FINAL:')
print('='*80)

if len(debate['rodadas']) >= 2:
    votos_finais = _extract_votes(debate['rodadas'][-1]['respostas'])
    print(f"\nVotos finais (rodada {len(debate['rodadas'])}): {votos_finais}")
    
    contagem_final = {}
    for v in votos_finais.values():
        if v != 'unclear':
            contagem_final[v] = contagem_final.get(v, 0) + 1
    
    print(f"Contagem final: {contagem_final}")
    
    if contagem_final:
        max_voto = max(contagem_final, key=contagem_final.get)
        percentual = contagem_final[max_voto] / len(votos_finais) * 100
        print(f"\nDECISAO: Opcao {max_voto} com {contagem_final[max_voto]}/{len(votos_finais)} votos ({percentual:.0f}%)")
        
        if percentual >= 75:
            print("STATUS: CONSENSO ATINGIDO (>= 75%)")
        else:
            print("STATUS: SEM CONSENSO (< 75%)")
