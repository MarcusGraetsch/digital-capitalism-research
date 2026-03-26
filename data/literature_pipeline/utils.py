#!/usr/bin/env python3
"""Shared utilities: logging, config loading, hashing."""

import os
import re
import hashlib
import logging
from datetime import datetime
from pathlib import Path

import yaml


PIPELINE_DIR = Path(__file__).parent
CONFIG_FILE = PIPELINE_DIR / "config.yaml"
LOG_FILE = PIPELINE_DIR / "literature_pipeline.log"

logger = logging.getLogger("literature_pipeline")


def setup_logging(level=logging.INFO):
    """Configure logging to file + console."""
    fmt = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(),
        ],
    )
    return logger


def _expand_env_vars(obj):
    """Recursively expand ${VAR:-default} patterns in config values."""
    pattern = re.compile(r"\$\{([^}]+)\}")

    def _replace(match):
        expr = match.group(1)
        if ":-" in expr:
            var, default = expr.split(":-", 1)
            return os.environ.get(var, default)
        return os.environ.get(expr, match.group(0))

    if isinstance(obj, str):
        return pattern.sub(_replace, obj)
    if isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env_vars(v) for v in obj]
    return obj


def load_config(path=None):
    """Load and return config dict with env vars expanded."""
    path = Path(path) if path else CONFIG_FILE
    with open(path) as f:
        raw = yaml.safe_load(f)
    return _expand_env_vars(raw)


def file_hash(path, algorithm="sha256"):
    """Compute file hash for deduplication."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def text_hash(text):
    """Hash text content (for dedup of extracted text)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sanitize_filename(name, max_len=80):
    """Convert a string into a safe filename."""
    name = re.sub(r"[^\w\s-]", "", name.lower())
    name = re.sub(r"[\s]+", "_", name.strip())
    return name[:max_len]


def repo_root():
    """Return the repo root from config or default."""
    cfg = load_config()
    return Path(cfg["paths"]["repo_root"])


def source_library():
    """Return the external source library path."""
    cfg = load_config()
    return Path(cfg["paths"]["source_library"])
