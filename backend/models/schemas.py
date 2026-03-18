"""
schemas.py — Pydantic v2 models for RepoPulse API.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


# ── Request Models ────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository HTTPS URL")
    commit_depth: int = Field(default=200, ge=10, le=1000, description="Max commits to analyze")


# ── Tree Response ─────────────────────────────────────────────────────────────

class FileNode(BaseModel):
    type: str = "file"
    name: str
    path: str
    risk_score: float = 0.0
    commit_count: int = 0
    churn: int = 0


class TreeNode(BaseModel):
    type: str = "folder"
    name: str
    path: str
    children: list[Any] = Field(default_factory=list)


# ── Heatmap Response ──────────────────────────────────────────────────────────

class LineHeat(BaseModel):
    line_number: int
    modification_count: int
    normalized_intensity: float


# ── Developer Stat ────────────────────────────────────────────────────────────

class DevStat(BaseModel):
    author: str
    commit_count: int
    insertions: int
    deletions: int


# ── Timeline Entry ────────────────────────────────────────────────────────────

class TimelineEntry(BaseModel):
    date: str
    commits: int
    churn: int


from typing import Optional

# ── File Metrics Response ─────────────────────────────────────────────────────

class FileMetrics(BaseModel):
    commit_count: int
    churn: int
    insertions: int
    deletions: int
    risk_score: float
    developer_stats: list[DevStat]
    timeline: list[TimelineEntry]
    last_commit_date: Optional[str] = None
    top_contributor: Optional[str] = None


# ── Analysis Result (stored in cache) ────────────────────────────────────────

class FileStats(BaseModel):
    file_path: str
    commit_count: int = 0
    insertions: int = 0
    deletions: int = 0
    churn: int = 0
    risk_score: float = 0.0
    norm_frequency: float = 0.0
    norm_churn: float = 0.0
    developer_stats: list[DevStat] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    last_commit_date: Optional[str] = None
    top_contributor: Optional[str] = None


class AnalysisResult(BaseModel):
    repo_url: str
    repo_path: str
    commit_count: int
    file_stats: dict[str, FileStats]
    # line_churn: file_path → { line_number → count }
    line_churn: dict[str, dict[str, int]] = Field(default_factory=dict)
