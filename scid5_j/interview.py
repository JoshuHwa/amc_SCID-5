"""The Module J decision-tree engine.

Design notes
------------
* The transcript grows monotonically. Every rater call sees everything said so
  far, so a probe answered at J1 is still available when J5 is evaluated.
* A criterion is only ruled on by the rater. When the rater says "unclear",
  the engine puts the criterion's probes to the interviewee and re-rates with
  the enlarged transcript. Probes are asked at most once per criterion, so a
  rater that never commits cannot loop forever.
* Screening runs first: adjustment disorder is a residual category, so a
  presentation that clearly belongs to another DSM-5 chapter exits before
  J1 is ever evaluated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .coding import (
    DSM5_CATEGORIES,
    icd10_chapter_for_category,
    icd10_for_specifier,
)
from .criteria import MODULE_J, SPECIFIERS, Criterion
from .llm import Judgement, Rater

AskHuman = Callable[[str], str]


@dataclass
class CriterionResult:
    """Outcome for a single criterion."""

    id: str
    summary: str
    met: bool
    rationale: str
    evidence: str = ""
    probes_asked: list[str] = field(default_factory=list)


@dataclass
class InterviewResult:
    """Outcome of one Module J administration."""

    diagnosis: str  # "adjustment_disorder", "other_dsm5_category", or "no_diagnosis"
    criteria: list[CriterionResult] = field(default_factory=list)
    specifier: str | None = None
    icd10_code: str | None = None
    screened_out_as: str | None = None
    stopped_at: str | None = None
    transcript: str = ""

    @property
    def met_criteria(self) -> list[str]:
        return [c.id for c in self.criteria if c.met]

    def summary_lines(self) -> list[str]:
        """Human-readable report, one line per element."""
        lines: list[str] = []
        if self.diagnosis == "other_dsm5_category":
            name = DSM5_CATEGORIES.get(self.screened_out_as or "", self.screened_out_as or "")
            lines.append(f"Screened out of Module J: presentation fits {name}.")
            lines.append(f"ICD-10-CM chapter: {self.icd10_code}")
            return lines

        for c in self.criteria:
            mark = "met" if c.met else "not met"
            lines.append(f"  {c.id} [{mark}] {c.summary}")
            if c.rationale:
                lines.append(f"       rationale: {c.rationale}")
        if self.diagnosis == "adjustment_disorder":
            lines.append("")
            lines.append(f"Diagnosis: Adjustment disorder, {self.specifier}")
            lines.append(f"ICD-10-CM: {self.icd10_code}")
        else:
            lines.append("")
            lines.append(f"Diagnosis: criteria for adjustment disorder not met (stopped at {self.stopped_at}).")
        return lines


class ModuleJInterview:
    """Administers SCID-5 Module J against a rater and an interviewee."""

    def __init__(self, rater: Rater, ask_human: AskHuman | None = None):
        self._rater = rater
        self._ask_human = ask_human or (lambda q: "")
        self._transcript_parts: list[str] = []

    @property
    def transcript(self) -> str:
        return "\n".join(self._transcript_parts)

    def _record(self, speaker: str, text: str) -> None:
        self._transcript_parts.append(f"{speaker}: {text}")

    def _probe(self, criterion: Criterion) -> list[str]:
        """Put the criterion's probes to the interviewee, recording answers."""
        asked: list[str] = []
        for probe in criterion.probes:
            answer = self._ask_human(probe)
            self._record("Interviewer", probe)
            self._record("Interviewee", answer)
            asked.append(probe)
        return asked

    def _evaluate(self, criterion: Criterion) -> CriterionResult:
        judgement: Judgement = self._rater.judge(self.transcript, criterion.judgement_prompt)
        probes_asked: list[str] = []

        if judgement.verdict == "unclear" and criterion.probes:
            probes_asked = self._probe(criterion)
            judgement = self._rater.judge(self.transcript, criterion.judgement_prompt)

        # A criterion that is still unclear after probing is treated as not met.
        # Under-diagnosing is the safer failure for a screening aid.
        met = judgement.verdict == "yes"
        rationale = judgement.rationale or (criterion.rule_out if not met else "")
        if judgement.verdict == "unclear":
            rationale = f"Still undetermined after probing; treated as not met. {rationale}".strip()

        return CriterionResult(
            id=criterion.id,
            summary=criterion.summary,
            met=met,
            rationale=rationale,
            evidence=judgement.evidence,
            probes_asked=probes_asked,
        )

    def run(self, presentation: str) -> InterviewResult:
        """Administer Module J starting from an initial clinical description."""
        self._record("Interviewee", presentation.strip())

        screened = self._rater.screen(self.transcript, DSM5_CATEGORIES)
        if screened:
            return InterviewResult(
                diagnosis="other_dsm5_category",
                screened_out_as=screened,
                icd10_code=icd10_chapter_for_category(screened),
                transcript=self.transcript,
            )

        results: list[CriterionResult] = []
        for criterion in MODULE_J:
            result = self._evaluate(criterion)
            results.append(result)
            if not result.met:
                return InterviewResult(
                    diagnosis="no_diagnosis",
                    criteria=results,
                    stopped_at=criterion.id,
                    transcript=self.transcript,
                )

        specifier = self._rater.specifier(self.transcript, SPECIFIERS)
        return InterviewResult(
            diagnosis="adjustment_disorder",
            criteria=results,
            specifier=specifier,
            icd10_code=icd10_for_specifier(specifier),
            transcript=self.transcript,
        )
