import os
from git import Repo

# Path to the root of the repository
REPO_ROOT = os.path.abspath("../../../../")

# Ignore unnecessary directories
IGNORE_DIRS = {".git", "venv", "__pycache__", "node_modules", ".DS_Store"}


def list_repo_files():
    """
    Return all files in the repository except ignored directories
    """
    files = []

    for root, dirs, filenames in os.walk(REPO_ROOT):

        # remove ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for f in filenames:
            path = os.path.join(root, f)
            files.append(os.path.relpath(path, REPO_ROOT))

    return files


def read_file(path: str):
    """
    Read contents of a file in the repo
    """
    full_path = os.path.join(REPO_ROOT, path)

    if not os.path.exists(full_path):
        return "File not found"

    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def apply_patch(path: str, patch: str):
    """
    Overwrite file with new content
    """
    full_path = os.path.join(REPO_ROOT, path)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(patch)

    return {"status": "patched", "file": path}


def commit_changes(message: str):
    """
    Commit repo changes
    """
    repo = Repo(REPO_ROOT)

    repo.git.add(A=True)
    repo.index.commit(message)

    return {"status": "committed", "message": message}


def revert_commit(commit_hash: str = "HEAD~1"):
    """
    Revert to previous commit
    """
    repo = Repo(REPO_ROOT)

    repo.git.reset("--hard", commit_hash)

    return {"status": "reverted", "commit": commit_hash}