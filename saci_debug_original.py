"""
SACI ANTIGA - Debug dos Problemas da SACI EVOLUÍDA
Usa os 4 MODELOS ORIGINAIS do consenso.
"""

import asyncio
from llm_client import chat

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
                input=text[:8000]
            )
            embeddings.append(response.data[0].embedding)
        
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                cos_sim = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )
                similarities.append(cos_sim)
        
        return float(np.mean(similarities))
    except Exception:
        return 0.0  # Fallback silencioso
```

**Hipóteses:**
- A) Exceção silenciosa sempre (fallback 0.0)
- B) API OpenAI não configurada/timeout
- C) Embeddings calculados mas similarity incorreta
- D) Bug no cálculo de cosine similarity

**Impacto:**
- Score máximo possível = 0.4 (apenas votos)
- Early stopping nunca ativa (threshold 0.75 inatingível)

---

## PROBLEMA 2: Threshold 0.75 Muito Alto

**Evidências:**
- Debate 1: Consenso claro (75% votos D), mas score max=0.339
- Debate 2: Divergência real, score max=0.162

**Cálculo Atual:**
```python
score = (0.6 * 0.000) + (0.4 * vote_consensus)
      = 0.4 * vote_consensus

# Para atingir 0.75:
vote_consensus >= 1.875  # IMPOSSÍVEL (max=1.0)
```

**Hipóteses:**
- A) Threshold deveria ser 0.40 (apenas votos)
- B) Pesos deveriam ser invertidos (0.4 semantic, 0.6 votes)
- C) Threshold deveria ser adaptativo
- D) Bug de embeddings mascara problema real

---

## QUESTÕES PARA DEBATE

1. Causa raiz do bug de embeddings?
2. Threshold 0.75 é realista se embeddings funcionassem?
3. Qual problema atacar primeiro?
4. Sistema deveria continuar funcionando sem embeddings?
"""

DEBATE_PROMPT = """
Você é um modelo especializado em debugging e design de sistemas.

**PROBLEMA SUBMETIDO:**
{context}

**SUA TAREFA:**
1. Analise as evidências apresentadas
2. Priorize os problemas por severidade
3. Proponha diagnóstico para causa raiz
4. Sugira ordem de correção
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
  "diagnostico": "Sua análise detalhada",
  "prioridade": ["problema_1", "problema_2"],
  "causa_raiz_embeddings": "Hipótese A/B/C/D",
  "causa_raiz_threshold": "Hipótese A/B/C/D",
  "ordem_correcao": "Qual atacar primeiro e por quê",
  "impacto_estimado": "Severidade 1-10 para cada",
  "voto": "A/B/C/D/E",
  "confianca": 80
}}
```

Seja brutalmente honesto e técnico.
"""

async def run_saci_antiga_debug():
    """Executa debate com SACI antiga - MODELOS ORIGINAIS."""
    
    models = [
        "anthropic/claude-sonnet-4.5",
        "openai/gpt-5-codex",
        "google/gemini-2.5-pro",
        "x-ai/grok-4"
    ]
    
    print("\n" + "="*80)
    print("🔍 SACI ANTIGA - DEBUG DOS PROBLEMAS DA SACI EVOLUÍDA")
    print("="*80)
    print(f"\n📋 Modelos participantes: {len(models)}")
    for i, model in enumerate(models, 1):
        print(f"   {i}. {model}")
    
    print("\n🎯 Iniciando rodada de diagnóstico...\n")
    
    responses = []
    
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
    
    print("\n" + "="*80)
    print("💾 Salvando resultados...")
    print("="*80 + "\n")
    
    with open("logs/saci_antiga_debug_problemas.md", "w", encoding="utf-8") as f:
        f.write("# SACI ANTIGA - DIAGNÓSTICO DOS PROBLEMAS DA SACI EVOLUÍDA\n\n")
        f.write("**Modelos Originais do Consenso SACI EVOLUÍDO**\n\n")
        f.write("---\n\n")
        
        for i, resp in enumerate(responses, 1):
            model_name = resp['model'].split('/')[-1]
            f.write(f"## 🤖 RESPOSTA {i}: {model_name}\n\n")
            f.write(f"**Model ID:** `{resp['model']}`\n\n")
            f.write("### Diagnóstico:\n\n")
            f.write(resp['response'])
            f.write("\n\n---\n\n")
        
        f.write("## 📊 ANÁLISE DE CONSENSO\n\n")
        f.write("**Extrair votos manualmente de cada resposta JSON**\n")
    
    print("✅ Resultados salvos em: logs/saci_antiga_debug_problemas.md")
    
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
    print(f"📊 {len(responses)}/{len(models)} modelos responderam\n")

if __name__ == "__main__":
    asyncio.run(run_saci_antiga_debug())
