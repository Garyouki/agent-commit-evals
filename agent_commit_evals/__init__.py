"""Offline evaluation of commit gates for state-changing agent actions."""

from .benchmark import (
    Case,
    Evaluation,
    GuardInput,
    allow_all,
    evaluate,
    paired_cases,
    revision_guard,
    semantic_guard,
)

__version__ = "0.1.0"

__all__ = [
    "Case",
    "Evaluation",
    "GuardInput",
    "allow_all",
    "evaluate",
    "paired_cases",
    "revision_guard",
    "semantic_guard",
]
