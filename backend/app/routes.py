"""
Flask REST API routes for RepoPulse.
"""

import logging
import os
import traceback

from flask import Blueprint, jsonify, request, current_app

from app.services.repo_cloner import clone_repository
from app.services.commit_analyzer import extract_commits
from app.services.hotspot_calculator import calculate_hotspots
from app.services.risk_engine import compute_risk_scores
from app.visualization.churn_chart import plot_top_files_by_risk, plot_churn_distribution
from app.visualization.heatmap import plot_directory_heatmap
from app.visualization.developer_graph import plot_developer_contributions
import config.settings as settings

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


@api_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "RepoPulse API"})


@api_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyze a GitHub repository for hotspots.

    Request body (JSON):
        repo_url (str): GitHub repository URL.
        max_commits (int, optional): Max commits to analyze. Default 500.

    Returns:
        JSON with risk scores, folder stats, developer stats, and chart URLs.
    """
    data = request.get_json(silent=True) or {}
    repo_url = (data.get("repo_url") or "").strip()
    max_commits = int(data.get("max_commits") or settings.MAX_COMMITS)
    max_commits = min(max(max_commits, 10), 1000)  # clamp between 10 and 1000

    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    if not (repo_url.startswith("https://github.com/") or repo_url.startswith("http://github.com/")):
        return jsonify({"error": "Only GitHub URLs are supported (https://github.com/...)"}), 400

    try:
        logger.info(f"Starting analysis for: {repo_url} (max_commits={max_commits})")

        # 1. Clone repository
        repo_path = clone_repository(repo_url, settings.TEMP_REPO_DIR)
        logger.info(f"Repository ready at: {repo_path}")

        # 2. Extract commits
        commits_df = extract_commits(repo_path, max_commits)
        if commits_df.empty:
            return jsonify({"error": "No commits found or repository is empty"}), 400
        logger.info(f"Extracted {len(commits_df)} commit-file rows")

        # 3. Calculate hotspots
        hotspot_df, folder_df, dev_df = calculate_hotspots(commits_df)
        logger.info(f"Hotspot calculation complete: {len(hotspot_df)} files")

        # 4. Compute risk scores
        risk_df = compute_risk_scores(hotspot_df)
        logger.info("Risk scores computed")

        # 5. Generate visualizations
        graphs_dir = os.path.join(current_app.static_folder, "generated_graphs")
        repo_slug = _repo_slug(repo_url)

        chart_files = {}
        chart_files["risk_bar"] = plot_top_files_by_risk(risk_df, graphs_dir, repo_slug)
        chart_files["churn_dist"] = plot_churn_distribution(hotspot_df, graphs_dir, repo_slug)
        chart_files["dir_heatmap"] = plot_directory_heatmap(folder_df, graphs_dir, repo_slug)
        chart_files["dev_graph"] = plot_developer_contributions(dev_df, graphs_dir, repo_slug)
        logger.info("Visualizations generated")

        # 6. Build response
        return jsonify({
            "repo_url": repo_url,
            "commits_analyzed": commits_df["commit_hash"].nunique(),
            "files_analyzed": len(hotspot_df),
            "risk_scores": risk_df.head(settings.TOP_N_FILES).to_dict(orient="records"),
            "folder_stats": folder_df.head(20).to_dict(orient="records"),
            "developer_stats": dev_df.head(20).to_dict(orient="records"),
            "charts": {k: f"/api/charts/{v}" for k, v in chart_files.items()},
        })

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        logger.error(f"Analysis failed: {traceback.format_exc()}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@api_bp.route("/charts/<path:filename>", methods=["GET"])
def serve_chart(filename):
    """Serve a generated chart PNG."""
    from flask import send_from_directory
    graphs_dir = os.path.join(current_app.static_folder, "generated_graphs")
    return send_from_directory(graphs_dir, filename)


def _repo_slug(repo_url: str) -> str:
    """Convert a GitHub URL into a filesystem-safe slug."""
    slug = repo_url.replace("https://github.com/", "").replace("/", "_").replace(".git", "")
    return slug[:60]  # limit length
