# Evals and benchmark

The eval pipeline turns "I think this skill works" into "this skill beats
baseline on 4/5 test cases by X%". It's the infrastructure that lets you
iterate with real feedback instead of hunches.

## When to use

- Full track skills (discipline, high-stakes, multi-use-case).
- Any skill where you want objective proof it helps before shipping.
- Skills shared with others — the benchmark is the receipt.

Skip for lightweight personal skills where eyeballing is enough.

## Workspace layout

```
<skill-name>-workspace/
├── iteration-1/
│   ├── eval-0-name/
│   │   ├── eval_metadata.json
│   │   ├── with_skill/
│   │   │   ├── outputs/          # files the subagent produced
│   │   │   ├── transcript.md     # the subagent's verbatim trace
│   │   │   ├── timing.json       # {total_tokens, duration_ms}
│   │   │   └── grading.json      # assertion pass/fail results
│   │   └── without_skill/        # baseline (or old_skill/ for existing skills)
│   ├── eval-1-name/
│   ├── ...
│   ├── benchmark.json
│   ├── benchmark.md
│   └── feedback.json             # populated after user review
└── iteration-2/
    └── ...
```

Sibling to the skill directory. Name eval directories after what they test,
not `eval-0` — `pdf-scanned-cjk/` is more useful than `eval-0/`.

## evals.json schema

```json
{
  "skill_name": "pdf-to-markdown",
  "evals": [
    {
      "id": 0,
      "eval_name": "scanned-cjk-legal",
      "prompt": "ok so my boss sent me this pdf of a lease...",
      "expected_output": "Markdown file with the rent amount and renewal clause extracted",
      "files": ["fixtures/lease-scan.pdf"],
      "assertions": [
        {
          "text": "output contains rent amount in RMB",
          "type": "regex",
          "pattern": "¥\\s*\\d+"
        },
        {
          "text": "output preserves Chinese characters",
          "type": "regex",
          "pattern": "[\u4e00-\u9fff]"
        },
        {
          "text": "markdown structure has H2 sections",
          "type": "regex",
          "pattern": "^##\\s"
        }
      ]
    }
  ]
}
```

**Rules**:
- Write prompts first, assertions later — assertions only make sense after
  you know what "good output" looks like.
- Assertion `text` shows in the viewer; make it descriptive so a glance tells
  you what each check measures.
- Use regex for structural checks, file existence for output-file checks.
  Avoid LLM-as-judge assertions unless the skill is inherently subjective.

## Running evals

Dispatch **with-skill** and **baseline** subagents in the same turn so they
complete around the same time and share load. Save outputs to each run's
`outputs/` directory. Record `timing.json` from the subagent notification as
it completes — the number is only available at that moment.

## benchmark.json

After grading, aggregate:

```json
{
  "skill_name": "pdf-to-markdown",
  "iteration": 1,
  "configurations": [
    {
      "name": "with_skill",
      "pass_rate": {"mean": 0.87, "stddev": 0.05},
      "duration_seconds": {"mean": 23.3, "stddev": 3.1},
      "total_tokens": {"mean": 84852, "stddev": 2100}
    },
    {
      "name": "without_skill",
      "pass_rate": {"mean": 0.44, "stddev": 0.15},
      "duration_seconds": {"mean": 41.0, "stddev": 12.8},
      "total_tokens": {"mean": 102340, "stddev": 18500}
    }
  ],
  "per_eval": [...]
}
```

## Reading the numbers

- **Pass rate delta < 10%**: skill isn't pulling its weight, or assertions
  aren't discriminating. Check for always-pass assertions (remove them) or
  re-scope the skill.
- **Time / tokens with skill > baseline**: skill is making the model do more
  work. Sometimes right (more thoroughness), sometimes wrong (telling model
  to do things it was already doing). Read transcripts.
- **High variance in with_skill**: skill is ambiguous; model interprets
  differently each run. Add concrete examples or tighten wording.

## Grading

A grader subagent reads outputs and emits `grading.json`:

```json
{
  "eval_id": 0,
  "config": "with_skill",
  "expectations": [
    {"text": "output contains rent amount in RMB", "passed": true, "evidence": "line 42: ¥5000"},
    {"text": "output preserves Chinese characters", "passed": true, "evidence": "section headers in 中文"},
    {"text": "markdown structure has H2 sections", "passed": false, "evidence": "only one H1, no H2"}
  ]
}
```

**Exact field names matter** — the eval-viewer depends on `text`, `passed`,
`evidence`. Scripts that grade programmatically are faster and more reliable
than model-graded assertions where possible.

## Review

Open the outputs side by side — the with-skill rendering next to the baseline
rendering, with the graded assertions and timing data visible. A minimal
static HTML viewer works; a live server is overkill.

For iteration 2+, also expose the previous iteration's outputs as a
"previous output" panel so you can see whether the change actually helped
the cases the user flagged.

Save feedback as `feedback.json` next to the iteration directory. An empty
feedback entry for an eval means the user was fine with it; don't regress
those in the next pass.

## Feedback → iteration

Read `feedback.json`, focus improvements on evals with specific complaints.
Empty feedback = user was fine with the output. Don't over-improve what's
working.
