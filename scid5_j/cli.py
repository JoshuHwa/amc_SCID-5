"""Command-line front end.

    python -m scid5_j.cli --presentation "..."
    python -m scid5_j.cli --presentation-file case.txt --json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from .interview import ModuleJInterview
from .llm import DEFAULT_MODEL, OpenAIRater

DISCLAIMER = (
    "Research prototype — decision support only. Output is not a diagnosis "
    "and must be reviewed by a qualified clinician."
)


def _ask_human(question: str) -> str:
    """Put a probe to the interviewee on stdin."""
    print(f"\n[probe] {question}")
    try:
        return input("> ").strip()
    except EOFError:
        return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scid5_j",
        description="Administer SCID-5 Module J (adjustment disorder) with an LLM rater.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--presentation", help="Initial clinical description of the case.")
    source.add_argument("--presentation-file", help="File containing the initial description.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"OpenAI model (default: {DEFAULT_MODEL}).")
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON.")
    parser.add_argument(
        "--no-probes",
        action="store_true",
        help="Do not prompt for follow-up answers; undetermined criteria are treated as not met.",
    )
    args = parser.parse_args(argv)

    if args.presentation_file:
        with open(args.presentation_file, encoding="utf-8") as handle:
            presentation = handle.read()
    else:
        presentation = args.presentation

    try:
        rater = OpenAIRater(model=args.model)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    interview = ModuleJInterview(rater, ask_human=None if args.no_probes else _ask_human)
    result = interview.run(presentation)

    if args.json:
        print(json.dumps(dataclasses.asdict(result), ensure_ascii=False, indent=2))
    else:
        print("\n=== SCID-5 Module J ===")
        for line in result.summary_lines():
            print(line)
        print(f"\n{DISCLAIMER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
