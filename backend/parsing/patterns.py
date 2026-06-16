"""Regex patterns for framework and architectural pattern detection.

These patterns are used during Tier 1 (deterministic) extraction to
identify frameworks, ORM usage, event-driven patterns, and service
boundaries without requiring any LLM calls.
"""

from __future__ import annotations

import re

# ──────────────────────────────────────────────────────────────────────────────
# FastAPI patterns
# ──────────────────────────────────────────────────────────────────────────────

FASTAPI_APP = re.compile(
    r"(?:app|application)\s*=\s*FastAPI\s*\(",
    re.IGNORECASE,
)

FASTAPI_ROUTER = re.compile(
    r"(\w+)\s*=\s*APIRouter\s*\(",
    re.IGNORECASE,
)

FASTAPI_ROUTE_DECORATOR = re.compile(
    r"@\s*(\w+)\.(get|post|put|delete|patch|options|head)\s*\(\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)

FASTAPI_DEPENDS = re.compile(
    r"Depends\s*\(\s*(\w+)",
)

# ──────────────────────────────────────────────────────────────────────────────
# Flask patterns
# ──────────────────────────────────────────────────────────────────────────────

FLASK_APP = re.compile(
    r"(?:app|application)\s*=\s*Flask\s*\(",
    re.IGNORECASE,
)

FLASK_BLUEPRINT = re.compile(
    r"(\w+)\s*=\s*Blueprint\s*\(",
    re.IGNORECASE,
)

FLASK_ROUTE_DECORATOR = re.compile(
    r"@\s*(\w+)\.route\s*\(\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)

FLASK_METHODS_ARG = re.compile(
    r"methods\s*=\s*\[([^\]]+)\]",
    re.IGNORECASE,
)

# ──────────────────────────────────────────────────────────────────────────────
# Django patterns
# ──────────────────────────────────────────────────────────────────────────────

DJANGO_URL_PATH = re.compile(
    r"path\s*\(\s*[\"']([^\"']+)[\"']\s*,\s*(\w[\w.]*)",
)

DJANGO_URL_RE_PATH = re.compile(
    r"re_path\s*\(\s*[\"']([^\"']+)[\"']\s*,\s*(\w[\w.]*)",
)

DJANGO_MODEL_CLASS = re.compile(
    r"class\s+(\w+)\s*\(\s*(?:models\.Model|Model)\s*\)",
)

DJANGO_VIEW_CLASS = re.compile(
    r"class\s+(\w+)\s*\(\s*(?:\w*View\w*)\s*\)",
)

DJANGO_ADMIN_REGISTER = re.compile(
    r"@\s*admin\.register\s*\(\s*(\w+)",
)

# ──────────────────────────────────────────────────────────────────────────────
# SQLAlchemy model patterns
# ──────────────────────────────────────────────────────────────────────────────

SQLALCHEMY_MODEL_CLASS = re.compile(
    r"class\s+(\w+)\s*\(\s*(?:Base|DeclarativeBase|DeclarativeMeta)\s*\)",
)

SQLALCHEMY_TABLE_NAME = re.compile(
    r"__tablename__\s*=\s*[\"']([^\"']+)[\"']",
)

SQLALCHEMY_COLUMN = re.compile(
    r"(\w+)\s*=\s*(?:Column|mapped_column|relationship)\s*\(",
)

SQLALCHEMY_RELATIONSHIP = re.compile(
    r"(\w+)\s*=\s*relationship\s*\(\s*[\"']?(\w+)[\"']?",
)

# ──────────────────────────────────────────────────────────────────────────────
# Pydantic patterns
# ──────────────────────────────────────────────────────────────────────────────

PYDANTIC_MODEL_CLASS = re.compile(
    r"class\s+(\w+)\s*\(\s*(?:BaseModel|BaseSettings)\s*\)",
)

PYDANTIC_FIELD = re.compile(
    r"(\w+)\s*:\s*(\w[\w\[\], |]*)\s*(?:=\s*Field\s*\()?",
)

# ──────────────────────────────────────────────────────────────────────────────
# Event / messaging patterns
# ──────────────────────────────────────────────────────────────────────────────

EVENT_EMIT = re.compile(
    r"\.\s*(?:emit|fire|dispatch|send|publish)\s*\(\s*[\"']([^\"']+)[\"']",
)

EVENT_SUBSCRIBE = re.compile(
    r"\.\s*(?:on|subscribe|listen|register|add_listener)\s*\(\s*[\"']([^\"']+)[\"']",
)

EVENT_HANDLER_DECORATOR = re.compile(
    r"@\s*\w+\.\s*(?:on|listener|handler|subscribe)\s*\(\s*[\"']([^\"']+)[\"']",
)

# ──────────────────────────────────────────────────────────────────────────────
# Service boundary patterns
# ──────────────────────────────────────────────────────────────────────────────

DOCKERFILE = re.compile(
    r"^FROM\s+.+",
    re.MULTILINE,
)

DOCKER_COMPOSE_SERVICE = re.compile(
    r"^\s{2}(\w[\w-]*):\s*$",
    re.MULTILINE,
)

ENTRYPOINT_MAIN = re.compile(
    r"if\s+__name__\s*==\s*[\"']__main__[\"']",
)

SETUP_PY = re.compile(
    r"setup\s*\(",
)

PYPROJECT_TOML_PROJECT = re.compile(
    r"\[project\]",
)

# ──────────────────────────────────────────────────────────────────────────────
# Convenience catalogue
# ──────────────────────────────────────────────────────────────────────────────

FRAMEWORK_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "fastapi": [FASTAPI_APP, FASTAPI_ROUTER, FASTAPI_ROUTE_DECORATOR],
    "flask": [FLASK_APP, FLASK_BLUEPRINT, FLASK_ROUTE_DECORATOR],
    "django": [DJANGO_URL_PATH, DJANGO_MODEL_CLASS, DJANGO_VIEW_CLASS],
    "sqlalchemy": [SQLALCHEMY_MODEL_CLASS, SQLALCHEMY_TABLE_NAME],
    "pydantic": [PYDANTIC_MODEL_CLASS],
}


def detect_frameworks(source: str) -> list[str]:
    """Return the list of framework names detected in *source*.

    Scans the source text against all known framework patterns and returns
    the distinct framework identifiers whose patterns matched at least once.

    Args:
        source: The raw source code as a string.

    Returns:
        A list of framework name strings (e.g. ``["fastapi", "pydantic"]``).
    """
    found: list[str] = []
    for name, patterns in FRAMEWORK_PATTERNS.items():
        for pat in patterns:
            if pat.search(source):
                found.append(name)
                break  # one match is enough for this framework
    return found
