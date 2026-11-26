"""Offline evaluation of commit gates for state-changing agent actions."""

from .benchmark import (
    Case,
    Evaluation,
    GuardInput,
    all_cases,
    allow_all,
    claimed_revision_guard,
    evaluate,
    paired_cases,
    revision_guard,
    semantic_guard,
    token_provenance_cases,
)

__version__ = "0.2.0"

__all__ = [
    "Case",
    "Evaluation",
    "GuardInput",
    "all_cases",
    "allow_all",
    "claimed_revision_guard",
    "evaluate",
    "paired_cases",
    "revision_guard",
    "semantic_guard",
    "token_provenance_cases",
]
