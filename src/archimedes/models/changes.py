"""Compatibility module for change and diff models."""

from .change import ChangeEvent, DependencyImpactResult
from .diffs import ArtifactDiff, FieldDiff

__all__ = [
    "ChangeEvent",
    "DependencyImpactResult",
    "FieldDiff",
    "ArtifactDiff",
]
