"""Run the four-case smoke evaluation."""

import argparse
import json
from dataclasses import asdict

from . import (
    __version__,
    allow_all,
    evaluate,
    paired_cases,
    revision_guard,
    semantic_guard,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="agent-commit-evals", description=__doc__)
    parser.add_argument(
        "--json", action="store_true", help="Emit per-case decisions and counts."
    )
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)

    cases = paired_cases()
    results = {
        guard.__name__: evaluate(guard, cases)
        for guard in (allow_all, revision_guard, semantic_guard)
    }
    if args.json:
        print(
            json.dumps(
                {
                    "version": __version__,
                    "results": {
                        name: asdict(result) for name, result in results.items()
                    },
                },
                indent=2,
            )
        )
        return

    print(
        f"Agent Commit Evals {__version__} | two valid and two invalid synthetic cases"
    )
    print(
        f"{'Guard':<18}{'Unsafe commits':>16}{'Unnecessary blocks':>21}{'Safe completions':>19}"
    )
    for name, result in results.items():
        print(
            f"{name:<18}{result.unsafe_commits:>16}{result.unnecessary_blocks:>21}"
            f"{result.safe_completions:>19}"
        )


if __name__ == "__main__":
    main()
