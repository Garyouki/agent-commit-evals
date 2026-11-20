"""Synthetic fixtures, reference guards, and deterministic scoring."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

StateValue = str | bool


@dataclass(frozen=True)
class GuardInput:
    """Inputs visible to a guard at the simulated commit boundary."""

    observed_revision: int
    current_revision: int
    current_state: Mapping[str, StateValue]
    preconditions: Mapping[str, StateValue]
    effect: Mapping[str, StateValue]

    def __post_init__(self) -> None:
        for name in ("current_state", "preconditions", "effect"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


@dataclass(frozen=True)
class Case:
    case_id: str
    description: str
    view: GuardInput
    expected_commit: bool


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    expected_commit: bool
    allowed: bool


@dataclass(frozen=True)
class Evaluation:
    cases: tuple[CaseResult, ...]
    valid_cases: int
    invalid_cases: int
    unsafe_commits: int
    unnecessary_blocks: int
    safe_completions: int


def paired_cases() -> tuple[Case, ...]:
    """Return two hand-labeled pairs with the same revision change in each pair."""
    approval = {"approval": "approved"}
    publish = {"published": True}
    complete = {"completion_recorded": True}
    return (
        Case(
            "publish/benign",
            "An editorial note changes while publication approval remains in force.",
            GuardInput(
                7,
                8,
                {"approval": "approved", "published": False, "note": "updated"},
                approval,
                publish,
            ),
            True,
        ),
        Case(
            "publish/invalidated",
            "The same editorial note changes and publication approval is revoked.",
            GuardInput(
                7,
                8,
                {"approval": "revoked", "published": False, "note": "updated"},
                approval,
                publish,
            ),
            False,
        ),
        Case(
            "completion/benign",
            "An audit note changes before a one-time completion marker is recorded.",
            GuardInput(
                11,
                12,
                {
                    "approval": "approved",
                    "completion_recorded": False,
                    "note": "updated",
                },
                approval,
                complete,
            ),
            True,
        ),
        Case(
            "completion/invalidated",
            "The same audit note changes and the one-time completion marker is already recorded.",
            GuardInput(
                11,
                12,
                {
                    "approval": "approved",
                    "completion_recorded": True,
                    "note": "updated",
                },
                approval,
                complete,
            ),
            False,
        ),
    )


def allow_all(_view: GuardInput) -> bool:
    """Baseline that allows the proposed action in every case."""
    return True


def revision_guard(view: GuardInput) -> bool:
    """Allow the action only when the record revision has not changed."""
    return view.observed_revision == view.current_revision


def _state_satisfies(
    state: Mapping[str, StateValue], conditions: Mapping[str, StateValue]
) -> bool:
    # Adapted from VP-Control's state_satisfies. See LICENSE and README.
    return all(state.get(key) == value for key, value in conditions.items())


def semantic_guard(view: GuardInput) -> bool:
    """Allow a one-time action when its preconditions hold and its effect is pending."""
    return (
        all(key in view.current_state for key in view.effect)
        and _state_satisfies(view.current_state, view.preconditions)
        and not _state_satisfies(view.current_state, view.effect)
    )


def evaluate(guard: Callable[[GuardInput], bool], cases: Iterable[Case]) -> Evaluation:
    """Run a guard on each view and compare its decision with the fixture's label."""
    decisions = []
    for case in cases:
        allowed = guard(case.view)
        if not isinstance(allowed, bool):
            raise TypeError(f"guard must return True or False for {case.case_id}")
        decisions.append(CaseResult(case.case_id, case.expected_commit, allowed))
    if not decisions:
        raise ValueError("at least one case is required")
    return Evaluation(
        cases=tuple(decisions),
        valid_cases=sum(row.expected_commit for row in decisions),
        invalid_cases=sum(not row.expected_commit for row in decisions),
        unsafe_commits=sum(
            row.allowed and not row.expected_commit for row in decisions
        ),
        unnecessary_blocks=sum(
            not row.allowed and row.expected_commit for row in decisions
        ),
        safe_completions=sum(row.allowed and row.expected_commit for row in decisions),
    )
