#!/usr/bin/env python3
"""
Debate SACI: O que fazer com v2.0 e o problema de embeddings?
"""

from saci_v1 import debate_saci

problema = """SACI v2.0 com embeddings vs alternativas: Qual caminho seguir?

CONTEXTO:
- SACI v2.0 tentou usar embeddings OpenAI para medir convergencia semantica
- OpenRouter NAO oferece API de embeddings (erro: AttributeError)
- SACI v1.0 funciona perfeitamente com keyword matching simples
- Correcoes v2.0.1 (logging, retry, exceptions) funcionaram bem

OPCOES:
A) Descartar v2.0 completamente, usar apenas v1.0
B) Implementar embeddings locais (sentence-transformers, ~500MB)
C) Usar API OpenAI separada para embeddings (2 API keys)
D) Criar hibrido: v1.0 keywords + score numerico simples
E) Aguardar OpenRouter adicionar embeddings nativos

Vote claramente (VOTE: A/B/C/D/E) e justifique."""

resultado = debate_saci(
    problema=problema,
    contexto="",
    max_rodadas=3,
    threshold_consenso=0.75,
    verbose=True
)

print("\n" + "="*80)
print("RESULTADO FINAL DO DEBATE:")
print("="*80)
print(f"Consenso atingido: {resultado['consenso']}")
print(f"Solucao final: {resultado['solucao_final']}")
print(f"Votos finais: {resultado['votos']}")
print(f"Total de rodadas: {len(resultado['rodadas'])}")
