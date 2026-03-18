"""
hotspot_calculator.py — Aggregate commit data into file/folder/developer metrics.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def calculate_hotspots(df: pd.DataFrame):
    """
    From raw commit-file DataFrame, compute:
      - File-level metrics (frequency, churn).
      - Folder-level aggregated metrics.
      - Developer contribution summary.

    Args:
        df: DataFrame from commit_analyzer.extract_commits().

    Returns:
        Tuple of (hotspot_df, folder_df, dev_df)
    """
    if df.empty:
        empty = pd.DataFrame()
        return empty, empty, empty

    # ── File-level hotspot metrics ──────────────────────────────────────────
    file_stats = (
        df.groupby("file_path")
        .agg(
            commit_frequency=("commit_hash", "nunique"),
            total_insertions=("insertions", "sum"),
            total_deletions=("deletions", "sum"),
        )
        .reset_index()
    )
    file_stats["total_churn"] = file_stats["total_insertions"] + file_stats["total_deletions"]
    logger.info(f"File hotspots calculated: {len(file_stats)} files")

    # ── Folder-level aggregation ─────────────────────────────────────────────
    df["folder"] = df["file_path"].apply(_extract_folder)
    folder_stats = (
        df.groupby("folder")
        .agg(
            file_count=("file_path", "nunique"),
            commit_frequency=("commit_hash", "nunique"),
            total_churn=("insertions", "sum"),
        )
        .reset_index()
    )
    folder_stats["total_churn"] += df.groupby("folder")["deletions"].sum().values
    folder_stats = folder_stats.sort_values("commit_frequency", ascending=False)
    logger.info(f"Folder stats calculated: {len(folder_stats)} folders")

    # ── Developer contribution summary ───────────────────────────────────────
    dev_stats = (
        df.groupby("author")
        .agg(
            commit_count=("commit_hash", "nunique"),
            files_touched=("file_path", "nunique"),
            total_insertions=("insertions", "sum"),
            total_deletions=("deletions", "sum"),
        )
        .reset_index()
    )
    dev_stats["total_churn"] = dev_stats["total_insertions"] + dev_stats["total_deletions"]
    dev_stats = dev_stats.sort_values("commit_count", ascending=False)
    logger.info(f"Developer stats calculated: {len(dev_stats)} developers")

    return file_stats, folder_stats, dev_stats


def _extract_folder(file_path: str) -> str:
    """Return the top-level folder from a file path, or '(root)' if top-level."""
    parts = file_path.replace("\\", "/").split("/")
    return parts[0] if len(parts) > 1 else "(root)"
