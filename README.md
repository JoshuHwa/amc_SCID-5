# SCID-5 Module J Agent

**An LLM-administered structured psychiatric interview for adjustment disorder — DSM-5 criteria J1–J5, with a human in the loop.**

> ⚠️ **Research prototype. Not a medical device, not for clinical use.** The output is a structured summary of how a language model rated an interview transcript against published criteria. It is not a diagnosis, and it must not be used to make care decisions.

Structured clinical interviews such as the SCID-5 are decision trees: a fixed sequence of criteria, each of which is met or not met, with an explicit stopping rule the moment one fails. That structure is exactly what a language model tends to abandon — ask GPT for a diagnosis and it will produce a fluent paragraph that skipped three criteria. This project puts the tree back in charge: **the engine owns the control flow, and the model only ever answers one criterion question at a time.**

Originally built for the **AI psychiatrist project at Ajou University Medical Center (AMC)** in 2024, and rewritten in 2026 (see [What changed](#what-changed-in-the-rewrite)).

---

## The idea

```
presentation ──▶ screening ──▶ J1 ──▶ J2 ──▶ J3 ──▶ J4 ──▶ J5 ──▶ specifier ──▶ F43.2x
                     │          │      │      │      │      │
                     └── other  └──────┴──────┴──────┴──────┴── any failure stops here
                         DSM-5
                         category
```

Adjustment disorder is a *residual* category — DSM-5 reaches it only after better-defined disorders have been excluded. So the engine screens first, walks J1 through J5 in order, and stops at the first unmet criterion. Full diagram, including the probe loop: [docs/decision-tree.md](docs/decision-tree.md).

**The interesting part is what happens on "unclear."** The rater model answers each criterion with `yes`, `no`, or `unclear`, and it is instructed to prefer `unclear` whenever the transcript does not settle the question. An `unclear` is not a failure — it is the trigger that puts the criterion's follow-up probes to the actual interviewee:

```
[probe] 무슨 일이 있었는지 말씀해 주시겠습니까?
    > 직장에서 상사와 크게 부딪히는 일이 있었습니다.
[probe] 그 일이 있고 나서 얼마 뒤에 증상이 처음 시작되었습니까?
    > 한 2~3주 뒤부터 잠을 못 자기 시작했습니다.
```

The answers go into the transcript, the same criterion is re-rated with the enlarged transcript, and the interview moves on. This is what keeps the model from filling gaps by inference — a missing timeline becomes a question to a human rather than a plausible guess.

Three design rules follow from that:

| Rule | Why |
|---|---|
| Probes are asked at most once per criterion | A rater that never commits cannot loop forever |
| The transcript is append-only and shared across criteria | A timeline given at J1 is still available when J5 is rated |
| Still `unclear` after probing ⇒ **not met** | For a screening aid, under-detection is the safer failure |

## Quickstart

See the decision tree run without an API key or network:

```bash
git clone https://github.com/sehyeony0518/scid5-module-j-agent.git
cd scid5-module-j-agent
python examples/demo_offline.py
```

```
=== SCID-5 Module J ===
  J1 [met] Identifiable stressor with symptom onset within 3 months
  J2 [met] Marked distress out of proportion, or impairment in functioning
  J3 [met] Not merely an exacerbation of a pre-existing mental disorder
  J4 [met] Not better explained by normal bereavement
  J5 [met] Symptoms do not persist beyond 6 months after the stressor ends

Diagnosis: Adjustment disorder, with_mixed_anxiety_and_depressed_mood
ICD-10-CM: F43.23
```

With a real model:

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...          # never commit this
python -m scid5_j.cli --presentation "환자는 두 달 전 직장에서의 갈등 이후 불면과 집중력 저하를 호소합니다."
python -m scid5_j.cli --presentation-file case.txt --json      # machine-readable result
python -m scid5_j.cli --presentation-file case.txt --no-probes # batch mode, no human in the loop
```

## Using it as a library

The engine depends on a `Rater` protocol, not on any vendor SDK — swap in another model, or a scripted rater for testing, without touching the decision tree:

```python
from scid5_j import ModuleJInterview, OpenAIRater

interview = ModuleJInterview(OpenAIRater(model="gpt-4o"), ask_human=input)
result = interview.run(presentation)

result.diagnosis     # 'adjustment_disorder' | 'no_diagnosis' | 'other_dsm5_category'
result.met_criteria  # ['J1', 'J2', 'J3', 'J4', 'J5']
result.icd10_code    # 'F43.23'
result.criteria[0].rationale   # why the rater ruled the way it did
result.transcript    # everything said, including probe answers
```

Every result carries the rationale and the quoted transcript evidence behind each rating, so a clinician can check the chain rather than the conclusion.

## Tests

```bash
python -m unittest discover -s tests -t .
```

Seven tests cover the decision tree with a scripted rater — no network, no API key, no `openai` install needed (the SDK is imported lazily). They pin the behaviour that matters: the stopping rule fires at the first unmet criterion and skips the rest, screening exits before J1 is ever rated, `unclear` triggers probes and re-rates, probe answers stay visible to later criteria, and a persistently `unclear` criterion is recorded as not met.

## Project layout

```
scid5_j/
├── criteria.py     J1–J5 definitions, probes, DSM-5 specifiers
├── coding.py       DSM-5 categories, ICD-10-CM mapping (F43.20–F43.25)
├── llm.py          Rater protocol + OpenAI implementation (JSON-constrained)
├── interview.py    Decision-tree engine
└── cli.py
tests/              Decision-tree tests with a scripted rater
examples/           Offline demo
docs/               Decision-tree diagrams
legacy/SCID_J.py    The original 2024 script, kept for provenance
```

## What changed in the rewrite

The 2024 version ([`legacy/SCID_J.py`](legacy/SCID_J.py)) is kept in the repository because the diff is the interesting part. It was a 327-line script that worked as a proof of concept and broke in instructive ways:

| v1 (2024) | v2 (2026) |
|---|---|
| `openai.ChatCompletion` + `openai.api_key` — removed in the 1.0 SDK, so the script no longer runs | `client.chat.completions.create` via a `Rater` protocol; the engine is vendor-agnostic |
| API key read from `api_key.txt` next to the source | `OPENAI_API_KEY` from the environment; both `api_key.txt` and `.env` are gitignored |
| Screening compared free-text model output against a dict of Korean category names with `in` — **it could never match**, so every case fell through to J1 | The model must return a slug from a closed vocabulary, which is validated before use |
| Verdicts parsed by substring (`"예" in answer`), with a keyword fallback that read words like "스트레스" as a yes | JSON-constrained `yes`/`no`/`unclear` with rationale and quoted evidence |
| Each criterion asked in isolation from a static `user_input`; probe answers were never fed back to the model | Append-only transcript passed to every rating call |
| `follow_up = self.ask_patient(additional_question)` — the interviewee's own answer was echoed back at them as the next question, in three separate branches | Probes come from the criterion definition; answers are recorded, not re-asked |
| J4 set "not bereavement" to **true** when the interviewee confirmed a recent death — inverted | J4 asks the criterion as DSM-5 states it, and the probe wording matches the direction of the answer |
| No tests, no dependency manifest, hardcoded case at the bottom of the file | 7 unit tests, `requirements.txt`, CLI with file/JSON/batch modes |

## Scope and limitations

- **One module.** Module J only. The screening step names another DSM-5 category when the case clearly belongs elsewhere, but it does not administer that module.
- **The rater is a language model.** It has not been validated against clinician ratings; agreement with trained raters is unmeasured, and that measurement is the prerequisite for any claim of usefulness.
- **No patient data.** This repository contains no clinical data, and none was used to build it. The example case is fabricated.
- **Instrument copyright.** SCID-5 is published by American Psychiatric Association Publishing and is a licensed instrument. No verbatim item text is reproduced here — `criteria.py` holds condensed paraphrases of the DSM-5 criteria for the purpose of implementing the decision logic. Administering the actual SCID-5 requires the licensed materials and appropriate training.

## Author

**Se-Hyeon Hwang** — Embedded Software Lab, Ajou University
Built for the AI psychiatrist project at Ajou University Medical Center. Published for portfolio and reference purposes; contact the author before reuse.
