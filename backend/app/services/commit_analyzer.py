"""
commit_analyzer.py — Mine commit history from a local Git repository.
"""

import logging
import os
from datetime import datetime

import git
import pandas as pd

logger = logging.getLogger(__name__)


def extract_commits(repo_path: str, max_commits: int = 500) -> pd.DataFrame:
    """
    Extract commit-level file change data from a local Git repository.

    Args:
        repo_path: Absolute path to the local Git repository.
        max_commits: Maximum number of commits to process.

    Returns:
        DataFrame with columns:
            commit_hash, author, timestamp, file_path, insertions, deletions

    Raises:
        ValueError: If repo_path is not a valid Git repository.
        RuntimeError: On unexpected Git errors.
    """
    if not os.path.exists(os.path.join(repo_path, ".git")):
        raise ValueError(f"Not a valid Git repository: {repo_path}")

    try:
        repo = git.Repo(repo_path)
    except git.exc.InvalidGitRepositoryError as e:
        raise ValueError(f"Invalid Git repository: {e}") from e

    rows = []
    commit_count = 0

    logger.info(f"Walking commits (max={max_commits})...")

    for commit in repo.iter_commits():
        if commit_count >= max_commits:
            break

        try:
            stats = commit.stats.files
        except Exception:
            commit_count += 1
            continue

        for file_path, file_stats in stats.items():
            rows.append({
                "commit_hash": commit.hexsha[:8],
                "author": commit.author.name,
                "timestamp": datetime.fromtimestamp(commit.committed_date),
                "file_path": file_path,
                "insertions": file_stats.get("insertions", 0),
                "deletions": file_stats.get("deletions", 0),
            })

        commit_count += 1

    if not rows:
        logger.warning("No commit data extracted.")
        return pd.DataFrame(columns=["commit_hash", "author", "timestamp", "file_path", "insertions", "deletions"])

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    logger.info(f"Extracted {commit_count} commits, {len(df)} file-change rows.")
    return df
