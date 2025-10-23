# PLANO DE AÇÃO - BASEADO NA CONSULTA À JUNTA DE ESPECIALISTAS
# Gemini 2.5 PRO + GPT-5 CODEX + Grok 4

## PRIORIDADE 0 (CRÍTICA) - Fixar Planner AGORA

### 1. Criar Schema Pydantic para Output do Planner
```python
# planner_schema.py
from pydantic import BaseModel, Field
from typing import List

class PatchItem(BaseModel):
    path: str = Field(..., description="Caminho relativo do arquivo (ex: src/main.py)")
    content: str = Field(..., description="Conteúdo COMPLETO do arquivo após modificações")

class TestItem(BaseModel):
    description: str = Field(..., description="Descrição do teste a executar")
    command: str = Field(default="pytest", description="Comando de teste")

class PlannerOutput(BaseModel):
    patches: List[PatchItem] = Field(..., description="Lista de arquivos a criar/modificar")
    test_plan: List[TestItem] = Field(..., description="Plano de testes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "patches": [
                    {"path": "src/hello.py", "content": "def hello():\\n    return 'Hello, World!'"}
                ],
                "test_plan": [
                    {"description": "Testa função hello", "command": "pytest tests/test_hello.py"}
                ]
            }
        }
```

### 2. Atualizar planner_coder.md com FEW-SHOT EXAMPLES
Adicionar no final do prompt:

```markdown
## EXEMPLOS DE OUTPUT CORRETO:

### Exemplo 1 - Arquivo simples:
```json
{
  "patches": [
    {
      "path": "src/calculator.py",
      "content": "def add(a, b):\\n    return a + b\\n\\ndef subtract(a, b):\\n    return a - b\\n"
    }
  ],
  "test_plan": [
    {
      "description": "Testa operações matemáticas",
      "command": "pytest tests/test_calculator.py"
    }
  ]
}
```

### Exemplo 2 - Múltiplos arquivos:
```json
{
  "patches": [
    {
      "path": "src/utils.py",
      "content": "def format_name(name: str) -> str:\\n    return name.title()\\n"
    },
    {
      "path": "tests/test_utils.py",
      "content": "from src.utils import format_name\\n\\ndef test_format_name():\\n    assert format_name('john doe') == 'John Doe'\\n"
    }
  ],
  "test_plan": [
    {
      "description": "Valida formatação de nomes",
      "command": "pytest tests/test_utils.py -v"
    }
  ]
}
```

**IMPORTANTE:** 
- Cada "content" DEVE ser uma string com o arquivo COMPLETO
- Use \\n para quebras de linha, não quebras literais
- NÃO inclua comentários fora do JSON
- NÃO envolva em ```json``` - retorne APENAS o JSON puro
```

### 3. Modificar nodes/planner_coder.py para validar com Pydantic

```python
# No início do arquivo
from planner_schema import PlannerOutput

# Dentro do try do loop de tentativas:
try:
    out = router.call('planner', system, user, max_completion=3000, force_json=True)
    
    # VALIDAÇÃO IMEDIATA com Pydantic
    validated = PlannerOutput.model_validate_json(out)
    
    # Converter de volta para dict
    data = validated.model_dump()
    
    assert 'patches' in data and 'test_plan' in data, 'JSON invalido do PlannerCoder'
    return data
    
except ValidationError as ve:
    # Erro de validação Pydantic - gera prompt de correção
    last_error = f"Validation error: {ve.error_count()} errors - {ve.errors()[0]['msg']}"
    # Próxima tentativa incluirá esse erro no prompt
```

### 4. Reduzir Contexto Drasticamente

NO planner_coder.py:
```python
# Limitar spec a primeiras 20 linhas (não 15)
spec_lines = spec_dump.splitlines()
if len(spec_lines) > 20:
    spec_summary = '\n'.join(spec_lines[:20]) + '\n...(truncado)'
else:
    spec_summary = spec_dump

# Limitar a 2 arquivos apenas (não 3)
file_list_short = file_list[:2]

# Prompt SUPER simplificado
base_user_parts = [
    f"ESPECIFICAÇÃO:\\n{spec_summary}",
    f"ARQUIVOS EXISTENTES (amostra):\\n{json.dumps(file_list_short, ensure_ascii=False)}",
    "",
    "RETORNE APENAS JSON no formato PlannerOutput (ver schema acima).",
    "NÃO adicione comentários, NÃO envolva em markdown.",
    "Cada 'content' deve ser string com arquivo COMPLETO usando \\\\n para quebras de linha."
]
```

---

## PRIORIDADE 1 - Testar Planner Isoladamente

### Criar harness de teste:
```python
# test_planner_harness.py
import yaml
from nodes.planner_coder import run_planner_coder
from router import Router

specs = [
    "examples/specs/hello_world.yaml",
    # Adicionar mais specs gradualmente
]

for spec_path in specs:
    print(f"\\n{'='*80}")
    print(f"Testando: {spec_path}")
    print(f"{'='*80}")
    
    try:
        router = Router()
        result = run_planner_coder(router, ".", spec_path)
        
        print(f"✓ SUCESSO!")
        print(f"  Patches: {len(result['patches'])}")
        print(f"  Tests: {len(result['test_plan'])}")
        
        # Validar que todos patches têm 'content'
        for p in result['patches']:
            assert 'content' in p, f"Patch sem 'content': {p}"
            assert len(p['content']) > 0, f"Patch com content vazio: {p['path']}"
        
        print(f"✓ Validação estrutural OK")
        
    except Exception as e:
        print(f"✗ FALHA: {e}")
```

---

## PRIORIDADE 2 - Simplificar Committee

### Reduzir para 1 modelo primário + 1 fallback testado:
```python
# router.py - simplificar committee
COMMITTEES = {
    'planner': [
        'anthropic/claude-sonnet-4.5',  # Primário
        'google/gemini-2.5-pro'          # Fallback único
    ],
    # ... outros agentes
}
```

---

## PRIORIDADE 3 - Adicionar UI (MVP com Streamlit)

### Estrutura:
```
flashsoft_ui/
├── app.py                 # Streamlit main
├── api.py                 # FastAPI wrapper (opcional)
├── pages/
│   ├── 1_Upload_Spec.py
│   ├── 2_Monitor_Run.py
│   └── 3_View_Results.py
└── requirements_ui.txt
```

### app.py básico:
```python
import streamlit as st
import subprocess
import json

st.title("🏭 FlashSoft Factory")

uploaded_file = st.file_uploader("Upload spec YAML", type=['yaml', 'yml'])

if uploaded_file:
    spec_content = uploaded_file.read().decode('utf-8')
    st.code(spec_content, language='yaml')
    
    branch_name = st.text_input("Branch name", value="autobot/streamlit-test")
    
    if st.button("🚀 Run Factory"):
        with st.spinner("Executando pipeline..."):
            # Salvar spec temporário
            with open('/tmp/uploaded_spec.yaml', 'w') as f:
                f.write(spec_content)
            
            # Executar run_spec.ps1
            result = subprocess.run(
                ['powershell', './run_spec.ps1', '-Spec', '/tmp/uploaded_spec.yaml', '-Branch', branch_name],
                capture_output=True,
                text=True
            )
            
            st.write("### Output:")
            st.code(result.stdout)
            
            if result.returncode == 0:
                st.success("✓ Pipeline completado!")
            else:
                st.error(f"✗ Falha (exit code {result.returncode})")
```

---

## CRONOGRAMA SUGERIDO

### Dia 1 (HOJE)
- ✅ Schema Pydantic criado
- ✅ planner_coder.md atualizado com few-shot
- ✅ planner_coder.py modificado para validação
- ✅ Contexto reduzido

### Dia 2
- Test harness rodando com hello_world
- Ajustes no prompt baseado em falhas
- Conseguir 1 execução bem-sucedida end-to-end

### Dia 3-5
- Testar com specs progressivamente mais complexas
- Simplificar committee
- Documentar lições aprendidas

### Dia 6-7
- UI MVP com Streamlit
- Integração básica com pipeline

---

## MÉTRICAS DE SUCESSO

### Curto Prazo (24-48h)
- [ ] Planner gera JSON válido com 'content' em 90% das tentativas
- [ ] hello_world spec → PR aberto com sucesso
- [ ] KeyError: 'content' eliminado

### Médio Prazo (1 semana)
- [ ] Interview Assistant spec → PR aberto
- [ ] UI básica funcional
- [ ] Taxa de sucesso end-to-end > 70%

### Longo Prazo (2 semanas)
- [ ] UI completa com monitoramento
- [ ] Pipeline robusto com retry inteligente
- [ ] Documentação completa

---

## REFERÊNCIAS (conforme indicado pela junta)

- LangChain/LangGraph: https://github.com/langchain-ai/langgraph
- AutoGen (Microsoft): https://github.com/microsoft/autogen
- CrewAI: https://github.com/joaomdmoura/crewAI
- Pydantic validation: https://docs.pydantic.dev/latest/
- Streamlit: https://docs.streamlit.io/
