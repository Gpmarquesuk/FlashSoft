"""
CONSULTA COMPLETA À JUNTA DE ESPECIALISTAS
Modelos: Gemini 2.5 Pro, GPT-5 Codex, Grok 4

Cada modelo receberá contexto completo do projeto FlashSoft e deverá:
1. Analisar a arquitetura atual da fábrica
2. Propor melhorias no workflow
3. Criticar problemas no modelo atual
4. Sugerir estratégias de melhoria
5. Opinar sobre criação de UI para a fábrica
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

print(f"✓ API Key carregada: {api_key[:20]}...")

# Definir modelos EXATOS conforme solicitado
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
    }
}

# Contexto COMPLETO do projeto
CONTEXT = """
# CONTEXTO COMPLETO - FÁBRICA DE SOFTWARE FLASHSOFT

## OBJETIVO
Fábrica automatizada de software usando agentes de IA que transforma especificações YAML em Pull Requests funcionais no GitHub, com testes validados.

## ARQUITETURA ATUAL

### Pipeline Principal
1. **run_spec.ps1** → Orchestrator Sentry → **run.py** → Agentes Sequenciais
2. Workspace temporário: /tmp/autobot_work (clone do repo)
3. Logs estruturados: run-*.jsonl (eventos), ORCH_*_out.txt (stdout/stderr)
4. Comitê de modelos LLM via OpenRouter API

### Agentes na Sequência
1. **Task Decomposer**: Quebra spec em tarefas menores (opcional, desabilitado por padrão)
2. **Architect**: Analisa arquitetura e propõe estrutura de arquivos (opcional)
3. **Planner/Coder**: Gera patches (arquivos completos) em JSON: {"patches": [...], "test_plan": [...]}
4. **Tester**: Executa pytest e valida código
5. **QA**: Verifica cobertura de testes
6. **Reviewer**: Faz code review e gera REVIEW.md
7. **Release**: Cria PR no GitHub

### Router System (llm_client.py)
- **Committee Pattern**: Cada agente tem lista de modelos fallback
- **Fallback Automático**: Se modelo falha, tenta próximo da lista
- **force_json**: Pode forçar JSON mode ou permitir markdown

### Orchestrator Sentry (orchestrator_sentry.py)
- **Retry Logic**: Até 6 tentativas com estratégias adaptativas
- **Decisões Automáticas**:
  - action=retry: Tenta novamente
  - action=force_json: Força JSON mode no próximo
  - action=switch_planner: Muda modelo do Planner
  - action=new_branch_suffix: Gera novo nome de branch
- **Análise de Logs**: Parser inteligente detecta tipo de erro

## PROBLEMAS CRÍTICOS ATUAIS

### 1. PLANNER FALHA 100% (até hoje)
- **Sintoma**: "Todas as estratégias de sanitização falharam"
- **Root Cause Identificado**: Context Window Overflow (GPT-5 Codex analysis)
- **Tentativas**: 10 retries esgotados, 5 estratégias de JSON sanitizer
- **Modelos tentados**: Claude Sonnet 4.5, Gemini 2.5 Pro, GPT-4o

### 2. JSON SANITIZER (json_sanitizer.py)
Implementado com 5 estratégias progressivas:
1. Direct parse
2. Markdown extraction (```json blocks)
3. Common error fixes (trailing commas, quotes)
4. Fuzzy extraction (balanced braces)
5. Structural repair (aggressive cleanup)

**Resultado**: Funciona em testes isolados, falha na pipeline real

### 3. CORREÇÕES RECENTES
- ✓ run.py restaurado de backup (estava corrompido)
- ✓ .env corrigido (linha breaks)
- ✓ Prompts re-encodados UTF-8 (eram Latin-1)
- ✓ Spec truncado em linhas completas (não no meio do YAML)
- ✓ Lista de arquivos reduzida 60→3
- ⚠️ Spec simples (hello-world) → Planner funcionou MAS formato incorreto (falta "content")

### 4. ÚLTIMO SUCESSO PARCIAL
Execução com spec hello-world:
- ✓ Planner gerou JSON (primeira vez!)
- ✓ planner_coder_done com success=true
- ✗ KeyError: 'content' no patcher
- **Conclusão**: Formato JSON diferente do esperado

## PROMPTS DOS AGENTES

### planner_coder.md (Principal Problemático)
Solicita JSON:
```json
{
  "patches": [
    {"path": "relative/path.py", "content": "arquivo inteiro"}
  ],
  "test_plan": [...]
}
```

Mas recebe formato DESCONHECIDO sem chave "content".

## TECNOLOGIAS
- Python 3.12.10, .venv
- OpenRouter API (sk-or-v1-8106...)
- GitHub CLI (gh 2.81.0)
- Git branching automático
- pytest para validação

## HISTÓRICO
- 2+ semanas de desenvolvimento
- 20+ tentativas de execução TODAS falharam
- Múltiplos agentes (GPT-5, Grok, Gemini, Claude) tentaram resolver
- Usuário extremamente frustrado com falhas consecutivas
"""

# Perguntas para a junta
QUESTIONS = """
# PERGUNTAS CRÍTICAS PARA A JUNTA DE ESPECIALISTAS

## 1. ANÁLISE DE ARQUITETURA
- A arquitetura atual (Orchestrator → Sequential Agents → GitHub PR) é adequada?
- Quais são os principais gargalos arquiteturais?
- O padrão Committee + Fallback é eficaz ou causa mais problemas?

## 2. WORKFLOW PROPOSTO
- Qual seria o workflow IDEAL para uma fábrica de software com agentes IA?
- Devemos manter sequência linear ou paralelizar agentes?
- Decomposer e Architect agregam valor ou são overhead desnecessário?

## 3. CRÍTICAS AO MODELO ATUAL
- Por que o Planner consistentemente falha em gerar JSON válido?
- É viável esperar que LLMs gerem arquivos completos em JSON?
- O Orchestrator Sentry com 6 retries é estratégia correta?

## 4. ESTRATÉGIAS DE MELHORIA
- Como resolver definitivamente o problema do Planner?
- JSON Sanitizer é solução ou workaround que mascara problema maior?
- Devemos simplificar o formato de saída (ex: gerar arquivos .py direto)?

## 5. INTERFACE DE USUÁRIO (UI)
- A fábrica FlashSoft precisa de uma UI web?
- Que funcionalidades seriam essenciais na UI?
- Como integrar UI com pipeline CLI existente?
- Frameworks recomendados (Streamlit, Gradio, FastAPI+React, outros)?

## 6. RECOMENDAÇÕES IMEDIATAS
- Qual é a ação MAIS URGENTE para conseguir 1 execução completa bem-sucedida?
- Devemos descartar código atual e recomeçar, ou continuar iterando?
- Há exemplos de projetos similares (agent orchestration) que devemos estudar?

RESPONDA CADA SEÇÃO COM MÁXIMO DETALHE E FUNDAMENTAÇÃO TÉCNICA.
"""

def consult_model(model_key: str, model_info: dict):
    """Consulta um modelo específico e salva relatório"""
    model_id = model_info['id']
    model_name = model_info['name']
    
    print(f"\n{'='*80}")
    print(f"🤖 CONSULTANDO: {model_name}")
    print(f"   Model ID: {model_id}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    system_prompt = """You are a senior software architect and AI systems expert with deep knowledge of:
- LLM orchestration and agent-based systems
- Software factory automation
- JSON parsing and structured output from LLMs
- CI/CD pipelines and GitHub automation
- Python architecture and design patterns
- UI/UX for developer tools

Provide detailed, technical, and actionable analysis. Be critical but constructive."""

    user_prompt = f"{CONTEXT}\n\n{QUESTIONS}"
    
    try:
        print(f"⏳ Enviando prompt ({len(user_prompt)} chars)...")
        
        # CORREÇÃO: chat() espera system e user como args separados, não messages list
        response = chat(
            model=model_id,
            system=system_prompt,
            user=user_prompt,
            max_tokens=4000,
            temperature=0.3
        )
        
        elapsed = time.time() - start_time
        
        # Calcular tokens aproximados
        input_tokens = (len(system_prompt) + len(user_prompt)) // 4
        output_tokens = len(response) // 4
        
        print(f"✓ Resposta recebida!")
        print(f"  Tempo: {elapsed:.1f}s")
        print(f"  Input tokens: ~{input_tokens}")
        print(f"  Output tokens: ~{output_tokens}")
        print(f"  Total tokens: ~{input_tokens + output_tokens}")
        
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
        
        # Salvar JSON
        json_filename = f"logs/consulta_{model_key}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"  Salvo: {json_filename}")
        
        # Salvar texto legível
        txt_filename = f"logs/consulta_{model_key}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"CONSULTA À JUNTA DE ESPECIALISTAS\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Modelo: {model_name} ({model_id})\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tempo: {elapsed:.1f}s\n")
            f.write(f"Input tokens: ~{input_tokens}\n")
            f.write(f"Output tokens: ~{output_tokens}\n")
            f.write(f"Total tokens: ~{input_tokens + output_tokens}\n\n")
            f.write(f"{'='*80}\n")
            f.write(f"RESPOSTA:\n")
            f.write(f"{'='*80}\n\n")
            f.write(response)
        print(f"  Salvo: {txt_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        
        # Salvar erro
        error_filename = f"logs/consulta_{model_key}_ERROR.txt"
        with open(error_filename, 'w', encoding='utf-8') as f:
            f.write(f"ERRO NA CONSULTA\n")
            f.write(f"Modelo: {model_name} ({model_id})\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Erro: {str(e)}\n")
        
        return False

def main():
    print("\n" + "="*80)
    print("CONSULTA COMPLETA À JUNTA DE ESPECIALISTAS - FLASHSOFT")
    print("="*80)
    print(f"\nModelos a consultar:")
    for key, info in MODELS.items():
        print(f"  • {info['name']} ({info['id']})")
    print("\n")
    
    results = {}
    
    for model_key, model_info in MODELS.items():
        success = consult_model(model_key, model_info)
        results[model_key] = success
        
        # Pausa entre consultas
        if model_key != list(MODELS.keys())[-1]:
            print("\n⏸  Aguardando 3s antes da próxima consulta...")
            time.sleep(3)
    
    # Resumo final
    print(f"\n\n{'='*80}")
    print("RESUMO DA CONSULTA")
    print(f"{'='*80}\n")
    
    for model_key, success in results.items():
        model_name = MODELS[model_key]['name']
        status = "✓ SUCESSO" if success else "✗ FALHA"
        print(f"  {status}: {model_name}")
    
    successful = sum(1 for s in results.values() if s)
    print(f"\n  Total: {successful}/{len(MODELS)} consultas bem-sucedidas")
    
    print(f"\n{'='*80}")
    print("Relatórios salvos em:")
    print("  - logs/consulta_gemini25pro.json + .txt")
    print("  - logs/consulta_gpt5codex.json + .txt")
    print("  - logs/consulta_grok4.json + .txt")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
