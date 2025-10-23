from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence


class RequirementError(Exception):
    """Raised when the generated plan violates mandatory requirements."""


EXPECTED_COMPONENT_KEYWORDS = {
    "audio": {"audio", "transcriber", "microphone", "whisper"},
    "documents": {"document", "parser", "pdf", "docx", "ingestion"},
    "retrieval": {"retrieval", "vector", "embeddings", "rag"},
    "generation": {"generation", "llm", "response"},
    "overlay": {"overlay", "ui", "view", "hotkey"},
    "observability": {"metrics", "logging", "observability"},
}


@dataclass
class PlanComponent:
    component_id: str
    description: str

    @property
    def tokens(self) -> set[str]:
        return {token.lower() for token in self.component_id.split("_")} | {
            token.lower() for token in self.description.split()
        }


def _load_components(plan: Mapping[str, object]) -> List[PlanComponent]:
    components: Sequence[Mapping[str, object]] = plan.get("components", [])  # type: ignore[assignment]
    parsed: List[PlanComponent] = []
    for component in components:
        component_id = str(component.get("id", "")).strip()
        description = str(component.get("description", "")).strip()
        if component_id:
            parsed.append(PlanComponent(component_id=component_id, description=description))
    return parsed


def _covers_requirement(component: PlanComponent, keywords: Iterable[str]) -> bool:
    tokens = component.tokens
    return any(keyword in tokens for keyword in keywords)


def enforce_plan_requirements(plan: Mapping[str, object]) -> None:
    """
    Ensure that the architect plan covers all critical components.

    Raises:
        RequirementError: if a required subsystem is missing.
    """
    components = _load_components(plan)
    missing: List[str] = []

    for requirement, keywords in EXPECTED_COMPONENT_KEYWORDS.items():
        if not any(_covers_requirement(component, keywords) for component in components):
            missing.append(requirement)

    if missing:
        raise RequirementError(
            "Plano do Architect ausente dos modulos obrigatorios: "
            + ", ".join(sorted(missing))
        )


def enforce_artifact_presence(artifact_dir: Path, required_files: Sequence[Path]) -> None:
    missing = [path for path in required_files if not (artifact_dir / path).exists()]
    if missing:
        raise RequirementError(
            "Artefatos obrigatorios ausentes: " + ", ".join(str(p) for p in missing)
        )
