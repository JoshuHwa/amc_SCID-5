"""Run Module J end to end with a scripted rater — no API key, no network.

    python examples/demo_offline.py

Useful for seeing the decision tree's behaviour and output format before
wiring up a real model.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scid5_j.interview import ModuleJInterview  # noqa: E402
from scid5_j.llm import Judgement  # noqa: E402

PRESENTATION = (
    "환자는 두 달 전 직장에서 상사와의 갈등을 겪은 뒤 집중력 저하와 불면이 시작되었다고 "
    "보고합니다. 이전에 정신과 진단을 받은 적은 없으며, 최근 가족 관계에서도 어려움이 "
    "있다고 합니다."
)

# Verdicts a rater might return for J1..J5. J1 comes back 'unclear' first,
# which is what triggers the follow-up probes.
SCRIPT = ["unclear", "yes", "yes", "yes", "yes", "yes"]

PROBE_ANSWERS = {
    "무슨 일이 있었는지 말씀해 주시겠습니까?": "직장에서 상사와 크게 부딪히는 일이 있었습니다.",
    "그 일이 있고 나서 얼마 뒤에 증상이 처음 시작되었습니까?": "한 2~3주 뒤부터 잠을 못 자기 시작했습니다.",
}


class ScriptedRater:
    def __init__(self, verdicts):
        self.verdicts = list(verdicts)

    def judge(self, transcript, question):
        verdict = self.verdicts.pop(0) if self.verdicts else "no"
        return Judgement(verdict=verdict, rationale=f"(scripted rater returned {verdict!r})")

    def screen(self, transcript, categories):
        return None

    def specifier(self, transcript, specifiers):
        return "with_mixed_anxiety_and_depressed_mood"


def main() -> None:
    def ask(question: str) -> str:
        answer = PROBE_ANSWERS.get(question, "잘 모르겠습니다.")
        print(f"[probe] {question}\n    > {answer}")
        return answer

    result = ModuleJInterview(ScriptedRater(SCRIPT), ask_human=ask).run(PRESENTATION)

    print("\n=== SCID-5 Module J ===")
    for line in result.summary_lines():
        print(line)


if __name__ == "__main__":
    main()
