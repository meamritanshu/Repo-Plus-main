"""
test_analyzer.py — Unit tests for commit_analyzer module.
"""

import os
import sys
import pytest
import pandas as pd

# Add backend root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.commit_analyzer import extract_commits


class TestExtractCommits:
    """Tests for extract_commits function."""

    def test_invalid_path_raises_value_error(self):
        with pytest.raises(ValueError, match="Not a valid Git repository"):
            extract_commits("/tmp/definitely_not_a_repo_123456")

    def test_returns_dataframe(self, tmp_path):
        """extract_commits with a repo with one commit returns a DataFrame."""
        import subprocess
        repo_dir = tmp_path / "testrepo"
        repo_dir.mkdir()
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_dir,
                       check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir,
                       check=True, capture_output=True)
        # Need at least one commit so HEAD exists
        (repo_dir / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, capture_output=True)

        df = extract_commits(str(repo_dir), max_commits=10)
        assert isinstance(df, pd.DataFrame)

    def test_dataframe_schema(self, tmp_path):
        """Returned DataFrame must have the expected columns."""
        import subprocess
        repo_dir = tmp_path / "testrepo2"
        repo_dir.mkdir()
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_dir,
                       check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir,
                       check=True, capture_output=True)

        # Create a commit
        (repo_dir / "hello.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, capture_output=True)

        df = extract_commits(str(repo_dir), max_commits=10)
        expected_cols = {"commit_hash", "author", "timestamp", "file_path", "insertions", "deletions"}
        assert expected_cols.issubset(set(df.columns))
