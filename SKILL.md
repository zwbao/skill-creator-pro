---
name: skill-creator-pro
description: Use when creating new skills, iterating on existing skills, auditing skill quality, bumping skill versions, or optimizing skill trigger descriptions. Pro-grade lifecycle covering scaffold, baseline testing, evals, lint, semver, CHANGELOG, and description optimization. Triggers on "create a skill", "new skill", "迭代 skill", "优化 skill", "skill 版本", "skill lint", "review this skill", "write a skill for X", "turn this into a skill", or whenever the user starts or edits a SKILL.md.
license: MIT
compatibility: >
  Requires Python 3.8+ (stdlib only). Optional: subagents for pressure testing
  and a benchmark-review HTML viewer for eval comparison.
metadata:
  author: zwbao
  version: "0.1.0"
  tags: meta skill-lifecycle tdd-for-docs lint semver changelog
---

# skill-creator-pro — A pro-grade skill lifecycle

You are about to create or change a skill. That is a high-leverage act: one
skill lives in the system prompt of every future conversation and gets invoked
tens, hundreds, or thousands of times. **Treat it like production code.**

The lifecycle is one pipeline: **RED → GREEN → EVAL → LINT → BUMP →
OPTIMIZE-DESC → PACKAGE / SYNC**. Each step exists because skipping it has
produced a specific failure mode in real use.

---

## The Core Loop

```
Understand intent
  │
  ▼
RED: Run 1-2 baseline subagent scenarios WITHOUT the skill
  │  (watch it fail; record rationalizations verbatim)
  ▼
GREEN: scripts/init_skill.py <name>  →  fill SKILL.md addressing those failures
  │  (description = "Use when ..."; body explains WHY, not just WHAT)
  ▼
EVAL (optional, recommended for non-trivial skills):
  │  write evals.json → spawn with-skill + baseline subagents → benchmark.json
  │  → eval-viewer → user feedback → improve → re-run
  ▼
REFACTOR: close new rationalizations surfaced by evals
  │
  ▼
LINT: scripts/lint_skill.py <name>  →  fix all errors, then warns
  │
  ▼
BUMP: scripts/bump_version.py <name> --type <patch|minor|major> -m "..."
  │  (creates/updates CHANGELOG.md, badges, frontmatter.metadata.version)
  ▼
OPTIMIZE TRIGGER DESC: (when accuracy matters)
  │  iterate the description against 20 trigger queries (10 should-trigger, 10 near-miss)
  ▼
PACKAGE / SYNC: deploy to ~/.claude/skills/ or rsync to a distribution repo
```

**Do not skip RED.** The biggest failure mode of hand-written skills is that
they solve problems the model never had — you assumed a rationalization that
never appears, and missed the one that does.

---

## Decide the Track Up Front

Not every skill earns the full pipeline. Pick a track **before** you start:

| Track | When | Skip |
|-------|------|------|
| **Lightweight** | Personal utility, narrow scope, pure-reference, one user | RED, EVAL, description optimization |
| **Full** | Discipline skill (TDD-like), shipped to others, >1 use case, high stakes | Nothing; run the whole loop |
| **Audit-only** | Existing skill the user wants polished | Start at LINT, skip RED/GREEN |

Announce the track to the user in one line: *"Going with the lightweight track
because X."* Let them redirect.

---

## Step-by-Step

### 1. Understand intent (2 min)

Ask, using `AskUserQuestion` when available:

- What should this skill enable a future Claude to do?
- What would a user **actually type** that should trigger it? (Get 2-3 real
  phrasings, not abstract intents.)
- Input → output: concrete shape, formats, file types.
- One sentence on **why it doesn't already work without a skill** — this is the
  gap the skill fills.

If the user says "turn this conversation into a skill", mine the transcript
instead of asking: extract the steps they corrected, the tools used, the
unobvious judgment calls. Then confirm the gaps.

### 2. RED — baseline subagent test (full track only)

**Before writing a single line of the skill**, run one pressure scenario with a
subagent **without** the skill. Use the Agent tool:

> Execute this task: [the realistic user prompt]. Report what you did and how
> you decided, verbatim. No skill is available.

Record: *what did it do wrong? what rationalizations did it use?* These become
the specific things your skill must counter. If the baseline succeeds
effortlessly, **the skill is probably unnecessary** — tell the user.

See `references/tdd-for-skills.md` for pressure-scenario patterns, pressure
types (time, sunk cost, authority, exhaustion), and a catalog of
rationalizations.

### 3. GREEN — scaffold + write

```bash
python scripts/init_skill.py <name> --dest ~/.claude/skills
```

This creates `<dest>/<name>/` with:

- `SKILL.md` — frontmatter template + TODO placeholders
- `README.md` — human-readable, version badge, install snippet, options table
- `scripts/` — empty; create if the skill has deterministic helpers
- `references/` — empty; create for heavy reference material (>100 lines)

Now fill `SKILL.md`:

- **Frontmatter** (see `references/frontmatter-spec.md` for the full spec):
  ```yaml
  ---
  name: <kebab-case-name>
  description: Use when <specific triggering conditions>. Triggers on
    <concrete phrases>.
  license: MIT
  metadata:
    author: <you>
    version: "0.1.0"
    tags: <space-separated>
  ---
  ```
  `name` and `description` are the only hard requirements; the rest improves
  discoverability, versioning, and lint signal.

- **Body** (≤500 lines; split to `references/` beyond that):
  - One-paragraph overview.
  - "When to Use" bullet list of symptoms, and "When NOT to Use" for adjacent
    cases.
  - Workflow steps (imperative: "Do X", not "You should do X").
  - A quick-reference table for scanning.
  - Common mistakes with fixes.
  - **Explain the WHY** for every non-obvious rule. Today's models have theory
    of mind — rigid MUSTs without reasoning produce brittle compliance.

- **README.md** — humans read this on GitHub or in the file browser. Keep the
  version badge, install command, and a minimal usage example.

### 4. EVAL — objective benchmark (full track)

Write 2-3 realistic test prompts in `evals/evals.json`, spawn **with-skill**
and **baseline** subagents in the same turn, collect outputs into
`<skill>-workspace/iteration-1/`, grade against assertions, aggregate into
`benchmark.json`, review the side-by-side output, iterate.

See `references/evals-and-benchmark.md` for the schemas, workspace layout, and
what a benchmark review should surface.

### 5. REFACTOR — close new rationalizations

When you read the transcripts (not just outputs) from the with-skill runs, look
for:

- **Repeated helper scripts** the subagent wrote independently — bundle one
  into `scripts/`.
- **New rationalizations** the skill didn't counter — add them to a
  rationalization table in the body, keep the *why* attached.
- **Instructions the model ignored** — they're likely too abstract or too
  rigid; rewrite as a principle with a concrete example.

### 6. LINT — automated audit

```bash
python scripts/lint_skill.py <name> --path <skill-dir>
# or:  python scripts/lint_skill.py <name> --dest ~/.claude/skills --json
```

Checks (see `references/lint-rules.md` for the full list):

- Structure: `SKILL.md` present, optional `README.md`, `CHANGELOG.md`.
- Frontmatter: `name` + `description` required; `description` starts with "Use
  when"; `metadata.version` is semver; `tags` present; `description` ≥ 80
  chars (below = almost never enough trigger info).
- **Description anti-pattern**: warns if the description reads like a workflow
  summary ("then ... next ... finally ..."). When the description describes
  *what* the skill does, the model follows the description and skips the body.
  Keep it strictly "when to use".
- Body: no `TODO` placeholders left, ≤500 lines, interactive skills mention
  `AskUserQuestion` (or explicitly declare non-interactive).
- Scripts: Python CLIs use `argparse`, no `pip --break-system-packages` in
  production code paths.

Fix `error`-severity findings before shipping. Treat `warn` as a checklist.

### 7. BUMP — semver + CHANGELOG

```bash
python scripts/bump_version.py <name> --path <skill-dir> \
    --type patch \
    --message "primary change summary" \
    --change "additional bullet" \
    --change "additional bullet"
```

| Bump | Use for |
|------|---------|
| `patch` | Bug fix, wording, frontmatter tweak, CJK rendering fix |
| `minor` | New CLI flag, new option, new reference doc, expanded scope |
| `major` | Breaking CLI change, removed option, renamed skill |

Stay in `0.x` until the skill has stabilized across real use.

The script updates `README.md` version badge, `SKILL.md` frontmatter
`metadata.version`, and prepends a dated entry to `CHANGELOG.md`
(auto-created in Keep-a-Changelog format if missing).

### 8. OPTIMIZE trigger description (optional, full track)

Build a 20-query eval set (≈10 should-trigger, ≈10 near-miss
should-not-trigger) and iterate the description against it. Split 60/40
train/test and pick the winner by **test** score, not train, to avoid
overfitting.

See `references/description-optimization.md` for the "when-to-use-only" rule,
a worked set of good/bad description examples, and how to write realistic
near-miss queries.

### 9. PACKAGE / SYNC

- **Single-location deploy** (most users): the skill is already live in
  `~/.claude/skills/<name>/`. Verify with a fresh conversation.
- **Shared library** (publishing to a repo): keep the source-of-truth repo,
  `~/.claude/skills/<name>` (via symlink), and the distribution repo in sync.
  Never let the copies drift — use `rsync` from the source whenever the
  distribution repo is separate from the source.

---

## The Three Iron Laws

### 1. No skill without a failing test (or a documented reason why)

If you skipped RED, write one sentence in the skill's commit message
explaining why: *"Lightweight track, pure reference, verified by eyeballing
the rendered output."* Forcing yourself to justify it in writing prevents
lazy skipping.

### 2. Description = "when to use", never "what it does"

Testing found that when the description summarizes the workflow, the model
follows the description **instead of reading the skill body**. A description
saying "performs code review between tasks" caused the model to do ONE
review; the actual skill required TWO. Changing the description to just "Use
when executing plans with independent tasks" fixed it.

See the rationalization table at the end of this file.

### 3. Violating the letter = violating the spirit

If the skill says "run lint before bump", running bump first and lint after
"because it's faster" is a violation. The letter exists because the spirit
isn't self-enforcing. When tempted to bend a rule, **update the skill
instead** so the rule reflects your current judgment.

---

## When NOT to create a skill

Push back on the user — politely — if:

- The task is a one-off; skills are for repeated patterns.
- The rule is mechanically enforceable (regex, linter, type system). A skill
  documents judgment calls; automate the rest.
- The project-specific convention belongs in `CLAUDE.md`, not in a globally
  loaded skill.
- There's already a skill doing this; **improve the existing one** rather
  than forking.

---

## Rationalization Table — watch yourself for these

| Excuse | Reality |
|--------|---------|
| "Skipping RED because the skill is obvious" | Obvious to you ≠ obvious under pressure. Takes 3 minutes. Run it. |
| "I'll polish the description later" | Description is the only thing that makes the skill discoverable. Polish it before shipping, not "later". |
| "Just this once I'll summarize the workflow in the description" | The model will shortcut past the body. This is the single most tested failure mode. |
| "The lint warning isn't a real problem" | If you're right, fix the lint rule. If the rule is right, fix the skill. Don't suppress. |
| "I'll bump version later" | Every change without a CHANGELOG entry is a loss of history. Bump now. |
| "It's working for me" | A skill's job is to work for **future Claude** in conversations you won't see. Test from that stance. |

---

## Where to go next

- `references/frontmatter-spec.md` — every field, when to set it, common
  mistakes.
- `references/tdd-for-skills.md` — RED pressure scenarios, subagent prompts,
  rationalization capture.
- `references/description-optimization.md` — the "when-to-use-only" rule, good
  vs bad examples, iteration loop mechanics.
- `references/evals-and-benchmark.md` — evals.json schema, workspace layout,
  benchmark review, grading assertions.
- `references/lint-rules.md` — full list of lint checks, severities, and the
  reasoning behind each.
