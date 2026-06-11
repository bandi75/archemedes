"""Socrates adversarial review workflow."""

from .dispatcher import DispatchMessage, DispatcherExecutor
from .persona import PersonaExecutor
from .synthesizer import SocratesSynthesizerExecutor
from .workflow import SocratesWorkflow, build_socrates_workflow

__all__ = [
    "DispatchMessage",
    "DispatcherExecutor",
    "PersonaExecutor",
    "SocratesSynthesizerExecutor",
    "SocratesWorkflow",
    "build_socrates_workflow",
]
