# Lint rules

The `scripts/lint_skill.py` script enforces a layered set of checks. Each
finding has a severity (`error`, `warn`, `info`), a code, a message, and a
fix hint.

## Severity policy

| Severity | Meaning | Action |
|----------|---------|--------|
| `error` | Skill is malformed or unusable; exit code 2 | **Block**: fix before shipping |
| `warn` | Likely quality problem, not a hard break | Fix unless you can justify keeping it |
| `info` | Recommendation; context-dependent | Apply if cheap and safe |

## Checks

### Structure

- `DIR_MISSING` (error) — the skill directory doesn't exist.
- `DIR_NAME` (warn) — directory name isn't lowercase kebab-case. Some
  harnesses reject non-kebab names.
- `MISSING_SKILL_MD` (error) — no `SKILL.md`. A skill without a SKILL.md is
  not a skill.
- `NO_README` (info) — no `README.md`. Not required, but humans browsing
  the filesystem will thank you.

### Frontmatter — required fields

- `FM_MISSING_REQUIRED` (error) — `name` or `description` missing or empty.
  These are the minimum viable frontmatter. Skill cannot be discovered
  without them.
- `FM_MISSING_RECOMMENDED` (warn) — `license` or `metadata` missing.
  These signal pro-grade hygiene; their absence suggests an ad-hoc skill.

### Frontmatter — name

- `FM_NAME_MISMATCH` (warn) — frontmatter `name` doesn't match directory
  basename. Allowed if the name is namespaced (`plugin:skill`).

### Frontmatter — description

- `FM_DESC_TOO_SHORT` (warn) — under 80 chars. Usually means missing trigger
  phrases or disambiguation.
- `FM_DESC_TOO_LONG` (warn) — over 1024 chars. YAML frontmatter has a hard
  total budget.
- `FM_DESC_NO_TRIGGER` (warn) — missing "Use when" and "Triggers on"
  phrasing. Without explicit trigger language, the model may miss the skill
  when it's relevant.
- `FM_DESC_WORKFLOW_SUMMARY` (warn) — description contains workflow-smell
  phrases (" then ", " next ", " step 1", "workflow:", etc.). This is the
  single most-tested failure mode: workflow summaries in the description
  cause the model to shortcut past the body.

### Frontmatter — metadata

- `FM_META_MISSING` (info) — `metadata.{author,version,tags}` missing.
- `FM_VERSION_FORMAT` (warn) — `metadata.version` is not semver (`x.y.z`).
  Required for `bump_version.py` to work.

### Body

- `BODY_TODO` (error) — unreplaced `TODO:` placeholders. Ship-blocker.
- `BODY_TOO_LONG` (warn) — more than 500 lines. Use progressive disclosure:
  move heavy content into `references/` and link from SKILL.md.
- `BODY_NO_ASKUSER` (info) — interactive workflow doesn't reference
  `AskUserQuestion`. Either add a user-prompting step or explicitly declare
  "fully automatic" / "non-interactive" so readers know this is intentional.

### Scripts

- `SCRIPT_NO_ARGPARSE` (warn) — `.py` file with `if __name__ == "__main__"`
  but no `argparse`. Consistent CLI surface across all skills makes them
  interoperable.
- `SCRIPT_PIP_IN_CODE` (info) — script shells out `pip install
  --break-system-packages`. Install instructions belong in docs, not
  execution paths; doing it in code creates the "silent breakage" category
  of bug.

### CHANGELOG

- `NO_CHANGELOG` (info) — no `CHANGELOG.md`. Running `bump_version.py` once
  creates it. Recommended for any skill that will be iterated on.

## Disabling a check

If a check is genuinely wrong for your skill, don't silence it — fix the
rule. Either:

1. Open an issue / PR against `lint_skill.py` to relax the check.
2. Add a specific justification comment next to the problem in SKILL.md so
   future maintainers understand why it's that way.

Silencing lint without a documented reason is the same anti-pattern as
"disable this test to make the build pass". Don't do it.

## Exit codes

- `0` — no `error`-severity findings (warns and infos don't block).
- `2` — at least one `error`. Use this in CI to block bad skills from
  being merged.

## Running

```bash
# Audit a skill at the default location
python scripts/lint_skill.py my-skill

# Audit at a custom parent directory
python scripts/lint_skill.py my-skill --dest ~/my-skills

# Audit by absolute path
python scripts/lint_skill.py --path /Users/me/projects/my-skill

# Machine-readable output
python scripts/lint_skill.py my-skill --json | jq '.findings[] | select(.severity == "error")'
```
