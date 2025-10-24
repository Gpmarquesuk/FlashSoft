"""
SACI ANTIGA - Debug dos Problemas da SACI EVOLUÍDA

Submete 2 problemas críticos encontrados nos testes para debate:
1. Bug de embeddings (similaridade sempre 0.0)
2. Threshold 0.75 muito alto (max atingido: 0.34)

Usa a SACI ANTIGA (sem métricas quantitativas) para obter diagnóstico.
"""

import asyncio
from llm_client import chat

# Contexto detalhado dos problemas
PROBLEMA_CONTEXT = """
# PROBLEMAS ENCONTRADOS NA SACI EVOLUÍDA

## CONTEXTO
Durante testes da SACI EVOLUÍDA (implementada com consenso 4/4 models), 
foram identificados 2 problemas críticos em 15 rodadas de debates reais:

## PROBLEMA 1: Similaridade Semântica Sempre 0.0

**Evidências:**
- Debate 1 (Integração FlashSoft): 5 rodadas, todas com similarity=0.000
- Debate 2 (vs. Devin): 5 rodadas, todas com similarity=0.000
- Debate Teste (Database): 5 rodadas, todas com similarity=0.000

**Implementação:**
```python
def compute_semantic_similarity(texts: List[str], timeout: int = 10) -> float:
    try:
        client = OpenAI()
        embeddings = []
        for text in texts:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000]  # Truncate
            )
            embeddings.append(response.data[0].embedding)
        
        # Cosine similarity entre todos os pares
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                cos_sim = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )
                similarities.append(cos_sim)
        
        return float(np.mean(similarities))
    except Exception:
        return 0.0  # Fallback
```

**Hipóteses:**
- A) Exceção silenciosa sempre (fallback 0.0)
- B) API OpenAI não configurada/timeout
- C) Embeddings calculados mas similarity incorreta
- D) Bug no cálculo de cosine similarity

**Impacto:**
- Score máximo possível = 0.4 (apenas votos)
- Early stopping nunca ativa (threshold 0.75 inatingível)
- Métrica de convergência degenerada

---

## PROBLEMA 2: Threshold 0.75 Muito Alto

**Evidências:**
- Debate 1: Consenso claro (75% votos D), mas score max=0.339
- Debate 2: Divergência real, score max=0.162
- Debate Teste: Score max=0.248

**Cálculo Atual:**
```python
score = (semantic_weight * similarity) + (vote_weight * vote_consensus)
      = (0.6 * 0.000) + (0.4 * vote_consensus)
      = 0.4 * vote_consensus

# Para atingir 0.75:
0.4 * vote_consensus >= 0.75
vote_consensus >= 1.875  # IMPOSSÍVEL (max=1.0)
```

**Hipóteses:**
- A) Threshold deveria ser 0.40 (apenas votos)
- B) Pesos deveriam ser invertidos (0.4 semantic, 0.6 votes)
- C) Threshold deveria ser adaptativo baseado em rounds
- D) Bug de embeddings mascara problema real de threshold

**Impacto:**
- Early stopping nunca ativa
- Debates sempre vão até max_rounds (5)
- Custo e latência desnecessários

---

## DADOS REAIS DOS TESTES

### Debate 1 (Integração FlashSoft)
| Rodada | Similarity | Votos | Score | Consenso? |
|--------|-----------|-------|-------|-----------|
| 1 | 0.000 | d:3, c:1 | 0.339 | 75% em D |
| 2 | 0.000 | d:3, c:1 | 0.335 | 75% em D |
| 3 | 0.000 | d:3, c:1 | 0.335 | 75% em D |
| 4 | 0.000 | d:3, c:1 | 0.338 | 75% em D |
| 5 | 0.000 | d:3, c:1 | 0.339 | 75% em D |

**Resultado:** Consenso claro, mas score insuficiente para early stopping.

### Debate 2 (vs. Devin)
| Rodada | Similarity | Votos | Score | Consenso? |
|--------|-----------|-------|-------|-----------|
| 1 | 0.000 | c:3, d:1 | 0.129 | 75% em C |
| 2 | 0.000 | c:3, d:1 | 0.145 | 75% em C |
| 3 | 0.000 | c:3, d:1 | 0.154 | 75% em C |
| 4 | 0.000 | c:3, d:1 | 0.162 | 75% em C |
| 5 | 0.000 | c:3, d:1 | 0.153 | 75% em C |

**Resultado:** Consenso claro, mas score ainda mais baixo.

---

## QUESTÕES PARA DEBATE

1. **Causa Raiz do Bug de Embeddings:**
   - É problema de implementação, configuração ou design?
   - Fallback silencioso é apropriado ou deveria falhar ruidosamente?

2. **Design de Threshold:**
   - 0.75 é realista se embeddings funcionassem?
   - Deveria ser adaptativo (variar com número de rodadas)?

3. **Pesos de Métricas:**
   - 0.6 semantic + 0.4 votes é correto?
   - Ou deveria priorizar votos (mais confiáveis)?

4. **Prioridade de Fix:**
   - Corrigir embeddings primeiro?
   - Ou ajustar threshold para funcionar só com votos?

5. **Fallback Strategy:**
   - Sistema deveria continuar funcionando sem embeddings?
   - Ou deveria falhar explicitamente e exigir fix?
"""

DEBATE_PROMPT = """
Você é um modelo especializado em debugging e design de sistemas.

**PROBLEMA SUBMETIDO:**
{context}

**SUA TAREFA:**
1. Analise as evidências apresentadas
2. Priorize os problemas por severidade e impacto
3. Proponha diagnóstico para causa raiz de cada problema
4. Sugira ordem de correção (qual problema atacar primeiro)
5. Vote em UMA das opções:

**OPÇÕES DE DIAGNÓSTICO:**

**A:** Bug de embeddings é crítico, fix imediato (threshold é consequência)
**B:** Threshold está errado, ajustar primeiro (embeddings podem esperar)
**C:** Design fundamentalmente falho, refatorar métricas completamente
**D:** Ambos são bugs independentes, corrigir em paralelo
**E:** Sistema funciona bem só com votos, remover embeddings

**FORMATO DE RESPOSTA:**
```json
{{
  "diagnostico": "Sua análise detalhada das causas raiz",
  "prioridade": ["problema_1", "problema_2", ...],
  "causa_raiz_embeddings": "Hipótese mais provável (A/B/C/D)",
  "causa_raiz_threshold": "Hipótese mais provável (A/B/C/D)",
  "ordem_correcao": "Qual problema atacar primeiro e por quê",
  "impacto_estimado": "Severidade 1-10 para cada problema",
  "voto": "A/B/C/D/E",
  "confianca": 80
}}
```

Seja brutalmente honesto e técnico. Priorize evidências empíricas.
"""

async def run_saci_antiga_debug():
    """Executa debate com SACI antiga sobre os problemas."""
    
    models = [
        "openai/o3-mini",
        "anthropic/claude-3.7-sonnet",
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct"
    ]
    
    print("\n" + "="*80)
    print("🔍 SACI ANTIGA - DEBUG DOS PROBLEMAS DA SACI EVOLUÍDA")
    print("="*80)
    print(f"\n📋 Modelos participantes: {len(models)}")
    for i, model in enumerate(models, 1):
        print(f"   {i}. {model}")
    
    print("\n🎯 Iniciando rodada de diagnóstico...\n")
    
    responses = []
    
    # Rodada única (SACI antiga não tem rodadas múltiplas formais)
    for i, model in enumerate(models, 1):
        print(f"⏳ Consultando {model.split('/')[-1]}...")
        
        try:
            prompt = DEBATE_PROMPT.format(context=PROBLEMA_CONTEXT)
            
            content = await asyncio.to_thread(
                chat,
                model=model,
                system="Você é um especialista em debugging e design de sistemas.",
                user=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            responses.append({
                "model": model,
                "response": content
            })
            
            print(f"✅ Resposta recebida ({len(content)} chars)\n")
            
        except Exception as e:
            print(f"❌ Erro ao consultar {model}: {e}\n")
            responses.append({
                "model": model,
                "response": f"ERROR: {str(e)}"
            })
    
    # Salvar resultados
    print("\n" + "="*80)
    print("💾 Salvando resultados...")
    print("="*80 + "\n")
    
    # Markdown formatado
    with open("logs/saci_antiga_debug_problemas.md", "w", encoding="utf-8") as f:
        f.write("# SACI ANTIGA - DIAGNÓSTICO DOS PROBLEMAS DA SACI EVOLUÍDA\n\n")
        f.write(f"**Data:** {asyncio.get_event_loop().time()}\n")
        f.write(f"**Modelos:** {len(models)}\n\n")
        f.write("---\n\n")
        
        for i, resp in enumerate(responses, 1):
            model_name = resp['model'].split('/')[-1]
            f.write(f"## 🤖 RESPOSTA {i}: {model_name}\n\n")
            f.write(f"**Model ID:** `{resp['model']}`\n\n")
            f.write("### Diagnóstico:\n\n")
            f.write(resp['response'])
            f.write("\n\n---\n\n")
        
        # Análise de consenso (manual)
        f.write("## 📊 ANÁLISE DE CONSENSO\n\n")
        f.write("**Próximo passo:** Revisar os 4 diagnósticos e identificar:\n")
        f.write("1. Qual hipótese de causa raiz tem mais suporte?\n")
        f.write("2. Qual problema atacar primeiro?\n")
        f.write("3. Qual estratégia de correção usar?\n\n")
        f.write("**Votos extraídos:** (revisar manualmente no JSON de cada resposta)\n")
    
    print("✅ Resultados salvos em: logs/saci_antiga_debug_problemas.md")
    
    # Exibir preview
    print("\n" + "="*80)
    print("📄 PREVIEW DAS RESPOSTAS")
    print("="*80 + "\n")
    
    for i, resp in enumerate(responses, 1):
        model_name = resp['model'].split('/')[-1]
        preview = resp['response'][:300] + "..." if len(resp['response']) > 300 else resp['response']
        print(f"🤖 {model_name}:")
        print(preview)
        print("\n" + "-"*80 + "\n")
    
    print("✅ Debate concluído!")
    print(f"📊 {len(responses)}/{len(models)} modelos responderam")
    print("📁 Análise completa disponível em: logs/saci_antiga_debug_problemas.md\n")

if __name__ == "__main__":
    asyncio.run(run_saci_antiga_debug())
