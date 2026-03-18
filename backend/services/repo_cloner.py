"""
repo_cloner.py — Clone or update a GitHub repository.
"""

import logging
import os
import re
import shutil

import git

logger = logging.getLogger(__name__)


def clone_repository(repo_url: str, dest_dir: str) -> str:
    """
    Clone a GitHub repository into dest_dir.
    If already cloned, fetch latest changes.

    Args:
        repo_url: GitHub HTTPS URL.
        dest_dir: Parent directory to clone into.

    Returns:
        Absolute path to the cloned repository.

    Raises:
        ValueError: If URL is invalid.
        RuntimeError: If cloning fails.
    """
    if not _is_valid_github_url(repo_url):
        raise ValueError(f"Invalid GitHub URL: {repo_url}")

    os.makedirs(dest_dir, exist_ok=True)

    repo_name = _extract_repo_name(repo_url)
    repo_path = os.path.join(dest_dir, repo_name)

    if os.path.exists(repo_path):
        logger.info(f"Repo exists at {repo_path}. Fetching latest…")
        try:
            repo = git.Repo(repo_path)
            repo.remotes.origin.fetch()
            logger.info("Fetch complete.")
        except Exception as e:
            logger.warning(f"Fetch failed ({e}). Re-cloning…")
            shutil.rmtree(repo_path, ignore_errors=True)
            _do_clone(repo_url, repo_path)
    else:
        _do_clone(repo_url, repo_path)

    return repo_path


def _do_clone(repo_url: str, repo_path: str) -> None:
    logger.info(f"Cloning {repo_url} → {repo_path}")
    try:
        git.Repo.clone_from(repo_url, repo_path)
        logger.info("Clone complete.")
    except git.exc.GitCommandError as e:
        raise RuntimeError(f"Failed to clone: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected clone error: {e}") from e


def _is_valid_github_url(url: str) -> bool:
    pattern = r"^https?://github\.com/[\w.\-]+/[\w.\-]+(\.git)?/?$"
    return bool(re.match(pattern, url))


def _extract_repo_name(repo_url: str) -> str:
    clean = repo_url.rstrip("/").replace(".git", "")
    parts = clean.split("/")
    owner, repo = parts[-2], parts[-1]
    return f"{owner}__{repo}"
