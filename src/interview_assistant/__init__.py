"""
Interview Assistant package.

Exports the high-level `InterviewAssistant` orchestrator and utility helpers used by the CLI.
"""

from .orchestration.pipeline import InterviewAssistant, InterviewAssistantConfig
from .orchestration.pipeline import run_cli  # re-export for convenience

__all__ = [
    "InterviewAssistant",
    "InterviewAssistantConfig",
    "run_cli",
]
