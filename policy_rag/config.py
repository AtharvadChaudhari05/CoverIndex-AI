from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional in test/runtime environments
    def load_dotenv(*args, **kwargs):  # type: ignore[override]
        return False

# Load environment variables from .env file
load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = PROJECT_ROOT / "public"
CACHE_DIR = PROJECT_ROOT / "cache"
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_DIR = PROJECT_ROOT / "prompts"


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
        ]
    )
    return candidates


@lru_cache(maxsize=None)
def load_prompt_text(prompt_filename: str) -> str:
    prompt_path = PROMPTS_DIR / prompt_filename
    return prompt_path.read_text(encoding="utf-8")


def load_system_prompt(mode: str = "insurance_rag") -> str:
    if mode == "fallback_confirmed":
        return load_prompt_text("system_prompt_fallback_confirmed.md")
    return load_prompt_text("system_prompt_insurance_rag.md")


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def allow_out_of_scope_answers() -> bool:
    return env_flag("ALLOW_OUT_OF_SCOPE_ANSWERS", False)


def require_fallback_confirmation() -> bool:
    return env_flag("REQUIRE_FALLBACK_CONFIRMATION", True)
