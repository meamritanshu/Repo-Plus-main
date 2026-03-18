"""
test_risk_engine.py — Unit tests for the risk_engine module.
"""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.risk_engine import compute_risk_scores


class TestComputeRiskScores:
    """Tests for compute_risk_scores function."""

    def _make_df(self, data):
        return pd.DataFrame(data, columns=["file_path", "commit_frequency", "total_churn",
                                           "total_insertions", "total_deletions"])

    def test_empty_df_returns_empty(self):
        df = pd.DataFrame(columns=["file_path", "commit_frequency", "total_churn",
                                   "total_insertions", "total_deletions"])
        result = compute_risk_scores(df)
        assert result.empty

    def test_risk_score_column_exists(self):
        df = self._make_df([
            ("src/main.py", 10, 500, 300, 200),
            ("src/utils.py", 3, 50, 30, 20),
            ("README.md", 1, 10, 8, 2),
        ])
        result = compute_risk_scores(df)
        assert "risk_score" in result.columns

    def test_risk_score_bounded_0_1(self):
        df = self._make_df([
            ("a.py", 10, 1000, 600, 400),
            ("b.py", 5, 500, 300, 200),
            ("c.py", 1, 50, 30, 20),
        ])
        result = compute_risk_scores(df)
        assert (result["risk_score"] >= 0.0).all()
        assert (result["risk_score"] <= 1.0).all()

    def test_highest_freq_churn_gets_highest_risk(self):
        df = self._make_df([
            ("hot.py", 100, 10000, 6000, 4000),
            ("cool.py", 1, 5, 3, 2),
            ("medium.py", 10, 200, 100, 100),
        ])
        result = compute_risk_scores(df)
        assert result.iloc[0]["file_path"] == "hot.py"

    def test_sorted_descending(self):
        df = self._make_df([
            ("a.py", 10, 500, 300, 200),
            ("b.py", 2, 100, 60, 40),
            ("c.py", 50, 2000, 1200, 800),
        ])
        result = compute_risk_scores(df)
        scores = result["risk_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_single_file_returns_score_zero(self):
        df = self._make_df([("only.py", 5, 100, 60, 40)])
        result = compute_risk_scores(df)
        # With one file min==max, normalized values are 0 → risk_score = 0
        assert result.iloc[0]["risk_score"] == 0.0

    def test_rank_column_assigned(self):
        df = self._make_df([
            ("a.py", 10, 500, 300, 200),
            ("b.py", 2, 50, 30, 20),
        ])
        result = compute_risk_scores(df)
        assert "rank" in result.columns
        assert result.iloc[0]["rank"] == 1
