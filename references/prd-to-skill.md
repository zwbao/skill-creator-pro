# PRD → top-tier skill

The operational procedure for turning a PRD (product requirements doc, spec, or
even a loose description) into a skill that meets the
[`top-skills-playbook.md`](top-skills-playbook.md) quality bar. This is the
path invoked when the user says "here's my PRD, build the skill".

## Contents

- [Step 0 — ingest & classify](#step-0--ingest--classify)
- [Step 1 — derive the evals from the PRD](#step-1--derive-the-evals-from-the-prd)
- [Step 2 — RED baseline](#step-2--red-baseline)
- [Step 3 — scaffold the right shape](#step-3--scaffold-the-right-shape)
- [Step 4 — GREEN against the playbook](#step-4--green-against-the-playbook)
- [Step 5 — verify, lint, optimize, package](#step-5--verify-lint-optimize-package)
- [The PRD intake template](#the-prd-intake-template)

## Step 0 — ingest & classify

Read the whole PRD first, then extract a structured intake (template at the
bottom). The two classifications drive everything downstream:

1. **School** (capability vs discipline) — see the playbook's two-schools
   table. "Extract/convert/generate/analyze X" → capability. "Always/never,
   enforce, stop the agent from Z" → discipline. This decides body structure,
   trigger style, and verification method.
2. **Shape** (single-file vs router+workflows) — ≥3 distinct user intents in
   the PRD → router. See `router-and-workflows.md`.

If the PRD is missing any of: the real user phrasings that should trigger it,
the concrete input→output, the "things dangerous to guess" (for the Evidence
Contract), or the acceptance criteria — **ask the user before building** (use
`AskUserQuestion`). A PRD without trigger phrasings produces an undiscoverable
skill; that gap is worth one round-trip.

## Step 1 — derive the evals from the PRD

Eval-first is non-negotiable: write the tests before the docs, so the skill
closes a *demonstrated* gap, not an imagined one. The PRD's acceptance criteria
ARE your assertions.

- Turn each PRD acceptance criterion / "must do X" into ≥1 objectively-checkable
  assertion. Aim for **≥3 eval scenarios**.
- Eval record shape: `{skills, query, files, expected_behavior: [assertions]}`.
  Assertions must be verifiable with descriptive names — don't assert on
  subjective style.
- Store under `evals/evals.json`. See `evals-and-benchmark.md`.

If the PRD has no acceptance criteria, that's a red flag — extract implicit ones
("the skill should X") and confirm them with the user.

## Step 2 — RED baseline

Run the PRD's hardest scenario with a subagent **without** the skill. Capture
its failures and rationalizations verbatim — these become exactly what the
SKILL.md must counter. For discipline skills, build a multi-pressure scenario
(time + sunk cost + authority); a single-pressure or academic scenario is too
weak. See `tdd-for-skills.md`.

If the baseline succeeds effortlessly, the skill may be unnecessary — tell the
user rather than building a skill that earns nothing.

## Step 3 — scaffold the right shape

```bash
python scripts/init_skill.py <name> --dest ~/.claude/skills            # capability/single
python scripts/init_skill.py <name> --dest ~/.claude/skills --router   # ≥3 intents
```

Name from the PRD: lowercase-kebab, ideally gerund (`processing-invoices`),
never `helper/utils/tools`.

## Step 4 — GREEN against the playbook

Fill SKILL.md addressing the RED failures, applying the playbook by school:

**Capability school** → Overview + Core Principle → Quick-Reference routing
table → one section per capability with ✅/❌ pairs + inline `CRITICAL:` →
mandatory "assume failure" QA loop → Common Mistakes → Dependencies. Push
deterministic/repeated logic into `scripts/` (black-box, `--help`-documented);
push heavy API surface into one-level-deep `references/*.md` (TOC if >100 lines).

**Discipline school** → Overview + bolded Core Principle → When to Use + When
NOT → the one Iron Law in a fenced block → phased workflow with gates →
rationalization table (`Excuse | Reality`, seeded from RED) → red-flags STOP
list. Bright-line absolute language; almost no code.

**Both** → write the description as `<what> . Use when <triggers + keywords> .`
with a `Do NOT` clause; add an Evidence Contract if the skill touches external
facts (sources / fallback / never-fabricate).

## Step 5 — verify, lint, optimize, package

Run the rest of the lifecycle to completion — a PRD asks for a *finished*
skill, so do not stop at "drafted":

1. **Re-run the evals** (with-skill vs baseline, in parallel) → benchmark →
   confirm every PRD assertion passes. Close new rationalizations the run
   surfaces.
2. **LINT**: `lint_skill.py <name>` → fix all errors, triage warns.
3. **OPTIMIZE-DESC** (if triggering accuracy matters): 20-query set, 60/40
   train/test, pick by test score.
4. **BUMP**: `bump_version.py <name> --type minor -m "..."` → CHANGELOG.
5. **PACKAGE**: deploy to `~/.claude/skills/`, or emit multi-platform manifests
   for `npx skills add` (see `shipping-a-skill-library.md`).
6. **Report against the PRD**: list each PRD requirement and whether the shipped
   skill meets it, with the eval evidence. Be honest about anything deferred.

## The PRD intake template

Extract this from the PRD before building (ask the user to fill gaps):

```yaml
skill_name:            # lowercase-kebab, gerund preferred
one_line_purpose:      # what it does
school:                # capability | discipline
shape:                 # single-file | router
trigger_phrasings:     # 3+ real things a user would type (verbatim)
near_miss_skills:      # skills it must NOT steal triggers from → Do NOT clause
inputs:                # concrete shape, file types
outputs:               # concrete shape, format, template if fixed
dangerous_to_guess:    # values the agent must never fabricate (→ Evidence Contract)
acceptance_criteria:   # each becomes ≥1 eval assertion
target_models:         # which of Haiku/Sonnet/Opus it must work on
distribution:          # local ~/.claude/skills | multi-platform library
```

A filled intake + the playbook is enough to drive Steps 1–5 end to end.
