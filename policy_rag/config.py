from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = PROJECT_ROOT / "web"
CACHE_DIR = PROJECT_ROOT / "cache"
DATA_DIR = PROJECT_ROOT / "data"


def default_source_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_value = os.getenv("POLICY_DOCS_SOURCE")
    if env_value:
        candidates.append(Path(env_value))
    candidates.extend(
        [
            PROJECT_ROOT / "Policy Documents",
            DATA_DIR / "policies",
            DATA_DIR / "policies.zip",
            Path(r"C:\Users\ADMIN\OneDrive\Downloads\Policy Documents.zip"),
        ]
    )
    return candidates

