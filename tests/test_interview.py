"""Decision-tree tests. No network, no SDK — the rater is scripted."""

import unittest

from scid5_j.coding import ADJUSTMENT_DISORDER_CODES
from scid5_j.interview import ModuleJInterview
from scid5_j.llm import Judgement


class ScriptedRater:
    """Rater that replays a fixed list of verdicts."""

    def __init__(self, verdicts, screen_result=None, specifier_result="with_anxiety"):
        self.verdicts = list(verdicts)
        self.screen_result = screen_result
        self.specifier_result = specifier_result
        self.judge_calls = []

    def judge(self, transcript, question):
        self.judge_calls.append((transcript, question))
        verdict = self.verdicts.pop(0) if self.verdicts else "no"
        return Judgement(verdict=verdict, rationale=f"scripted:{verdict}")

    def screen(self, transcript, categories):
        return self.screen_result

    def specifier(self, transcript, specifiers):
        return self.specifier_result


class ModuleJTests(unittest.TestCase):
    def test_all_criteria_met_yields_adjustment_disorder(self):
        rater = ScriptedRater(["yes"] * 5, specifier_result="with_depressed_mood")
        result = ModuleJInterview(rater).run("Conflict at work two months ago; insomnia since.")

        self.assertEqual(result.diagnosis, "adjustment_disorder")
        self.assertEqual(result.met_criteria, ["J1", "J2", "J3", "J4", "J5"])
        self.assertEqual(result.specifier, "with_depressed_mood")
        self.assertEqual(result.icd10_code, ADJUSTMENT_DISORDER_CODES["with_depressed_mood"])

    def test_failed_criterion_stops_the_interview(self):
        rater = ScriptedRater(["yes", "no"])
        result = ModuleJInterview(rater).run("Case description.")

        self.assertEqual(result.diagnosis, "no_diagnosis")
        self.assertEqual(result.stopped_at, "J2")
        # J3 onwards must not be evaluated once J2 fails.
        self.assertEqual(len(result.criteria), 2)
        self.assertEqual(len(rater.judge_calls), 2)

    def test_screening_exits_before_module_j(self):
        rater = ScriptedRater(["yes"] * 5, screen_result="depressive")
        result = ModuleJInterview(rater).run("Two years of persistent low mood, no stressor.")

        self.assertEqual(result.diagnosis, "other_dsm5_category")
        self.assertEqual(result.screened_out_as, "depressive")
        self.assertEqual(result.criteria, [])
        self.assertEqual(rater.judge_calls, [])

    def test_unclear_triggers_probes_then_re_rates(self):
        asked = []
        rater = ScriptedRater(["unclear", "yes", "yes", "yes", "yes", "yes"])
        interview = ModuleJInterview(rater, ask_human=lambda q: asked.append(q) or "3주 뒤부터였습니다.")
        result = interview.run("Something happened at work.")

        self.assertEqual(result.diagnosis, "adjustment_disorder")
        self.assertEqual(len(asked), 2)  # J1 has two probes
        self.assertIn("3주 뒤부터였습니다.", interview.transcript)
        # J1 was rated twice: once before probing, once after.
        self.assertEqual(rater.judge_calls[0][1], rater.judge_calls[1][1])

    def test_probe_answers_are_visible_to_later_criteria(self):
        rater = ScriptedRater(["unclear", "yes", "yes", "yes", "yes", "yes"])
        interview = ModuleJInterview(rater, ask_human=lambda q: "직장 상사와의 갈등이 있었습니다.")
        interview.run("Case description.")

        # The J2 rating (last call) must contain the J1 probe answer.
        last_transcript = rater.judge_calls[-1][0]
        self.assertIn("직장 상사와의 갈등이 있었습니다.", last_transcript)

    def test_persistent_unclear_is_treated_as_not_met(self):
        rater = ScriptedRater(["unclear", "unclear"])
        result = ModuleJInterview(rater, ask_human=lambda q: "잘 모르겠습니다.").run("Case.")

        self.assertEqual(result.diagnosis, "no_diagnosis")
        self.assertEqual(result.stopped_at, "J1")
        self.assertIn("Still undetermined", result.criteria[0].rationale)

    def test_verdict_validation(self):
        with self.assertRaises(ValueError):
            Judgement(verdict="maybe")


if __name__ == "__main__":
    unittest.main()
