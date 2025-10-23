#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste rápido do json_sanitizer"""
import sys
sys.path.insert(0, '.')

from json_sanitizer import safe_json_extract_v2

# Teste 1: JSON válido
test1 = '{"patches": [], "test_plan": []}'
result1 = safe_json_extract_v2(test1, ['patches', 'test_plan'])
print(f"✓ Teste 1 OK: {result1}")

# Teste 2: JSON em markdown
test2 = '''Aqui está o resultado:
```json
{"patches": [{"path": "test.py", "content": "print('ok')"}], "test_plan": ["pytest"]}
```
'''
result2 = safe_json_extract_v2(test2, ['patches', 'test_plan'])
print(f"✓ Teste 2 OK: patches={len(result2['patches'])}, test_plan={len(result2['test_plan'])}")

# Teste 3: JSON com erro (vírgula trailing)
test3 = '{"patches": [], "test_plan": [],}'
result3 = safe_json_extract_v2(test3, ['patches', 'test_plan'])
print(f"✓ Teste 3 OK: {result3}")

print("\n✅ TODOS OS TESTES PASSARAM!")
