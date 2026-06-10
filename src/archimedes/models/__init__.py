"""Pydantic model package for Archimedes."""

from .base import ArchimedesModel, FlexibleContentModel, new_id, utc_now
from .artifacts import (
	AdrContent,
	HldContent,
	MermaidDiagram,
	OptionsContent,
	RequirementContent,
	VersionedArtifact,
	WafFinding,
	WafReviewContent,
)
from .claims import ClaimRecord
from .change import ChangeEvent, DependencyImpactResult
from .diffs import ArtifactDiff, FieldDiff
from .enums import DiffType, QualityGateStatus, SourceFreshness, StageName, StageStatus
from .evidence import EvidenceSource
from .patches import ApplyPatchResult, StagePatch
from .quality_gates import QualityGateCheck, QualityGateResult
from .session import ArchitectureSession, DEPENDENCY_RULES, DependencyMap, StageExecution

__all__ = [
	"ArchimedesModel",
	"FlexibleContentModel",
	"utc_now",
	"new_id",
	"StageName",
	"StageStatus",
	"QualityGateStatus",
	"RequirementContent",
	"OptionsContent",
	"MermaidDiagram",
	"AdrContent",
	"HldContent",
	"WafFinding",
	"WafReviewContent",
	"VersionedArtifact",
	"ClaimRecord",
	"EvidenceSource",
	"SourceFreshness",
	"DiffType",
	"ChangeEvent",
	"DependencyImpactResult",
	"FieldDiff",
	"ArtifactDiff",
	"StagePatch",
	"ApplyPatchResult",
	"QualityGateCheck",
	"QualityGateResult",
	"StageExecution",
	"ArchitectureSession",
	"DependencyMap",
	"DEPENDENCY_RULES",
]
