# Router + workflows: the two skill shapes

A skill is not always one `SKILL.md`. There are two shapes, and picking the
wrong one is a top cause of bloated, hard-to-trigger skills.

## Contents

- [The two shapes](#the-two-shapes)
- [Decision rule](#decision-rule)
- [Why progressive disclosure matters](#why-progressive-disclosure-matters)
- [Anatomy of a router SKILL.md](#anatomy-of-a-router-skillmd)
- [Anatomy of a workflow file](#anatomy-of-a-workflow-file)
- [The Evidence Contract pattern](#the-evidence-contract-pattern)
- [Common mistakes](#common-mistakes)

## The two shapes

### Shape A — single-file skill

One `SKILL.md` (plus optional `references/` and `scripts/`). The body *is* the
procedure. Use this when the skill does **one thing**, or a few tightly-related
things that share one workflow.

```
my-skill/
├── SKILL.md          # frontmatter + the whole procedure
├── references/       # heavy material loaded on demand
└── scripts/
```

### Shape B — router + workflows

A thin router `SKILL.md` that **indexes** named workflow files and tells the
agent to load only the one it needs. Use this when the skill spans **several
distinct capabilities** the user invokes separately.

```
my-skill/
├── SKILL.md              # router: routing rules + workflow index + evidence contract
├── workflows/
│   ├── workflow-a.md     # one self-contained procedure
│   ├── workflow-b.md
│   └── workflow-c.md
├── scripts/
└── assets/
```

This is the pattern behind `LLMQuant/skills` (18 category routers, each
indexing 1–10 workflows) and your own meta+companion families
(firefly / cancer-buddy / beacon are router-shaped in spirit).

## Decision rule

Pick **router + workflows** when *any* of these hold:

- The skill has **≥3 distinct user intents** that don't share one procedure
  ("score IV rank" vs "build a strategy" vs "simulate P&L").
- A single-file body would exceed ~400 lines and the sections are independently
  invoked (so progressive disclosure actually saves context).
- You expect the capability set to **grow** — adding a workflow file is cheaper
  and safer than editing a monolith.
- Different capabilities have **different guardrails or data needs**.

Otherwise, stay single-file. A router with one workflow is just indirection.

## Why progressive disclosure matters

The router frontmatter + body is loaded to decide *whether* the skill applies.
If the body is the entire 2000-line procedure, the model pays that cost on every
near-miss. A 40-line router that points to the right 120-line workflow means the
model reads ~160 lines instead of ~2000 — and reads the *relevant* 160. Context
economy is a correctness lever, not just a cost one: less irrelevant text in
context means fewer wrong turns.

## Anatomy of a router `SKILL.md`

Use `templates/SKILL_ROUTER_TEMPLATE.md`. The required parts:

1. **Frontmatter** — `description` is still "when to use", covering the whole
   category. Add `category:` for grouping. Do **not** summarize each workflow in
   the description (same shortcut failure as single-file skills).
2. **Routing Rules** — a numbered list ending with "open only the selected
   workflow". This is the instruction that makes progressive disclosure happen.
3. **Workflow Index** — a two-column table (user intent → workflow link). This
   is the single source of truth. The lint enforces: every file in `workflows/`
   appears here, and every linked file exists.
4. **Evidence Contract** — where ground truth comes from, the fallback for
   missing inputs, and what the agent must never fabricate. See below.
5. **Output Requirements** — the shared output shape across workflows.

## Anatomy of a workflow file

Use `templates/WORKFLOW_TEMPLATE.md`. Each workflow is narrow, repeatable, and
evidence-first. Fixed sections:

- **Use When** — the one task; tells the agent to bounce back to the router if
  the ask doesn't fit.
- **Inputs Needed** — required / optional / freshness / fallback.
- **Workflow** — numbered, deterministic steps.
- **Output Format** — numbered, so output is reproducible across runs.
- **Guardrails** — the lines you'd most regret omitting.

A reviewer should be able to answer, from the file alone: what question does
this answer? what inputs? in what order? what evidence must show? what on
missing data? what does the output look like?

## The Evidence Contract pattern

Borrowed from LLMQuant's "Data Contract", generalized. Every router (and ideally
every single-file skill that touches external facts) should declare:

- **Sources of record** — the API / DB / files / tools that supply ground truth.
  Prefer live retrieval over the model's memory.
- **Fallback** — if a required input is missing, name the exact missing input
  and continue only with retrieved or user-provided evidence.
- **Never fabricate** — the value types the model must not synthesize: quotes,
  prices, citations, lab values, dosages, holdings. A model guessing these is
  precisely the failure the contract exists to stop.

This is not finance-specific. A medical skill's contract forbids synthesizing
trial IDs or drug dosages and requires live database lookups; a research skill's
contract forbids inventing citations. Match the contract to the domain's
"things that are dangerous to guess".

## Common mistakes

- **Router with the procedure inlined.** If the router contains the steps, it's
  a single-file skill wearing a costume. Move steps into `workflows/`.
- **Workflow index out of sync.** A `workflows/foo.md` not listed in the index
  is invisible; an index row pointing to a missing file is a dead link. Lint
  flags both — keep them in sync.
- **Workflows that overlap.** Two workflows that handle the same intent force
  the router to guess. Make each intent map to exactly one workflow.
- **No evidence contract.** Without it, every workflow re-litigates "can I just
  make this up?" — and under pressure, the model will.
