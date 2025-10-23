"""
CONSULTA ESPECIAL À JUNTA DE ESPECIALISTAS
Tema: Criação da SACI (Sistema Avançado de Convergência de Ideias)

PROPOSTA DO USUÁRIO:
Criar uma célula de soluções avançadas onde 4 modelos de IA discutem 
um problema até a MAIORIA obter consenso. Será o "cérebro mestre" 
para resolver problemas críticos da fábrica FlashSoft e além.

OBJETIVO: Obter feedback dos especialistas sobre como implementar 
a SACI da forma mais eficaz possível.
"""

import os
import json
import time
from datetime import datetime
from llm_client import chat

# Carregar API key
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY não encontrada!")

print(f"✓ API Key carregada")

# Modelos para consulta sobre SACI
MODELS = {
    'gemini25pro': {
        'id': 'google/gemini-2.5-pro',
        'name': 'Gemini 2.5 PRO'
    },
    'gpt5codex': {
        'id': 'openai/gpt-5-codex',
        'name': 'GPT-5 CODEX'
    },
    'grok4': {
        'id': 'x-ai/grok-4',
        'name': 'Grok 4'
    },
    'claude35sonnet': {
        'id': 'anthropic/claude-sonnet-4.5',
        'name': 'Claude 3.5 Sonnet'
    }
}

CONTEXT = """
# CONTEXTO - PROPOSTA DO USUÁRIO

## SITUAÇÃO ATUAL
A fábrica FlashSoft está enfrentando problemas complexos que exigem soluções 
inovadoras. Tentativas anteriores com agentes únicos ou consultas paralelas 
não produziram convergência suficiente.

## PROPOSTA: SACI (Sistema Avançado de Convergência de Ideias)

### Conceito
Uma "célula de soluções avançadas" onde 4 modelos de IA:
1. Recebem um problema/desafio complexo
2. Debatem iterativamente (múltiplas rodadas)
3. Avaliam e refinam propostas uns dos outros
4. Convergem até MAIORIA (3 de 4) concordar com uma solução

### Objetivo
Criar o "cérebro mestre" que resolve problemas críticos através de:
- Debate estruturado entre IAs
- Convergência forçada (não apenas opiniões paralelas)
- Validação cruzada de soluções
- Refinamento iterativo até consenso

### Casos de Uso
- Decisões arquiteturais críticas da fábrica
- Debugging de problemas complexos
- Design de novos componentes
- Análise de trade-offs técnicos
- Qualquer desafio que exija "inteligência coletiva"

## CONSULTA PRÉVIA
Na consulta anterior, vocês 3 (Gemini, GPT-5 Codex, Grok 4) recomendaram:
- Fixar Planner com Pydantic schema
- Reduzir context window
- Simplificar committee
- Criar UI com Streamlit

Mas o usuário questiona: "Não estou convencido de que esta é a melhor estratégia."
Ele propõe que a PRÓPRIA SACI seja usada para validar/refinar essas recomendações.
"""

QUESTIONS = """
# PERGUNTAS PARA OS ESPECIALISTAS

## 1. ARQUITETURA DA SACI
- Como estruturar o sistema de debate entre 4 IAs?
- Quantas rodadas de debate são ideais?
- Como detectar convergência (além de votos majoritários)?
- Que mecanismos evitam loops infinitos sem consenso?

## 2. PROTOCOLO DE DEBATE
- Qual a melhor estrutura de prompts para debate produtivo?
- Como cada IA deve "responder" às propostas das outras?
- Deve haver um "moderador" (5º agente) ou auto-moderação?
- Como lidar com empates (2 vs 2)?

## 3. SELEÇÃO DOS 4 MODELOS
- Quais 4 modelos devem compor a SACI?
- Deve haver diversidade (GPT, Claude, Gemini, Grok) ou especialização?
- Como balancear custo vs qualidade nas escolhas?

## 4. IMPLEMENTAÇÃO TÉCNICA
- Python framework ideal (LangChain, CrewAI, custom)?
- Como persistir estado do debate (histórico, propostas)?
- Estrutura de dados para propostas e votos?
- Como apresentar resultado final ao usuário?

## 5. MECANISMOS DE CONVERGÊNCIA
- Votação simples (3 de 4) é suficiente?
- Deve haver métricas de "qualidade da convergência"?
- Como identificar quando debate está travado?
- Estratégias de desempate (trazer 5º modelo? Human in the loop?)?

## 6. VALIDAÇÃO DA PRÓPRIA SACI
- Como testar se a SACI funciona antes de usá-la em problemas reais?
- Benchmarks ou problemas "toy" para validação?
- Como comparar SACI vs consultas paralelas tradicionais?

## 7. APLICAÇÃO IMEDIATA
O usuário questiona as recomendações anteriores (Pydantic, context reduction, etc).
**PROPOSTA META:** Use o conceito da SACI NESTA PRÓPRIA CONSULTA.

Após responderem individualmente:
- Cada um deve AVALIAR as propostas dos outros 3
- Identificar pontos de consenso
- Propor síntese final que incorpore melhores ideias de todos
- Votar na solução final

## 8. CASOS DE USO ALÉM DA FÁBRICA
- Que outros problemas a SACI poderia resolver?
- Como torná-la genérica o suficiente para reutilização?
- Vale criar SACI como produto standalone (open-source)?

RESPONDA COM MÁXIMO DETALHE TÉCNICO E EXEMPLOS DE CÓDIGO/PSEUDOCÓDIGO QUANDO RELEVANTE.
"""

def consult_model(model_key: str, model_info: dict):
    """Consulta um modelo sobre a SACI"""
    model_id = model_info['id']
    model_name = model_info['name']
    
    print(f"\n{'='*80}")
    print(f"🤖 CONSULTANDO: {model_name}")
    print(f"   Model ID: {model_id}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    system_prompt = """You are a senior AI systems architect and expert in multi-agent systems, 
debate protocols, consensus mechanisms, and collective intelligence. You have deep knowledge of:
- Agent orchestration frameworks (LangChain, AutoGen, CrewAI)
- Debate and argumentation theory
- Consensus algorithms (Raft, Paxos, voting systems)
- Prompt engineering for collaborative AI
- Software architecture patterns

Provide detailed, technical, and actionable analysis with code examples when relevant."""

    user_prompt = f"{CONTEXT}\n\n{QUESTIONS}"
    
    try:
        print(f"⏳ Enviando prompt ({len(user_prompt)} chars)...")
        
        response = chat(
            model=model_id,
            system=system_prompt,
            user=user_prompt,
            max_tokens=4500,
            temperature=0.4
        )
        
        elapsed = time.time() - start_time
        
        input_tokens = (len(system_prompt) + len(user_prompt)) // 4
        output_tokens = len(response) // 4
        
        print(f"✓ Resposta recebida!")
        print(f"  Tempo: {elapsed:.1f}s")
        print(f"  Input tokens: ~{input_tokens}")
        print(f"  Output tokens: ~{output_tokens}")
        
        # Salvar relatório
        report = {
            'model': model_name,
            'model_id': model_id,
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': round(elapsed, 2),
            'tokens': {
                'input_approximate': input_tokens,
                'output_approximate': output_tokens,
                'total_approximate': input_tokens + output_tokens
            },
            'response': response
        }
        
        json_filename = f"logs/saci_consulta_{model_key}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"  Salvo: {json_filename}")
        
        txt_filename = f"logs/saci_consulta_{model_key}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"CONSULTA SACI - SISTEMA AVANÇADO DE CONVERGÊNCIA\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Modelo: {model_name} ({model_id})\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tempo: {elapsed:.1f}s\n")
            f.write(f"Tokens: ~{input_tokens + output_tokens}\n\n")
            f.write(f"{'='*80}\n")
            f.write(f"RESPOSTA:\n")
            f.write(f"{'='*80}\n\n")
            f.write(response)
        print(f"  Salvo: {txt_filename}")
        
        return True, response
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False, str(e)

def main():
    print("\n" + "="*80)
    print("CONSULTA SOBRE SACI - SISTEMA AVANÇADO DE CONVERGÊNCIA")
    print("="*80)
    print(f"\nModelos a consultar:")
    for key, info in MODELS.items():
        print(f"  • {info['name']} ({info['id']})")
    print("\n")
    
    responses = {}
    
    # FASE 1: Consultas individuais
    print("\n" + "="*80)
    print("FASE 1: CONSULTAS INDIVIDUAIS")
    print("="*80 + "\n")
    
    for model_key, model_info in MODELS.items():
        success, response = consult_model(model_key, model_info)
        responses[model_key] = {
            'success': success,
            'response': response,
            'model_name': model_info['name']
        }
        
        if model_key != list(MODELS.keys())[-1]:
            print("\n⏸  Aguardando 3s antes da próxima consulta...")
            time.sleep(3)
    
    # FASE 2: Análise cruzada (simulação de debate)
    print("\n\n" + "="*80)
    print("FASE 2: ANÁLISE CRUZADA (SIMULAÇÃO DE SACI)")
    print("="*80 + "\n")
    
    successful_responses = {k: v for k, v in responses.items() if v['success']}
    
    if len(successful_responses) >= 3:
        print("✓ Respostas suficientes para análise cruzada\n")
        
        # Preparar prompt de convergência
        convergence_prompt = """Você acabou de receber as propostas dos outros especialistas sobre a SACI.

PROPOSTAS DOS OUTROS MODELOS:
"""
        for key, data in successful_responses.items():
            if data['success']:
                convergence_prompt += f"\n{'='*80}\n"
                convergence_prompt += f"PROPOSTA DE {data['model_name']}:\n"
                convergence_prompt += f"{'='*80}\n"
                convergence_prompt += data['response'][:2000] + "...\n\n"
        
        convergence_prompt += """
TAREFA DE CONVERGÊNCIA:
1. Identifique os 3 pontos principais de CONSENSO entre as propostas
2. Identifique divergências ou trade-offs importantes
3. Proponha uma SÍNTESE FINAL que integre as melhores ideias
4. Vote: você APROVA a síntese final? (SIM/NÃO e por quê)

Responda de forma estruturada e concisa (máx 1000 tokens).
"""
        
        # Consultar um modelo para convergência (Gemini como "facilitador")
        print("🔄 Executando rodada de convergência...")
        print("   Facilitador: Gemini 2.5 PRO\n")
        
        try:
            conv_response = chat(
                model='google/gemini-2.5-pro',
                system="You are a facilitator of multi-agent consensus. Analyze proposals and synthesize the best solution.",
                user=convergence_prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            conv_filename = "logs/saci_convergencia.txt"
            with open(conv_filename, 'w', encoding='utf-8') as f:
                f.write("SACI - RODADA DE CONVERGÊNCIA\n")
                f.write("="*80 + "\n\n")
                f.write("Facilitador: Gemini 2.5 PRO\n")
                f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("="*80 + "\n")
                f.write("SÍNTESE E CONSENSO:\n")
                f.write("="*80 + "\n\n")
                f.write(conv_response)
            
            print(f"✓ Convergência salva: {conv_filename}")
            
        except Exception as e:
            print(f"❌ Erro na convergência: {e}")
    
    # Resumo final
    print(f"\n\n{'='*80}")
    print("RESUMO DA CONSULTA SACI")
    print(f"{'='*80}\n")
    
    successful = sum(1 for v in responses.values() if v['success'])
    print(f"  Consultas bem-sucedidas: {successful}/{len(MODELS)}")
    
    for model_key, data in responses.items():
        status = "✓ SUCESSO" if data['success'] else "✗ FALHA"
        print(f"  {status}: {data['model_name']}")
    
    print(f"\n{'='*80}")
    print("Relatórios salvos em:")
    print("  - logs/saci_consulta_*.json + .txt (propostas individuais)")
    print("  - logs/saci_convergencia.txt (síntese final)")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
