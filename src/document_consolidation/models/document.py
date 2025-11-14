"""Data models for document consolidation toolkit.

Pydantic models for type safety, validation, and serialization.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DocumentMetadata(BaseModel):
    """Metadata for a single document version."""

    path: Path
    folder: str
    content: str
    line_count: int
    modified_time: float
    hash: Optional[str] = None

    @field_validator("path", mode="before")
    @classmethod
    def convert_path(cls, v) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class ScoreBreakdown(BaseModel):
    """Individual scoring criteria breakdown."""

    completeness: float = Field(ge=0.0, le=10.0)
    recency: float = Field(ge=0.0, le=10.0)
    structure: float = Field(ge=0.0, le=10.0)
    citations: float = Field(ge=0.0, le=10.0)
    arguments: float = Field(ge=0.0, le=10.0)

    @property
    def total(self) -> float:
        """Calculate total score."""
        return (
            self.completeness
            + self.recency
            + self.structure
            + self.citations
            + self.arguments
        )


class TournamentResult(BaseModel):
    """Result of tournament evaluation for a document."""

    filename: str
    champion_folder: str
    champion_path: Path
    champion_score: float
    champion_breakdown: ScoreBreakdown
    all_scores: Dict[str, ScoreBreakdown]
    version_count: int
    runners_up: List[tuple[str, float]]

    @field_validator("champion_path", mode="before")
    @classmethod
    def convert_path(cls, v) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class SectionData(BaseModel):
    """Extracted markdown section data."""

    level: int = Field(ge=2, le=6, description="Header level (2-6 for ##-######)")
    title: str
    content: str
    line_start: int
    line_end: int


class UniqueImprovement(BaseModel):
    """Unique content improvement from non-champion version."""

    type: str = Field(
        description="Type: new_section, enhanced_section, citation_enhancement"
    )
    source_folder: str
    value: str = Field(description="Value rating: low, medium, high")
    reason: str

    # Optional fields based on type
    title: Optional[str] = None
    level: Optional[int] = None
    content: Optional[str] = None
    lines: Optional[str] = None
    similarity: Optional[float] = None
    additions_preview: Optional[str] = None
    citations: Optional[Dict[str, Dict[str, int]]] = None


class IntegrationResult(BaseModel):
    """Result of integrating improvements into champion document."""

    filename: str
    champion_folder: str
    champion_path: Path
    original_line_count: int
    integrated_line_count: int
    added_lines: int
    improvements_integrated: int
    source_folders: List[str]
    integrated_content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("champion_path", mode="before")
    @classmethod
    def convert_path(cls, v) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    @property
    def growth_percentage(self) -> float:
        """Calculate growth percentage."""
        if self.original_line_count == 0:
            return 0.0
        return (self.added_lines / self.original_line_count) * 100

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class VerificationIssue(BaseModel):
    """Document verification issue."""

    type: str = Field(
        description="Issue type: formatting, numbering, duplication, navigation"
    )
    severity: str = Field(description="Severity: low, medium, high")
    message: str
    line_number: Optional[int] = None


class VerificationResult(BaseModel):
    """Result of document verification."""

    filename: str
    filepath: Path
    line_count: int
    issues: List[VerificationIssue]
    passed: bool
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("filepath", mode="before")
    @classmethod
    def convert_path(cls, v) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    @property
    def issue_count(self) -> int:
        """Get total issue count."""
        return len(self.issues)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class CitationCounts(BaseModel):
    """Legal citation counts in a document."""

    matter_of: int = 0
    usc: int = 0
    cfr: int = 0
    ina: int = 0
    form_i: int = 0
    case_citations: int = 0

    @property
    def total(self) -> int:
        """Calculate total citation count."""
        return (
            self.matter_of
            + self.usc
            + self.cfr
            + self.ina
            + self.form_i
            + self.case_citations
        )
