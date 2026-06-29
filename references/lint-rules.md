# Lint rules

The `scripts/lint_skill.py` script enforces a layered set of checks. Each
finding has a severity (`error`, `warn`, `info`), a code, a message, and a
fix hint.

## Contents

- [Severity policy](#severity-policy)
- [Checks](#checks)
- [Disabling a check](#disabling-a-check)
- [Exit codes](#exit-codes)
- [Running](#running)

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

- `FM_DESC_PERSON` (info) — description opens in first person ("I can…",
  "Let me…"). The description is injected into the system prompt; write it in
  third person so discovery works.

### References (Anthropic official rules)

- `REF_NESTED` (warn) — a file under `references/` is more than one level deep
  (`references/<sub>/<file>.md`). Nested references get partial-read with
  `head -100` and missed; flatten to exactly one level.
- `REF_NO_TOC` (warn) — a `references/*.md` over 100 lines has no table of
  contents in its first 50 lines. Add a `## Contents` TOC so a partial read
  still reveals the full scope.

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

### Router + workflows

These fire only for router-shaped skills (a `workflows/` directory exists, or
the body has a "Workflow Index" / "Routing Rules" section). Single-file skills
are unaffected.

- `ROUTER_NO_WORKFLOWS` (warn) — SKILL.md reads like a router but `workflows/`
  is empty or missing. Either add workflows or make it a single-file skill.
- `ROUTER_NO_INDEX` (warn) — `workflows/` has files but SKILL.md has no Workflow
  Index / Routing Rules. Without the index, the router can't route.
- `ROUTER_DEAD_LINK` (error) — the body links `workflows/<x>.md` but the file
  doesn't exist. A dead route is a ship-blocker.
- `ROUTER_WORKFLOW_NOT_INDEXED` (warn) — a workflow file exists but isn't linked
  from SKILL.md, so the router never reaches it. Add it to the index.
- `ROUTER_NO_EVIDENCE_CONTRACT` (info) — the router declares no Evidence/Data
  Contract. Recommended so workflows don't re-litigate "can I make this up?".
- `WORKFLOW_NO_USE_WHEN` (warn) — a workflow file lacks a "Use When" section.
  Without it the router (and the agent) can't tell when the workflow applies.
- `WORKFLOW_NO_OUTPUT` (warn) — a workflow lacks an "Output Format" section.
  Structured output is what makes a workflow reproducible.
- `WORKFLOW_NO_GUARDRAILS` (info) — a workflow lacks a "Guardrails" section.
- `WORKFLOW_TODO` (error) — a workflow file still has `TODO:` placeholders.

### Scripts

- `SCRIPT_NO_ARGPARSE` (warn) — `.py` file with `if __name__ == "__main__"`
  but no `argparse`. Consistent CLI surface across all skills makes them
  interoperable.
- `SCRIPT_PIP_IN_CODE` (info) — script shells out `pip install
  --break-system-packages`. Install instructions belong in docs, not
  execution paths; doing it in code creates the "silent breakage" category
  of bug.

### Prompt/script boundary (harness vs brain)

Teeth on the boundary doctrine (`references/prompt-script-boundary.md`). They
guard **both** directions — judgment leaking into the harness, and the harness's
forcing-functions going un-built. A flag is a prompt to re-examine the boundary,
not an automatic defect.

Guarding **script ← judgment** (don't freeze judgment into the deterministic layer):

- `SCRIPT_LLM_CALL` (warn) — a `scripts/` file imports/calls an LLM SDK (openai,
  anthropic, litellm, `chat.completions`, …). Harness scripts must be
  deterministic; move the judgment to a prompt/subagent, or isolate a genuine
  model-driver layer from the state/validation scripts.
- `SCRIPT_KEYWORD_JUDGMENT` (info) — a `scripts/` file holds a large hardcoded
  domain-term collection (`KEYWORDS` / `CATEGORIES` / `TIER_DEFS` / `TAXONOMY` /
  …) used for branching. Judgment frozen into code misfires on unseen phrasings;
  route classification/extraction through a prompt or subagent.
- `SCRIPT_AUTOFILL_JUDGMENT` (warn) — a CLI arg named `insight` / `lesson` /
  `abstraction` / `rationale` / `summary` / `takeaway` carries a non-`None`
  default. A judgment field with a default gets auto-filled and the model skips
  it; leave it `None`/required so the model authors it deliberately.

Guarding **judgment ← script** (the model must not own the deterministic layer):

- `STATEFUL_HARNESS_NO_OBSERVE_VALIDATE` (warn) — a `scripts/` file persists a
  state file (`json.dump` / json `write_text`) AND defines ≥2 mutating
  subcommands (`add`/`set`/`update`/`merge`/`prune`/…) but ships no read-only
  projection (`observe`/`status`/`render`/…) and no `validate`. A long run then
  re-grounds on lossy memory and drifts. Add an `observe` (objective / done /
  pending / lessons / best) + a `validate` invariant-checker.
- `STATE_DIRECT_WRITE` (warn) — `SKILL.md` or a workflow instructs the LLM to
  edit/write a state `*.json` / `*.yaml` / `*.db` directly (within ~3 words of a
  "state" reference). The LLM must mutate durable state only through the
  harness's typed commands, never by editing the file — else it drifts/corrupts
  and can't be audited.
- `SUBAGENT_NO_RETURN_CONTRACT` (info) — the body dispatches subagents
  ("dispatch" / "subagent" / "fan out" / "spawn") but specifies no typed return
  contract ("return exactly …" / named fields / schema). A free-prose hand-back
  reintroduces judgment at the parse step; give each subagent a fixed scope and a
  named-field return.

Not linted (judgment-shaped — live as doctrine + rationalization-table rows): **H**
structured-search-over-sampling, and **G/I** held-out admit + honest
explored-vs-merged reporting.

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
