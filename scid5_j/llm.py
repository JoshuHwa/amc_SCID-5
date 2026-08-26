"""Rater backends.

The interview engine never talks to a vendor SDK directly — it talks to the
`Rater` protocol. That is what lets the decision tree be unit-tested with a
scripted rater and no network access.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol

DEFAULT_MODEL = os.environ.get("SCID5_MODEL", "gpt-4o")

VERDICTS = ("yes", "no", "unclear")

SYSTEM_PROMPT = (
    "You are assisting a clinician who is administering SCID-5 Module J "
    "(adjustment disorder). You do not diagnose. You read the interview "
    "transcript and answer one criterion question at a time, strictly from "
    "what the transcript supports.\n"
    "Answer 'unclear' whenever the transcript does not settle the question — "
    "an 'unclear' triggers a follow-up question to the interviewee, which is "
    "the correct outcome for missing information. Never infer a timeline, a "
    "prior diagnosis, or a degree of impairment that was not stated."
)


@dataclass(frozen=True)
class Judgement:
    """A rater's answer about one criterion."""

    verdict: str  # one of VERDICTS
    rationale: str = ""
    evidence: str = ""  # quoted span from the transcript, if any

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise ValueError(f"verdict must be one of {VERDICTS}, got {self.verdict!r}")


class Rater(Protocol):
    """What the interview engine needs from a language model."""

    def judge(self, transcript: str, question: str) -> Judgement: ...

    def screen(self, transcript: str, categories: dict[str, str]) -> str | None:
        """Return the slug of a better-fitting DSM-5 category, or None."""
        ...

    def specifier(self, transcript: str, specifiers: dict[str, str]) -> str:
        """Return the slug of the DSM-5 specifier that best fits."""
        ...


class OpenAIRater:
    """Rater backed by an OpenAI chat model, constrained to JSON output."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None, temperature: float = 0.0):
        # Imported lazily so that the decision tree and its tests stay
        # importable without the SDK installed.
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "The openai package is required for OpenAIRater. "
                "Install it with: pip install -r requirements.txt"
            ) from exc

        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Export it or pass api_key=... "
                "(see .env.example)."
            )
        self._client = OpenAI(api_key=key)
        self._model = model
        self._temperature = temperature

    def _ask_json(self, user_prompt: str) -> dict:
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return json.loads(response.choices[0].message.content)

    def judge(self, transcript: str, question: str) -> Judgement:
        payload = self._ask_json(
            f"Interview transcript so far:\n---\n{transcript}\n---\n\n"
            f"Criterion question: {question}\n\n"
            'Reply as JSON: {"verdict": "yes" | "no" | "unclear", '
            '"rationale": "<one sentence>", "evidence": "<quote from the '
            'transcript, or empty string>"}'
        )
        verdict = str(payload.get("verdict", "unclear")).lower()
        if verdict not in VERDICTS:
            verdict = "unclear"
        return Judgement(
            verdict=verdict,
            rationale=str(payload.get("rationale", "")),
            evidence=str(payload.get("evidence", "")),
        )

    def screen(self, transcript: str, categories: dict[str, str]) -> str | None:
        listing = "\n".join(f"- {slug}: {name}" for slug, name in categories.items())
        payload = self._ask_json(
            f"Interview transcript so far:\n---\n{transcript}\n---\n\n"
            "Adjustment disorder is a residual category: it is only considered "
            "when the presentation does not meet criteria for another DSM-5 "
            "disorder. Does the transcript clearly indicate one of these "
            f"categories instead?\n{listing}\n\n"
            'Reply as JSON: {"category": "<slug from the list, or null>", '
            '"rationale": "<one sentence>"}. Use null unless the transcript '
            "clearly supports that category."
        )
        category = payload.get("category")
        if isinstance(category, str) and category in categories:
            return category
        return None

    def specifier(self, transcript: str, specifiers: dict[str, str]) -> str:
        listing = "\n".join(f"- {slug}: {desc}" for slug, desc in specifiers.items())
        payload = self._ask_json(
            f"Interview transcript so far:\n---\n{transcript}\n---\n\n"
            "Adjustment disorder has been established. Which specifier fits "
            f"the predominant symptoms?\n{listing}\n\n"
            'Reply as JSON: {"specifier": "<slug from the list>", '
            '"rationale": "<one sentence>"}'
        )
        specifier = payload.get("specifier")
        if isinstance(specifier, str) and specifier in specifiers:
            return specifier
        return "unspecified"
