"""Ferramenta de scaffolding para planos FlashSoft Architect."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Set, Tuple, Union

import jsonschema
from jsonschema import ValidationError

from utils.json_validation import SchemaValidationError, validate_plan as schema_validate_plan

logger = logging.getLogger(__name__)

FLASHSOFT_ARCHITECT_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "FlashSoft Architect Plan",
    "type": "object",
    "additionalProperties": False,
    "required": ["metadata", "components"],
    "properties": {
        "metadata": {
            "type": "object",
            "additionalProperties": False,
            "required": ["spec", "created_at", "architect"],
            "properties": {
                "spec": {"type": "string", "minLength": 1},
                "created_at": {"type": "string", "format": "date-time"},
                "architect": {"type": "string", "minLength": 1},
                "version": {"type": "string", "minLength": 1},
                "assumptions": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
            },
        },
        "components": {
            "type": "array",
            "minItems": 1,
            "items": {"$ref": "#/definitions/component"},
        },
        "notes": {"type": "string"},
    },
    "definitions": {
        "component": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "id",
                "description",
                "responsibilities",
                "dependencies",
                "files",
                "acceptance_tests",
            ],
            "properties": {
                "id": {
                    "type": "string",
                    "pattern": "^[a-z0-9_\\-]+$",
                    "minLength": 1,
                },
                "description": {"type": "string", "minLength": 1},
                "responsibilities": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                    "uniqueItems": True,
                    "default": [],
                },
                "files": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"$ref": "#/definitions/fileDescriptor"},
                },
                "acceptance_tests": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"$ref": "#/definitions/acceptanceTest"},
                },
            },
        },
        "fileDescriptor": {
            "type": "object",
            "additionalProperties": False,
            "required": ["path", "description"],
            "properties": {
                "path": {
                    "type": "string",
                    "pattern": "^[^\\0]+$",
                    "minLength": 1,
                },
                "description": {"type": "string", "minLength": 1},
                "type": {
                    "type": "string",
                    "enum": ["code", "config", "test", "doc", "asset", "script", "other"],
                },
                "generated": {"type": "boolean"},
            },
        },
        "acceptanceTest": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "description", "success_criteria"],
            "properties": {
                "id": {
                    "type": "string",
                    "pattern": "^[a-z0-9_\\-]+$",
                    "minLength": 1,
                },
                "description": {"type": "string", "minLength": 1},
                "target_files": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                    "uniqueItems": True,
                },
                "success_criteria": {"type": "string", "minLength": 1},
            },
        },
    },
}

_SUPPORTED_KEYWORDS: Set[str] = {"classe", "função", "funcao", "método", "metodo"}
_IDENTIFIER_CLEANUP_RE = re.compile(r"[^\w]")

def _normalize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return schema_validate_plan(plan, FLASHSOFT_ARCHITECT_SCHEMA)
    except SchemaValidationError as exc:
        logger.error("Plano invalido: %s", exc)
        raise ValueError(f"Plano invalido: {exc}") from exc


class StubSpec(NamedTuple):
    keyword: str
    name: str
    responsibility: str


def validate_plan(plan: Dict[str, Any]) -> None:
    """Valida o plano de scaffolding contra o schema oficial."""
    logger.debug("Validando plano conforme o schema FlashSoft Architect.")
    try:
        jsonschema.validate(instance=plan, schema=FLASHSOFT_ARCHITECT_SCHEMA)
    except ValidationError as exc:
        logger.error("Plano inválido: %s", exc.message)
        raise ValueError(f"Plano inválido: {exc.message}") from exc
    logger.debug("Plano validado com sucesso.")


def scaffold_from_plan(
    plan: Dict[str, Any], base_path: Union[str, Path]
) -> Dict[str, List[str]]:
    """Gera a estrutura de arquivos baseada no plano fornecido."""
    summary: Dict[str, List[str]] = {
        "created_files": [],
        "skipped_files": [],
        "errors": [],
    }

    plan = _normalize_plan(plan)
    validate_plan(plan)

    base_dir = Path(base_path)
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        message = f"Falha ao preparar diretório base {base_dir}: {exc}"
        logger.error(message)
        summary["errors"].append(message)
        return summary

    for component in plan.get("components", []):
        component_id = component.get("id", "sem_id")
        responsibilities = component.get("responsibilities", [])
        files = component.get("files", [])
        logger.debug(
            "Processando componente '%s' com %d arquivos.",
            component_id,
            len(files),
        )

        for file_descriptor in files:
            file_path = base_dir / Path(file_descriptor["path"])
            description = file_descriptor.get("description", "")

            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                message = f"Falha ao criar diretório para {file_path}: {exc}"
                logger.error(message)
                summary["errors"].append(message)
                continue

            if file_path.exists():
                logger.info(
                    "Arquivo já existente, não será sobrescrito: %s", file_path
                )
                summary["skipped_files"].append(
                    _path_to_summary(base_dir, file_path)
                )
                continue

            try:
                content = _render_file_content(
                    path=file_path,
                    description=description,
                    responsibilities=responsibilities,
                )
                file_path.write_text(content, encoding="utf-8")
                logger.info("Arquivo criado: %s", file_path)
                summary["created_files"].append(
                    _path_to_summary(base_dir, file_path)
                )
            except Exception as exc:  # noqa: BLE001
                message = f"Erro ao criar arquivo {file_path}: {exc}"
                logger.exception(message)
                summary["errors"].append(message)
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except OSError:
                        logger.warning(
                            "Não foi possível remover arquivo parcial: %s", file_path
                        )

    return summary


def _render_file_content(
    path: Path, description: str, responsibilities: Iterable[str]
) -> str:
    if path.suffix == ".py":
        return _generate_python_content(description, responsibilities)
    return _generate_generic_content(description)


def _generate_python_content(
    description: str, responsibilities: Iterable[str]
) -> str:
    stub_lines, needs_any = _build_stub_lines(responsibilities)
    if not stub_lines:
        stub_lines, needs_any = _default_stub(description)

    module_doc = _sanitize_docstring(description) or "Módulo gerado automaticamente."
    lines: List[str] = [f'"""{module_doc}"""', ""]

    if needs_any:
        lines.extend(["from typing import Any", ""])

    lines.extend(stub_lines)

    content = "\n".join(lines).rstrip() + "\n"
    return content


def _generate_generic_content(description: str) -> str:
    text = description.strip()
    return f"{text}\n" if text else ""


def _build_stub_lines(
    responsibilities: Iterable[str],
) -> Tuple[List[str], bool]:
    lines: List[str] = []
    needs_any = False
    seen: Set[Tuple[str, str]] = set()

    for responsibility in responsibilities:
        spec = _parse_responsibility(responsibility)
        if not spec:
            logger.debug("Responsabilidade ignorada para stubs: %s", responsibility)
            continue

        key = (spec.keyword, spec.name)
        if key in seen:
            logger.debug(
                "Responsabilidade duplicada para %s '%s' ignorada.",
                spec.keyword,
                spec.name,
            )
            continue
        seen.add(key)

        if spec.keyword == "classe":
            lines.extend(_generate_class_stub(spec.name, spec.responsibility))
        elif spec.keyword in {"função", "funcao"}:
            lines.extend(_generate_function_stub(spec.name, spec.responsibility))
            needs_any = True
        elif spec.keyword in {"método", "metodo"}:
            lines.extend(_generate_method_stub(spec.name, spec.responsibility))
            needs_any = True

    return lines, needs_any


def _default_stub(description: str) -> Tuple[List[str], bool]:
    doc = _sanitize_docstring(description) or "Implementação pendente."
    lines = [
        "def implement() -> None:",
        f'    """Implementação pendente para: {doc}"""',
        "    raise NotImplementedError('Implementação pendente para este módulo.')",
        "",
    ]
    return lines, False


def _generate_class_stub(name: str, responsibility: str) -> List[str]:
    doc = _sanitize_docstring(responsibility)
    return [
        f"class {name}:",
        f'    """{doc}"""',
        "",
        "    def __init__(self) -> None:",
        f'        """Inicializa {name}."""',
        f"        raise NotImplementedError('Classe {name} não implementada: {doc}')",
        "",
    ]


def _generate_function_stub(name: str, responsibility: str) -> List[str]:
    doc = _sanitize_docstring(responsibility)
    return [
        f"def {name}(*args: Any, **kwargs: Any) -> None:",
        f'    """{doc}"""',
        f"    raise NotImplementedError('Função {name} não implementada: {doc}')",
        "",
    ]


def _generate_method_stub(name: str, responsibility: str) -> List[str]:
    doc = _sanitize_docstring(responsibility)
    return [
        f"def {name}(*args: Any, **kwargs: Any) -> None:",
        f'    """{doc}"""',
        f"    raise NotImplementedError('Método {name} não implementado: {doc}')",
        "",
    ]


def _parse_responsibility(responsibility: str) -> Optional[StubSpec]:
    if not responsibility:
        return None

    normalized = " ".join(responsibility.strip().split())
    if not normalized:
        return None

    parts = normalized.split(maxsplit=1)
    if len(parts) < 2:
        return None

    keyword = parts[0].rstrip(":").lower()
    if keyword not in _SUPPORTED_KEYWORDS:
        return None

    rest = parts[1].strip()
    if not rest:
        return None

    name_token = rest.split()[0]
    identifier = _sanitize_identifier(name_token)
    if not identifier:
        return None

    return StubSpec(keyword=keyword, name=identifier, responsibility=normalized)


def _sanitize_identifier(token: str) -> str:
    sanitized = _IDENTIFIER_CLEANUP_RE.sub("", token)
    if sanitized and sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    return sanitized


def _sanitize_docstring(text: str) -> str:
    sanitized = text.replace('"""', r'\"\"\"')
    sanitized = sanitized.replace("\r\n", " ").replace("\n", " ")
    sanitized = " ".join(sanitized.split()).strip()
    return sanitized


def _path_to_summary(base: Path, target: Path) -> str:
    """
    Convert an absolute path to a forward-slash summary relative to the base directory.

    This helper ensures deterministic reporting on both Windows and POSIX systems.
    """
    try:
        relative = target.relative_to(base)
    except ValueError:
        relative = target
    return str(relative).replace("\\", "/")


__all__ = ["validate_plan", "scaffold_from_plan"]
