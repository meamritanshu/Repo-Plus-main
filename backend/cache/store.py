"""
store.py — Thread-safe in-memory cache (plain Python dicts, no Pydantic).
"""
import threading
from typing import Optional

_lock = threading.Lock()
_CACHE: dict = {}


def get(repo_url: str) -> Optional[dict]:
    with _lock:
        return _CACHE.get(repo_url)


def set(repo_url: str, result: dict) -> None:
    with _lock:
        _CACHE[repo_url] = result


def has(repo_url: str) -> bool:
    with _lock:
        return repo_url in _CACHE


def clear(repo_url: str) -> None:
    with _lock:
        _CACHE.pop(repo_url, None)
