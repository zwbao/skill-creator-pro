# Contributing to skill-creator-pro

skill-creator-pro is a meta-skill: it teaches and tooling the lifecycle for
*other* skills. So it must hold itself to its own bar. Every change runs the
same pipeline it preaches.

## The contract

Before opening a PR, ensure:

- [ ] `python3 scripts/lint_skill.py skill-creator-pro --path .` passes with
      **0 errors** (warns triaged).
- [ ] `SKILL.md` stays ≤500 lines; heavy material lives in `references/`.
- [ ] The `description` frontmatter is still "when to use", never a workflow
      summary (the skill's own Iron Law #2).
- [ ] If you changed a script's CLI, the docs (`SKILL.md`, `README.md`, the
      relevant `references/*.md`) reflect the new flags — no code-only changes.
- [ ] You bumped the version with `scripts/bump_version.py` and the
      `CHANGELOG.md` entry describes the change. (patch = wording/fix,
      minor = new flag/reference/scope, major = breaking CLI/removed option.)
- [ ] New lint rules are documented in `references/lint-rules.md`.
- [ ] New behavior has a quick manual verification noted in the PR description
      (e.g. "scaffolded a --router skill in /tmp and linted it: 0 errors").

## What good contributions look like

- **New rules earn their place.** A rule added to the skill should counter a
  real failure mode you observed, not a hypothetical. State the failure in the
  PR.
- **Tooling tracks doctrine.** If you add a doctrine to `SKILL.md`, add a lint
  check (or explain why it can't be mechanized). Doctrine without enforcement
  drifts.
- **Distill, don't dump.** References are playbooks, not transcripts. If a
  section reads like a log, compress it into rules.

## Layout

```text
skill-creator-pro/
├── SKILL.md          # lifecycle + skill shapes + iron laws
├── references/       # deep-dive playbooks (progressive disclosure)
├── templates/        # copy-paste skeletons (router, workflow)
├── scripts/          # init_skill / lint_skill / bump_version (argparse CLIs)
├── CHANGELOG.md      # Keep a Changelog
└── README.md         # human-facing
```

## Commit / PR titles

Conventional Commits: `<type>(<scope>): <subject>`.

| type | when |
|------|------|
| `feat` | new lifecycle step, lint rule, template, script flag |
| `fix` | bug in a script, broken doc link, wrong lint behavior |
| `docs` | SKILL.md / references / README wording |
| `refactor` | restructure without behavior change |
| `chore` | scaffolding, maintenance |

Subject: imperative, lowercase first word, no trailing period, ≤72 chars.
Example: `feat(lint): add router workflow-index checks`.

## The one rule that overrides the rest

If a lint rule or doctrine here is wrong, **fix the rule** — don't suppress it
or work around it. A meta-skill that tolerates its own broken checks has no
standing to lint anyone else's.
