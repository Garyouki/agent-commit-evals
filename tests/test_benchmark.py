import io
import json
import unittest
from contextlib import redirect_stdout

from agent_commit_evals import (
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
from agent_commit_evals.__main__ import main


class BenchmarkTests(unittest.TestCase):
    def test_pairs_hold_revisions_constant_and_change_one_contract_field(self):
        cases = paired_cases()
        self.assertEqual(len({case.case_id for case in cases}), 4)
        for valid, invalid in ((cases[0], cases[1]), (cases[2], cases[3])):
            with self.subTest(pair=valid.case_id):
                self.assertTrue(valid.expected_commit)
                self.assertFalse(invalid.expected_commit)
                self.assertEqual(
                    valid.view.observed_revision, invalid.view.observed_revision
                )
                self.assertEqual(
                    valid.view.current_revision, invalid.view.current_revision
                )
                self.assertNotEqual(
                    valid.view.observed_revision, valid.view.current_revision
                )
                self.assertEqual(valid.view.preconditions, invalid.view.preconditions)
                self.assertEqual(valid.view.effect, invalid.view.effect)
                self.assertEqual(
                    valid.view.current_state.keys(), invalid.view.current_state.keys()
                )
                self.assertEqual(
                    sum(
                        valid.view.current_state[key] != invalid.view.current_state[key]
                        for key in valid.view.current_state
                    ),
                    1,
                )

    def test_reference_counts_match_manually_labeled_cases(self):
        for guard, expected in (
            (allow_all, (2, 0, 2)),
            (claimed_revision_guard, (0, 2, 0)),
            (revision_guard, (0, 2, 0)),
            (semantic_guard, (0, 0, 2)),
        ):
            with self.subTest(guard=guard.__name__):
                result = evaluate(guard, paired_cases())
                self.assertEqual((result.valid_cases, result.invalid_cases), (2, 2))
                self.assertEqual(
                    (
                        result.unsafe_commits,
                        result.unnecessary_blocks,
                        result.safe_completions,
                    ),
                    expected,
                )

    def test_provenance_pair_differs_only_in_what_the_runtime_served(self):
        valid, invalid = token_provenance_cases()
        self.assertTrue(valid.expected_commit)
        self.assertFalse(invalid.expected_commit)
        for case in (valid, invalid):
            with self.subTest(case=case.case_id):
                self.assertEqual(case.view.claimed_revision, case.view.current_revision)
        self.assertEqual(valid.view.observed_revision, valid.view.current_revision)
        self.assertLess(invalid.view.observed_revision, invalid.view.current_revision)
        self.assertEqual(valid.view.preconditions, invalid.view.preconditions)
        self.assertEqual(valid.view.effect, invalid.view.effect)

    def test_trusting_the_claimed_revision_admits_the_unsafe_provenance_case(self):
        for guard, expected in (
            (allow_all, (3, 0, 3)),
            (claimed_revision_guard, (1, 2, 1)),
            (revision_guard, (0, 2, 1)),
            (semantic_guard, (0, 0, 3)),
        ):
            with self.subTest(guard=guard.__name__):
                result = evaluate(guard, all_cases())
                self.assertEqual((result.valid_cases, result.invalid_cases), (3, 3))
                self.assertEqual(
                    (
                        result.unsafe_commits,
                        result.unnecessary_blocks,
                        result.safe_completions,
                    ),
                    expected,
                )

    def test_claimed_revision_guard_blocks_without_a_claim(self):
        view = GuardInput(8, 8, {"published": False}, {}, {"published": True})
        self.assertIsNone(view.claimed_revision)
        self.assertFalse(claimed_revision_guard(view))

    def test_semantic_guard_blocks_when_required_state_is_missing(self):
        for state in ({"published": False}, {"approval": "approved"}):
            with self.subTest(state=state):
                view = GuardInput(
                    7, 8, state, {"approval": "approved"}, {"published": True}
                )
                self.assertFalse(semantic_guard(view))

    def test_guard_views_do_not_allow_modifying_fixture_state(self):
        view = paired_cases()[0].view
        with self.assertRaises(TypeError):
            view.current_state["published"] = True
        self.assertTrue(semantic_guard(view))

    def test_custom_guard_must_return_a_boolean(self):
        with self.assertRaisesRegex(TypeError, "guard must return True or False"):
            evaluate(lambda view: "block", paired_cases())

    def test_json_cli_reports_per_case_decisions_and_denominators(self):
        with redirect_stdout(io.StringIO()) as output:
            main(["--json"])
        report = json.loads(output.getvalue())
        self.assertEqual(report["version"], "0.2.0")
        evaluation = report["results"]["semantic_guard"]
        self.assertEqual(evaluation["valid_cases"], 3)
        self.assertEqual(evaluation["invalid_cases"], 3)
        self.assertEqual(len(evaluation["cases"]), 6)
        self.assertTrue(
            all(row["allowed"] == row["expected_commit"] for row in evaluation["cases"])
        )
