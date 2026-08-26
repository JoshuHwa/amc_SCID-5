"""SCID-5 Module J (Adjustment Disorder) criteria.

The wording below is a condensed paraphrase of the DSM-5 criteria for
adjustment disorder as operationalised in SCID-5 Module J. The SCID-5
instrument itself is copyrighted by American Psychiatric Association
Publishing; no verbatim item text is reproduced here.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Criterion:
    """One node of the Module J decision tree.

    Attributes:
        id: Criterion identifier (J1-J5).
        summary: What the criterion asserts, in clinical shorthand.
        judgement_prompt: Question the rater model answers about the transcript.
        probes: Follow-up questions put to the interviewee when the rater
            model cannot decide from the material collected so far.
        rule_out: Message shown when the criterion is not met, explaining why
            adjustment disorder is ruled out at this node.
    """

    id: str
    summary: str
    judgement_prompt: str
    probes: tuple[str, ...] = field(default_factory=tuple)
    rule_out: str = ""


MODULE_J: tuple[Criterion, ...] = (
    Criterion(
        id="J1",
        summary="Identifiable stressor with symptom onset within 3 months",
        judgement_prompt=(
            "Is there an identifiable stressor, and did the emotional or "
            "behavioural symptoms begin within 3 months of its onset?"
        ),
        probes=(
            "무슨 일이 있었는지 말씀해 주시겠습니까?",  # What happened?
            "그 일이 있고 나서 얼마 뒤에 증상이 처음 시작되었습니까?",  # How long after the stressor did symptoms start?
        ),
        rule_out="No identifiable stressor, or onset outside the 3-month window.",
    ),
    Criterion(
        id="J2",
        summary="Marked distress out of proportion, or impairment in functioning",
        judgement_prompt=(
            "Do the symptoms cause distress that is out of proportion to the "
            "severity of the stressor, or significant impairment in social, "
            "occupational, or other important areas of functioning?"
        ),
        probes=(
            "그 증상이 생활에 어떤 영향을 주었습니까?",  # How did the symptoms affect your life?
            "다른 사람과의 관계, 직장이나 학업, 가정 생활에 어떤 영향이 있었습니까?",  # Effects on relationships, work/school, home?
        ),
        rule_out="Distress is proportionate and functioning is not impaired.",
    ),
    Criterion(
        id="J3",
        summary="Not merely an exacerbation of a pre-existing mental disorder",
        judgement_prompt=(
            "Is the disturbance something other than an exacerbation of a "
            "pre-existing mental disorder?"
        ),
        probes=(
            "이런 증상이 그 일이 있기 전에도 있었습니까?",  # Were these symptoms present before the stressor?
            "전에 정신건강 문제로 진단이나 치료를 받은 적이 있습니까?",  # Any prior diagnosis or treatment?
        ),
        rule_out="The presentation is an exacerbation of a pre-existing disorder.",
    ),
    Criterion(
        id="J4",
        summary="Not better explained by normal bereavement",
        judgement_prompt=(
            "Is the reaction something other than normal bereavement — that is, "
            "NOT adequately explained by an expected grief response to a death?"
        ),
        probes=(
            "최근에 가까운 사람을 잃은 일이 있었습니까?",  # Recent loss of someone close?
            "그 반응이 주변에서 보기에 흔히 예상되는 정도를 넘어섰다고 느끼십니까?",  # Beyond an expected grief reaction?
        ),
        rule_out="The reaction is accounted for by normal bereavement.",
    ),
    Criterion(
        id="J5",
        summary="Symptoms do not persist beyond 6 months after the stressor ends",
        judgement_prompt=(
            "Once the stressor (or its consequences) had ended, did the symptoms "
            "resolve within 6 months?"
        ),
        probes=(
            "그 일이 정리된 뒤에 증상이 얼마나 오래 지속되었습니까?",  # How long did symptoms last after the stressor ended?
        ),
        rule_out="Symptoms persisted for more than 6 months after the stressor ended.",
    ),
)

CRITERIA_BY_ID = {c.id: c for c in MODULE_J}

# DSM-5 specifiers for adjustment disorder, with the clinical description that
# distinguishes them.
SPECIFIERS: dict[str, str] = {
    "with_depressed_mood": "Low mood, tearfulness, or feelings of hopelessness predominate.",
    "with_anxiety": "Nervousness, worry, jitteriness, or separation anxiety predominates.",
    "with_mixed_anxiety_and_depressed_mood": "A combination of depression and anxiety predominates.",
    "with_disturbance_of_conduct": "Disturbance of conduct predominates.",
    "with_mixed_disturbance_of_emotions_and_conduct": "Both emotional symptoms and disturbance of conduct are present.",
    "unspecified": "Maladaptive reactions that do not fit one of the specific subtypes.",
}
