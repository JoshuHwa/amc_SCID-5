# Module J decision tree

Adjustment disorder is a residual diagnosis: DSM-5 reaches it only after the
presentation has failed to fit a better-defined category. The engine mirrors
that ordering — screening first, then the J1–J5 chain, then the specifier.

```mermaid
flowchart TD
    A[Initial presentation] --> S{Screen: does the case<br/>clearly fit another<br/>DSM-5 category?}
    S -->|yes| X[Exit Module J<br/>report category + ICD-10 chapter]
    S -->|no| J1

    J1{"J1 — identifiable stressor,<br/>onset within 3 months"} -->|not met| N[Adjustment disorder<br/>criteria not met]
    J1 -->|met| J2
    J2{"J2 — disproportionate distress<br/>or functional impairment"} -->|not met| N
    J2 -->|met| J3
    J3{"J3 — not an exacerbation of a<br/>pre-existing disorder"} -->|not met| N
    J3 -->|met| J4
    J4{"J4 — not normal bereavement"} -->|not met| N
    J4 -->|met| J5
    J5{"J5 — resolves within 6 months<br/>after the stressor ends"} -->|not met| N
    J5 -->|met| D[Adjustment disorder]

    D --> SP[Specifier + ICD-10-CM code<br/>F43.20–F43.25]
```

## What happens at each node

The rater model is asked one criterion question against the full transcript and
must answer `yes`, `no`, or `unclear`.

```mermaid
sequenceDiagram
    participant E as Engine
    participant R as Rater (LLM)
    participant P as Interviewee

    E->>R: judge(transcript, criterion question)
    R-->>E: unclear
    E->>P: probe 1
    P-->>E: answer
    E->>P: probe 2
    P-->>E: answer
    Note over E: transcript now contains both answers
    E->>R: judge(transcript, same question)
    R-->>E: yes / no
```

Three properties fall out of this shape:

- **Probes are bounded.** Each criterion's probes are asked at most once, so a
  rater that never commits cannot loop.
- **Context accumulates.** A probe answered at J1 is still in the transcript
  when J5 is rated, which is how a single timeline statement can settle two
  different criteria.
- **Undetermined is not met.** A criterion still `unclear` after probing is
  recorded as not met, with that fact stated in the rationale. For a screening
  aid, missing a case is the safer error.
