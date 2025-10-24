# SACI v2.0 - EVOLUÍDA (EM DESENVOLVIMENTO)

## ⚠️ STATUS: EXPERIMENTAL - NÃO USE EM PRODUÇÃO

Este diretório contém a **SACI v2.0 (EVOLUÍDA)** que está em desenvolvimento.

## 🐛 BUGS CONHECIDOS:

1. **Similaridade semântica sempre 0.0**
   - Causa: Case-sensitivity error (`Embeddings` vs `embeddings`)
   - Localização: `convergence_metrics.py`
   - Severidade: 9/10 (crítico)

2. **Threshold 0.75 inatingível**
   - Causa: Consequência do bug #1
   - Score máximo: 0.40 (sem embeddings)
   - Severidade: 6/10 (sintoma)

## 📋 ROADMAP v2.0:

### Antes de usar em produção:
- [ ] Corrigir bug de case-sensitivity
- [ ] Validar embeddings funcionando
- [ ] Ajustar threshold baseado em dados reais
- [ ] Executar 20+ debates comparativos vs v1.0
- [ ] Documentar superioridade comprovada

### Melhorias planejadas:
- [ ] Métricas de convergência semântica
- [ ] Early stopping inteligente
- [ ] Votos em JSON estruturado
- [ ] Rastreabilidade completa
- [ ] Logs de auditoria granulares

## ✅ USE ISTO EM PRODUÇÃO:

**`saci_v1.py`** (na raiz do repositório)

Veja: `SACI_V1_README.md` para documentação oficial.

## 📂 Estrutura v2.0:

```
saci/
├── __init__.py              # Helper function run_saci_debate()
├── convergence_metrics.py   # 🐛 BUG: case-sensitivity
├── round_manager.py         # Early stopping logic
└── trace_logger.py          # JSON auditability
```

## 🔬 Para Desenvolvedores:

Se você está trabalhando na v2.0:

1. **Corrija bugs primeiro** (veja diagnóstico em `SACI_DEBUG_CONSENSUS_4MODELS.md`)
2. **Teste isoladamente** antes de integrar
3. **Compare com v1.0** em debates reais
4. **Documente superioridade** antes de propor upgrade

## 📞 Referências:

- Diagnóstico completo: `SACI_DEBUG_CONSENSUS_4MODELS.md`
- Relatório executivo: `SACI_FINAL_EXECUTIVE_SUMMARY.md`
- Consenso de bugs: Logs em `logs/saci_antiga_debug_problemas.md`

---

**NÃO USE v2.0 ATÉ QUE DEMONSTRE SUPERIORIDADE SOBRE v1.0**
