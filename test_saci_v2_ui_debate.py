#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da SACI v2.1: Debate sobre a UI da SACI v3.0
==================================================

Este script executa a SACI v2.1 para debater a necessidade e a 
estratégia de implementação de uma interface de usuário para uma 
futura versão 3.0.

Objetivo:
----------
Validar a capacidade da SACI v2.1 de lidar com um problema complexo
e estratégico, testando a análise de convergência semântica em um
cenário real.

Autor: FlashSoft Team
Data: 24/10/2025
"""

import os
from saci.saci_v2 import debate_saci_v2

# Instalar dependências se necessário
try:
    import numpy
except ImportError:
    print("Instalando numpy...")
    os.system("pip install numpy")

# ============================================================================
# DEFINIÇÃO DO PROBLEMA
# ============================================================================

problema_debate = "A SACI v3.0 precisa de uma Interface de Usuário (UI)?"

contexto_debate = """
Se a resposta for sim, detalhe a estratégia de implementação.

Considere os seguintes pontos:
1.  **Público-Alvo:** Quem usará a UI? (Desenvolvedores, Analistas de Negócio, Gestores de Projeto?)
2.  **Tipo de Interface:**
    -   Web App (React, Vue, etc.)
    -   Terminal UI (TUI) rica (ex: com Textual)
    -   Integração com IDE (Plugin para VS Code)
    -   Dashboard simples (Streamlit, Gradio)
3.  **Funcionalidades Essenciais:**
    -   Formulário para iniciar novos debates.
    -   Visualização em tempo real do progresso do debate.
    -   Visualização do histórico de debates e logs.
    -   Exibição das métricas de convergência semântica.
    -   Comparativo de respostas entre modelos em cada rodada.
4.  **Arquitetura:** Como a UI se comunicaria com o backend da SACI? (API REST, WebSockets, etc.)
5.  **MVP (Minimum Viable Product):** Qual seria o conjunto mínimo de funcionalidades para a primeira versão da UI?
"""

# ============================================================================
# EXECUÇÃO DO DEBATE
# ============================================================================

print("Iniciando debate sobre a UI da SACI v3.0 com a SACI v2.1...")

try:
    resultado_final = debate_saci_v2(
        problema=problema_debate,
        contexto=contexto_debate,
        max_rodadas=3,
        verbose=True,
        debug_mode=False # <-- EXECUTANDO EM MODO DE PRODUÇÃO COM MODELOS PAGOS
    )

    # ============================================================================
    # APRESENTAÇÃO DOS RESULTADOS
    # ============================================================================

    print("\n" + "="*80)
    print("📊 RESULTADO FINAL DO DEBATE (SACI v2.1)")
    print("="*80)

    if resultado_final['consenso']:
        print("\n✅ Consenso Atingido!")
        print("\n--- Solução Final ---")
        print(resultado_final['solucao_final'])
    else:
        print("\n❌ Não foi possível atingir um consenso dentro do número máximo de rodadas.")
        if resultado_final.get('solucao_final'):
             print("\n--- Síntese da Melhor Tentativa ---")
             print(resultado_final['solucao_final'])

    print(f"\nTotal de rodadas executadas: {len(resultado_final['rodadas'])}")
    
    # Detalhes da última rodada
    if resultado_final['rodadas']:
        ultima_rodada = resultado_final['rodadas'][-1]
        analise = ultima_rodada.get('analise_convergencia', {})
        if analise.get('metodo') == 'semantico':
            print(f"Métrica de Convergência Final: {analise.get('score', 'N/A'):.2f}")
        else:
            print(f"Votos da Última Rodada (Fallback): {analise.get('votos', 'N/A')}")

except Exception as e:
    print(f"\n\n🚨 Ocorreu um erro crítico durante a execução do debate: {e}")
    print("   Por favor, verifique as chaves de API e a conexão com a internet.")

