# skill-creator-pro

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)
![License](https://img.shields.io/badge/license-MIT-blue)

A pro-grade lifecycle for creating, testing, versioning, and iterating on
Claude Code skills. One pipeline from idea to release:

**RED → GREEN → EVAL → LINT → BUMP → OPTIMIZE-DESC → PACKAGE/SYNC**

- **RED** — run a baseline subagent scenario *without* the skill and watch it
  fail. Document the failure modes.
- **GREEN** — scaffold the skill, fill `SKILL.md` targeting those specific
  failures. Description says *when* to use, never *what* the skill does.
- **EVAL** — write `evals.json`, run with-skill vs baseline subagents in
  parallel, grade against assertions, review the benchmark.
- **LINT** — audit frontmatter, body, scripts against the full rule set.
- **BUMP** — semver bump with auto-updated `CHANGELOG.md` and version badge.
- **OPTIMIZE-DESC** — iterate the trigger description against a 20-query eval
  set (10 should-trigger, 10 near-miss negatives) to maximize recall and
  precision.
- **PACKAGE / SYNC** — deploy to `~/.claude/skills/` or a distribution repo.

## Install

```bash
git clone https://github.com/zwbao/skill-creator-pro.git ~/.claude/skills/skill-creator-pro
# or symlink if the source lives elsewhere:
# ln -s /path/to/skill-creator-pro ~/.claude/skills/skill-creator-pro
```

Restart Claude Code (or open a new conversation). The skill triggers on
phrases like "create a new skill", "新建 skill", "优化 skill", "audit this
skill", or whenever you edit a `SKILL.md`.

## Quick start

```bash
# Scaffold a new skill
python3 ~/.claude/skills/skill-creator-pro/scripts/init_skill.py my-skill

# Edit SKILL.md and README.md, then audit
python3 ~/.claude/skills/skill-creator-pro/scripts/lint_skill.py my-skill

# Bump version + prepend CHANGELOG entry
python3 ~/.claude/skills/skill-creator-pro/scripts/bump_version.py my-skill \
  --type patch -m "initial release"
```

Or just tell Claude "create a skill that does X" and the pipeline runs.

## Structure

```
skill-creator-pro/
├── SKILL.md                         # Main entry: lifecycle + decision flow + iron laws
├── references/
│   ├── frontmatter-spec.md          # Every field, when to set it, common mistakes
│   ├── tdd-for-skills.md            # RED pressure scenarios, subagent prompts, rationalization capture
│   ├── description-optimization.md  # "When to use" rule, good/bad examples, optimization loop mechanics
│   ├── evals-and-benchmark.md       # evals.json, workspace layout, benchmark review, grading
│   └── lint-rules.md                # Full list of lint checks with reasoning per check
└── scripts/
    ├── init_skill.py                # Scaffold skill-name/ with rich frontmatter + README
    ├── lint_skill.py                # Audit + JSON findings (severity: error/warn/info)
    └── bump_version.py              # Semver bump + README badge + CHANGELOG.md
```

## Pick your track

- **Lightweight** — personal utility, narrow scope: skip RED, EVAL, description optimization.
- **Full** — discipline skill, shipped to others, high stakes: run the whole loop.
- **Audit-only** — existing skill to polish: start at LINT.

## Three iron laws

1. **No skill without a failing test** (or a one-sentence justification for why you skipped RED).
2. **Description = "when to use", never "what it does"** — workflow summaries in the description cause the model to shortcut past the body.
3. **Violating the letter = violating the spirit** — if the rule feels wrong, fix the rule, don't bend it.

See [`SKILL.md`](./SKILL.md) for the full walkthrough and [`references/`](./references/) for deep dives.

## Self-audit

This skill passes its own lint:

```
$ python3 scripts/lint_skill.py skill-creator-pro
✓ skill-creator-pro: 0 errors, 0 warnings
```

## Honest limitations

This skill is a **hypothesis**, not a validated product. Known risks:

- **Over-engineering small skills** — the lightweight track mitigates but
  doesn't eliminate the temptation to run the full loop when it's overkill.
- **Lint false positives** — `FM_DESC_WORKFLOW_SUMMARY` keyword detection can
  misfire on legitimate descriptions; review warnings, don't blindly "fix".
- **Methodology conflicts** — rules codified here are judgment calls; they
  may need revision as real-world use surfaces edge cases.
- **TDD-for-docs is an empirical claim**, not a controlled experiment. The
  "RED baseline first" rule inherits that uncertainty.

Report real failures and improvements as issues / PRs.

## License

MIT — see [`LICENSE`](./LICENSE).
