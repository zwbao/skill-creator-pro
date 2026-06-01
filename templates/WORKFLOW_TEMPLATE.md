---
name: <Human Readable Workflow Name>
description: <One sentence — the single task this workflow performs.>
pack: <optional grouping slug>
---

# <Workflow Name>

## Use When

Use this workflow when the user asks for <the one narrow task>. If the request
is broader or different, return to the router and pick another workflow — do
not stretch this one to cover adjacent cases.

## Inputs Needed

Required:
- <input + why it is needed>

Optional:
- <input + how it changes the output>

Freshness:
- <what dates / as-of stamps / versions must be reported with the result>

Fallback:
- If a required input is unavailable, name the exact missing input and continue
  only with retrieved or user-provided evidence. Do not fill gaps from memory.

## Workflow

1. Confirm inputs, scope, and the output target.
2. Retrieve / compute the required evidence.
3. Check coverage, dates, and missing fields before interpreting.
4. Separate retrieved evidence from your interpretation.
5. Produce the output in the format below.

## Output Format

1. **Answer** — <the headline result>
2. **Evidence** — <table or list with sources + dates>
3. **Scenario / Sensitivity** — <if applicable>
4. **Risks / Caveats**
5. **Data Used**

## Guardrails

- Do not invent missing values; name them as gaps instead.
- Do not present model output as if it were retrieved data.
- <one domain-specific guardrail — the line you'd most regret omitting>
