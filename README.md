# skill-creator-pro

![Version](https://img.shields.io/badge/version-0.5.0-CC785C)
![License](https://img.shields.io/badge/license-MIT-blue)

A pro-grade lifecycle for creating, testing, versioning, and iterating on
Claude Code skills. One pipeline from idea to release:

**RED → GREEN → EVAL → LINT → BUMP → OPTIMIZE-DESC → PACKAGE/SYNC**

- **RED** — run a baseline subagent scenario *without* the skill and watch it
  fail. Document the failure modes.
- **GREEN** — scaffold the skill, fill `SKILL.md` targeting those specific
  failures. Description states *what + when*, never the *how* (workflow steps).
- **EVAL** — write `evals.json`, run with-skill vs baseline subagents in
  parallel, grade against assertions, review the benchmark.
- **LINT** — audit frontmatter, body, scripts against the full rule set.
- **BUMP** — semver bump with auto-updated `CHANGELOG.md` and version badge.
- **OPTIMIZE-DESC** — iterate the trigger description against a 20-query eval
  set (10 should-trigger, 10 near-miss negatives) to maximize recall and
  precision.
- **PACKAGE / SYNC** — deploy to `~/.claude/skills/`, or ship a multi-platform
  library (`npx skills add`, plugin manifests for Claude Code / Codex / Cursor).

## Two skill shapes

The pipeline applies to both shapes; pick before scaffolding:

- **Single-file** — one `SKILL.md`. For one thing, or a few tightly-related
  things sharing one procedure.
- **Router + workflows** — a thin `SKILL.md` indexing `workflows/*.md`; the
  agent loads only the one it needs. For **≥3 distinct intents** or a growing
  capability set. Scaffold with `init_skill.py <name> --router` (router +
  `workflows/` + `.claude-plugin/` / `.codex-plugin/` / `.cursor-plugin/`
  manifests). See [`references/router-and-workflows.md`](references/router-and-workflows.md).

## Input a PRD → top-tier skill

Hand the pipeline a PRD (or spec, or loose description) and it drives the whole
lifecycle to a finished skill: ingest & classify (capability vs discipline
school; single-file vs router shape), derive evals from the acceptance
criteria, RED baseline, GREEN against the playbook, lint, version, package,
then report each PRD requirement against eval evidence. The quality bar is
distilled from the top-50 starred skill repos + Anthropic's official authoring
guidance. See [`references/prd-to-skill.md`](references/prd-to-skill.md) and
[`references/top-skills-playbook.md`](references/top-skills-playbook.md).

## Install

```bash
# Multi-platform (Claude Code / Codex / Cursor / OpenCode / Gemini …):
npx skills add zwbao/skill-creator-pro

# Or clone straight into your skills dir:
git clone https://github.com/zwbao/skill-creator-pro.git ~/.claude/skills/skill-creator-pro
# or symlink if the source lives elsewhere:
# ln -s /path/to/skill-creator-pro ~/.claude/skills/skill-creator-pro
```

Restart Claude Code (or open a new conversation). The skill triggers on
phrases like "create a new skill", "新建 skill", "优化 skill", "audit this
skill", "here's my PRD, build the skill", or whenever you edit a `SKILL.md`.

## Quick start

```bash
# Scaffold a new skill (single-file)
python3 ~/.claude/skills/skill-creator-pro/scripts/init_skill.py my-skill
# ...or a router + workflows skill:
python3 ~/.claude/skills/skill-creator-pro/scripts/init_skill.py my-skill --router

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
├── SKILL.md                         # Main entry: lifecycle + schools + PRD intake + iron laws
├── references/
│   ├── top-skills-playbook.md       # Quality bar from top-50 repos: two schools, anti-patterns, checklist
│   ├── prd-to-skill.md              # PRD → finished skill: ingest/classify, derive evals, intake template
│   ├── router-and-workflows.md      # Two skill shapes, router anatomy, Evidence Contract pattern
│   ├── shipping-a-skill-library.md  # Multi-platform packaging, exact manifest schemas, gotchas, CONTRIBUTING
│   ├── frontmatter-spec.md          # Every field, when to set it, common mistakes
│   ├── tdd-for-skills.md            # RED pressure scenarios, subagent prompts, rationalization capture
│   ├── description-optimization.md  # "What + when, never how", good/bad examples, optimization loop
│   ├── evals-and-benchmark.md       # evals.json, workspace layout, benchmark review, grading
│   └── lint-rules.md                # Full list of lint checks with reasoning per check
├── templates/
│   ├── SKILL_ROUTER_TEMPLATE.md     # Copy-paste router SKILL.md skeleton
│   └── WORKFLOW_TEMPLATE.md         # Copy-paste workflow file skeleton
├── scripts/
│   ├── init_skill.py                # Scaffold single-file or --router skill
│   ├── lint_skill.py                # Audit + JSON findings (incl. router + reference checks)
│   └── bump_version.py              # Semver bump + README badge + CHANGELOG.md
├── .claude-plugin/ .codex-plugin/ .cursor-plugin/   # Multi-platform install manifests
├── CONTRIBUTING.md                  # Contribution contract (lint-clean, semver, commits)
└── CHANGELOG.md
```

## Pick your track

- **Lightweight** — personal utility, narrow scope: skip RED, EVAL, description optimization.
- **Full** — discipline skill, shipped to others, high stakes: run the whole loop.
- **Audit-only** — existing skill to polish: start at LINT.

## Three iron laws

1. **No skill without a failing test** (or a one-sentence justification for why you skipped RED).
2. **Description = what + when, never how** — state the capability and the triggers; reciting the *workflow steps* makes the model shortcut past the body.
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
