# -*- coding: utf-8 -*-
"""
JSON Sanitizer Agent - Limpa e extrai JSON de respostas LLM imperfeitas
"""
import re
import json
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class JSONSanitizerAgent:
    """
    Agente especializado em extrair e corrigir JSON de respostas LLM.
    Usa estratégias progressivamente mais tolerantes.
    """

    def sanitize(self, input_text: str, expected_keys: Optional[list] = None) -> Optional[Dict[str, Any]]:
        """
        Tenta extrair JSON válido de texto usando múltiplas estratégias.
        
        Args:
            input_text: Texto bruto retornado pelo LLM
            expected_keys: Lista de chaves esperadas no JSON (ex: ['patches', 'test_plan'])
            
        Returns:
            Dict se sucesso, None se falha em todas as estratégias
        """
        strategies = [
            self._parse_direct,
            self._extract_markdown_json,
            self._fix_common_errors,
            self._fuzzy_extract,
            self._structural_repair
        ]

        for strategy in strategies:
            try:
                result = strategy(input_text)
                if result and self._validate_structure(result, expected_keys):
                    logger.info(f"✅ JSON sanitizado via {strategy.__name__}")
                    return result
            except Exception as e:
                logger.debug(f"Estratégia {strategy.__name__} falhou: {e}")
                continue

        logger.error("❌ Todas as estratégias de sanitização falharam")
        return None

    def _parse_direct(self, text: str) -> Optional[Dict]:
        """Tentativa 1: Parse direto (JSON já está válido)"""
        return json.loads(text.strip())

    def _extract_markdown_json(self, text: str) -> Optional[Dict]:
        """Tentativa 2: Extrai JSON de blocos markdown ```json```"""
        pattern = r'```(?:json)?\s*\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                return json.loads(match.strip())
            except:
                continue
        
        raise ValueError("Nenhum bloco JSON válido encontrado em markdown")

    def _fix_common_errors(self, text: str) -> Optional[Dict]:
        """Tentativa 3: Corrige erros comuns (vírgulas, aspas)"""
        # Remove comentários // e /* */
        text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        
        # Remove trailing commas antes de } e ]
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Corrige aspas simples para duplas em chaves
        text = re.sub(r"'(\w+)'(\s*):", r'"\1"\2:', text)
        
        # Tenta parse
        return json.loads(text.strip())

    def _fuzzy_extract(self, text: str) -> Optional[Dict]:
        """Tentativa 4: Extração fuzzy (encontra primeiro { até último })"""
        # Encontra primeiro { e último } balanceado
        start = text.find('{')
        if start == -1:
            raise ValueError("Nenhum objeto JSON encontrado")
        
        # Conta balanceamento de { }
        balance = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == '{':
                balance += 1
            elif text[i] == '}':
                balance -= 1
                if balance == 0:
                    end = i + 1
                    break
        
        if balance != 0:
            raise ValueError("JSON não balanceado")
        
        json_text = text[start:end]
        return json.loads(json_text)

    def _structural_repair(self, text: str) -> Optional[Dict]:
        """Tentativa 5: Reparo estrutural agressivo"""
        # Remove tudo antes do primeiro { e depois do último }
        text = re.sub(r'^[^{]*', '', text)
        text = re.sub(r'[^}]*$', '', text)
        
        # Garante que arrays e objetos estão fechados
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        text += '}' * open_braces
        text += ']' * open_brackets
        
        # Remove quebras de linha dentro de strings
        text = re.sub(r'"\s*\n\s*"', '" "', text)
        
        return json.loads(text)

    def _validate_structure(self, data: Dict, expected_keys: Optional[list]) -> bool:
        """Valida se o JSON tem as chaves esperadas"""
        if expected_keys is None:
            return True
        
        return all(key in data for key in expected_keys)


def safe_json_extract_v2(text: str, expected_keys: Optional[list] = None) -> Dict[str, Any]:
    """
    Versão melhorada de safe_json_extract usando o Sanitizer Agent.
    
    Args:
        text: Resposta bruta do LLM
        expected_keys: Chaves obrigatórias (ex: ['patches', 'test_plan'])
        
    Returns:
        Dict com JSON extraído
        
    Raises:
        ValueError se todas as estratégias falharem
    """
    sanitizer = JSONSanitizerAgent()
    result = sanitizer.sanitize(text, expected_keys)
    
    if result is None:
        raise ValueError(f"Falha ao extrair JSON. Texto original: {text[:200]}...")
    
    return result
