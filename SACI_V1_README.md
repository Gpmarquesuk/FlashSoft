# SACI v1.0 - Sistema Avançado de Convergência de Ideias

## 📋 DEFINIÇÃO OFICIAL

**SACI = 4 modelos específicos de IA que debatem até obter consenso majoritário.**

### 🤖 Modelos Oficiais (FIXOS, NÃO ALTERAR):

1. **Claude Sonnet 4.5** (`anthropic/claude-sonnet-4.5`)
2. **GPT-5 Codex** (`openai/gpt-5-codex`)
3. **Gemini 2.5 PRO** (`google/gemini-2.5-pro`)
4. **Grok 4** (`x-ai/grok-4`)

---

## 🎯 USO OFICIAL

### Import e execução básica:

```python
from saci_v1 import debate_saci

# Definir problema
problema = "Qual banco de dados usar: PostgreSQL ou MongoDB?"
contexto = "Sistema de e-commerce com alta consistência transacional"

# Executar debate
resultado = debate_saci(
    problema=problema,
    contexto=contexto,
    max_rodadas=3
)

# Resultado
if resultado['consenso']:
    print(f"✅ Consenso atingido!")
    print(f"Solução: {resultado['solucao_final']}")
else:
    print(f"❌ Sem consenso após {len(resultado['rodadas'])} rodadas")
```

### Verificar disponibilidade:

```python
from saci_v1 import verificar_saci_disponivel

status = verificar_saci_disponivel()
print(status)
# {'claude': True, 'codex': True, 'gemini': False, 'grok': True}
```

### Informações da versão:

```python
from saci_v1 import get_saci_info

info = get_saci_info()
print(f"Versão: {info['versao']}")
print(f"Modelos: {len(info['modelos'])}")
```

---

## 📊 METODOLOGIA

### Como funciona:

1. **Rodada 1:** Cada modelo recebe o problema e propõe uma solução
2. **Rodada 2+:** Modelos avaliam propostas anteriores e refinam suas posições
3. **Convergência:** Quando 3/4 (75%+) concordam, o debate termina
4. **Sem consenso:** Após max_rodadas, retorna sem solução consensual

### Parâmetros:

- `problema`: Questão/desafio a ser debatido (obrigatório)
- `contexto`: Informações adicionais relevantes (opcional)
- `max_rodadas`: Número máximo de iterações (padrão: 3)
- `threshold_consenso`: % de concordância necessária (padrão: 0.75 = 3/4)
- `output_dir`: Diretório para logs (padrão: "logs")
- `verbose`: Mostrar progresso (padrão: True)

### Retorno:

```python
{
    'consenso': bool,              # True se atingiu consenso
    'solucao_final': str,          # Solução consensual ou None
    'votos': dict,                 # Distribuição de votos
    'rodadas': list,               # Histórico completo
    'timestamp': str,              # ISO timestamp
    'versao': '1.0'
}
```

---

## 🔄 ROADMAP DE VERSÕES

### ✅ SACI v1.0 (ATUAL - ESTÁVEL)

**Status:** PRODUÇÃO  
**Quando usar:** SEMPRE, até que v2.0 prove superioridade

**Características:**
- ✅ 4 modelos fixos e testados
- ✅ Debate estruturado em rodadas
- ✅ Consenso por votação majoritária (3/4)
- ✅ Logs JSON completos
- ✅ Simples e confiável

**Limitações conhecidas:**
- ⚠️ Extração de votos por keywords (não JSON estruturado)
- ⚠️ Sem métricas de convergência semântica
- ⚠️ Early stopping apenas por consenso de votos
- ⚠️ Sem rastreabilidade granular

---

### 🚧 SACI v2.0 - EVOLUÍDA (EM DESENVOLVIMENTO)

**Status:** EXPERIMENTAL (diretório `saci/`)  
**Quando usar:** APENAS para testes, NÃO em produção

**Melhorias planejadas:**
- 🔄 Métricas de convergência semântica (embeddings OpenAI)
- 🔄 Early stopping inteligente (threshold adaptativo)
- 🔄 Votos em JSON estruturado (parsing robusto)
- 🔄 Rastreabilidade completa (auditoria por round)
- 🔄 Pesos configuráveis (semantic vs votes)

**Bugs conhecidos v2.0:**
- 🐛 Similaridade semântica retorna 0.0 (case-sensitivity)
- 🐛 Threshold 0.75 inatingível sem embeddings
- 🐛 Fallback silencioso mascara erros

**Quando migrar para v2.0:**
- ✅ Bugs corrigidos e validados
- ✅ Testes comparativos mostram superioridade
- ✅ Consenso de que métricas quantitativas agregam valor real
- ✅ Decisão explícita de upgrade

---

## ⚠️ REGRAS DE USO

### ❌ O QUE NÃO FAZER:

1. **NÃO altere os 4 modelos da SACI**
   - Se um modelo não funciona, investigue o problema
   - NÃO substitua por outros modelos
   - NÃO chame de "SACI" se usar modelos diferentes

2. **NÃO use v2.0 em produção**
   - Ainda está em desenvolvimento
   - Bugs conhecidos não resolvidos
   - Pode mudar sem aviso

3. **NÃO crie variações "SACI-like"**
   - SACI = ferramenta específica, não conceito genérico
   - Se precisar de algo diferente, dê outro nome

### ✅ O QUE FAZER:

1. **Use `saci_v1.py` para debates de produção**
2. **Reporte bugs/limitações da v1.0**
3. **Teste v2.0 em ambiente separado**
4. **Documente comparações v1.0 vs v2.0**

---

## 📁 ESTRUTURA DO REPOSITÓRIO

```
FlashSoft/
├── saci_v1.py              # ✅ SACI v1.0 OFICIAL (USE ESTE)
├── SACI_V1_README.md       # ✅ Este arquivo
│
├── saci/                   # 🚧 SACI v2.0 - EM DESENVOLVIMENTO
│   ├── __init__.py
│   ├── convergence_metrics.py
│   ├── round_manager.py
│   └── trace_logger.py
│
├── saci_experiments/       # 📦 EXPERIMENTOS ARQUIVADOS
│   ├── saci_product_strategy.py
│   ├── saci_meta_debate.py
│   ├── saci_evolution_debate.py
│   └── ...
│
└── logs/                   # 📊 Logs de debates
    ├── saci_debate_*.json
    └── saci_convergencia.txt
```

---

## 🧪 TESTES E VALIDAÇÃO

### Teste rápido:

```bash
python saci_v1.py
```

Deve executar um debate exemplo sobre PostgreSQL vs MongoDB.

### Teste de disponibilidade:

```python
from saci_v1 import verificar_saci_disponivel

status = verificar_saci_disponivel()
assert all(status.values()), "Algum modelo da SACI não está disponível!"
```

---

## 📚 CASOS DE USO

### 1. Decisões Arquiteturais

```python
resultado = debate_saci(
    problema="Qual padrão de arquitetura: Microservices ou Monolith Modular?",
    contexto="Startup com 5 devs, MVP em 3 meses, escalabilidade futura importante"
)
```

### 2. Debugging Complexo

```python
resultado = debate_saci(
    problema="Por que o sistema trava após 10k requisições simultâneas?",
    contexto="Stack: Node.js + PostgreSQL + Redis. Logs indicam timeout no DB."
)
```

### 3. Trade-offs Técnicos

```python
resultado = debate_saci(
    problema="REST vs GraphQL vs gRPC para nossa API pública?",
    contexto="Clientes web/mobile, documentação importante, performance crítica"
)
```

---

## 🤝 CONTRIBUINDO

### Para melhorar v1.0:

1. Reporte bugs via issues
2. Proponha melhorias na extração de votos
3. Adicione exemplos de uso
4. Melhore documentação

### Para desenvolver v2.0:

1. Trabalhe no diretório `saci/`
2. Corrija bugs conhecidos primeiro
3. Valide com testes comparativos
4. Documente superioridade antes de propor upgrade

---

## 📝 CHANGELOG

### v1.0 (24/10/2025) - VERSÃO INICIAL ESTÁVEL

- ✅ 4 modelos oficiais definidos
- ✅ Debate estruturado em rodadas
- ✅ Consenso por votação majoritária
- ✅ Logs JSON completos
- ✅ Funções auxiliares (verificar_saci_disponivel, get_saci_info)

---

## 📞 SUPORTE

- **Bugs:** Abra issue no repositório
- **Dúvidas:** Consulte este README primeiro
- **Melhorias:** PRs são bem-vindos (para v1.0)

---

## ⚖️ LICENÇA

Parte do projeto FlashSoft.  
Uso interno e desenvolvimento colaborativo.

---

**VERSÃO OFICIAL: 1.0**  
**STATUS: PRODUÇÃO ✅**  
**ÚLTIMA ATUALIZAÇÃO: 24/10/2025**
