# Shipping a skill library (multi-platform packaging)

A single skill lives in `~/.claude/skills/<name>/`. A **library** — several
skills shipped together to other people and other agents — needs packaging so
one install command works across Claude Code, Codex, Cursor, OpenCode, Gemini,
and friends. This is the `LLMQuant/skills` and `vercel-labs/skills` model.

## Contents

- [The one-command install target](#the-one-command-install-target)
- [Repository layout](#repository-layout)
- [Plugin manifests](#plugin-manifests)
- [Authoritative facts & install-breaking gotchas](#authoritative-facts--install-breaking-gotchas)
- [CONTRIBUTING: the required contract](#contributing-the-required-contract)
- [Conventional Commits for PR titles](#conventional-commits-for-pr-titles)
- [Source-of-truth and sync](#source-of-truth-and-sync)
- [When NOT to package as a library](#when-not-to-package-as-a-library)

## The one-command install target

The goal: a user runs one command and the skills land in the right place for
their agent.

```bash
npx skills add <owner>/<repo>            # auto-detects the host agent
npx skills add <owner>/<repo> -g --all   # all skills, global
npx skills add <owner>/<repo> --skill <name-a> <name-b>
npx skills add <owner>/<repo> -a codex   # target a specific agent
```

For this to work, the repo follows a fixed layout and ships plugin manifests.

## Repository layout

```text
<repo>/
├── skills/
│   ├── <skill-a>/
│   │   ├── SKILL.md
│   │   ├── workflows/      # if router-shaped
│   │   ├── scripts/
│   │   └── assets/
│   └── <skill-b>/
│       └── SKILL.md
├── templates/              # SKILL + workflow skeletons for contributors
├── .claude-plugin/         # Claude Code: plugin.json + marketplace.json
├── .codex-plugin/          # Codex: plugin.json
├── .cursor-plugin/         # Cursor: plugin.json
├── README.md
├── README.zh-CN.md         # parallel bilingual doc (don't duplicate every workflow)
├── CONTRIBUTING.md
└── LICENSE
```

Every skill lives under `skills/`. Do **not** scatter standalone `SKILL.md`
files at the repo root — the install unit is a skill folder under `skills/`.

## Plugin manifests

### `.claude-plugin/plugin.json`

```json
{
  "name": "<repo-name>",
  "version": "0.1.0",
  "description": "<what the library does>. Bundles every skill under skills/.",
  "author": { "name": "<you>", "url": "https://..." },
  "homepage": "https://github.com/<owner>/<repo>",
  "repository": "https://github.com/<owner>/<repo>",
  "license": "MIT",
  "keywords": ["<topic>", "skills"]
}
```

### `.claude-plugin/marketplace.json`

```json
{
  "name": "<owner-or-brand>",
  "owner": { "name": "<you>", "url": "https://..." },
  "description": "<one line>",
  "version": "0.1.0",
  "plugins": [
    {
      "name": "<repo-name>",
      "source": ".",
      "description": "All skills bundled as one plugin: <list>.",
      "version": "0.1.0",
      "license": "MIT"
    }
  ]
}
```

### `.codex-plugin/plugin.json`

Same core fields, plus `"skills": "./skills/"` and an `interface` block
(`displayName`, `shortDescription`, `defaultPrompt` examples, `brandColor`).

### `.cursor-plugin/plugin.json`

Minimal: `name`, `version`, `description`, `repository`, `"skills": "./skills/"`.

> **Single-skill-at-root repo** (like skill-creator-pro): the `SKILL.md` is at
> the repo root, not under `skills/`. Point the Codex/Cursor `skills` field at
> `"./"` instead of `"./skills/"`, and the Claude `plugin.json` needs only
> `{"name": "<kebab>"}` (since v2.1.142 a root `SKILL.md` auto-loads).

Keep the `version` fields in the three manifests and `marketplace.json` in sync
with each other; they version the *library*, while each skill's
`metadata.version` versions that skill independently.

## Authoritative facts & install-breaking gotchas

Verified against Anthropic's `plugins-reference` / `plugin-marketplaces` docs
and the `vercel-labs/skills` CLI source. Wrong field names/types break installs.

- **Only `.claude-plugin/` is read by Claude Code.** `.codex-plugin/` and
  `.cursor-plugin/` are pure metadata consumed by the `npx skills` CLI and the
  non-Claude agents — Claude ignores them. That's why one repo serves all
  platforms.
- **`name` is the only hard-required Claude field**, but a wrong *type* (e.g.
  `keywords` as a string instead of an array) is a load *error*, not a warning.
- **`version` is a footgun.** In `plugin.json` it's the update cache key: set it
  but forget to bump and users stay frozen on old code. For fast iteration you
  may omit it entirely (git SHA then drives updates).
- **Components inside `.claude-plugin/` silently disappear.** Only `plugin.json`
  and `marketplace.json` go there; `skills/`, `agents/`, `commands/`, `hooks/`
  live at the repo **root**. This is the #1 "my skills don't show up" bug.
- **`skills/` is always auto-scanned** by both Claude Code and the CLI, so you
  rarely need a `skills` field in `plugin.json` (when present it *adds to*, not
  replaces, `skills/`). Manifests are for metadata/marketplace, not discovery.
- **`npx skills add` discovery order**: repo root first (→ single-skill-at-root
  works), then `skills/` (+ `.curated/.experimental/.system`), one level deep
  (`skills/<name>/SKILL.md`), two levels for catalogs
  (`skills/<category>/<name>/SKILL.md`). A skill = any dir with a `SKILL.md`
  whose frontmatter has `name` + `description`. `..` paths are rejected.
- **One source, fanned out.** The CLI writes each skill into every target
  agent's dir (Claude Code → `.claude/skills`; the universal cluster — Codex,
  Cursor, OpenCode, Gemini, Antigravity, Copilot — → `.agents/skills`). You
  never author per-agent copies.
- **Reserved marketplace names**: don't name a marketplace `agent-skills` or
  `anthropic-*`.
- **Relative-path marketplace `source`** (`"."`, `"./plugins/x"`) only resolves
  when the marketplace is added via git (GitHub/GitLab/git URL), not via a raw
  URL to `marketplace.json` — use a `github`/`npm` source for URL distribution.
- **Validate before shipping**: `claude plugin validate ./ --strict` catches
  typo'd / wrong-type fields. Smoke-test installs:
  `npx skills add <you>/<repo> -a claude-code` (and `codex`, `cursor`,
  `opencode`).

## CONTRIBUTING: the required contract

A shipped library needs a written quality bar so contributions stay consistent.
State, at minimum:

- **Folder naming** convention (e.g. all skills prefixed `<brand>-`).
- **Required SKILL.md parts** — for routers: routing rules, workflow index,
  evidence contract, output requirements.
- **Required workflow parts** — use-when, inputs, procedure, output format,
  guardrails.
- **Freshness + fallback rules** — must be explicit in every skill.
- **Guardrails** that prevent invented data or unsupported conclusions.

### PR checklist (adapt)

- [ ] Skill folder named per convention.
- [ ] `SKILL.md` routes to a workflow (router) or contains the full procedure (single-file).
- [ ] Workflow files have use-when / inputs / procedure / output / guardrails.
- [ ] Evidence contract present; freshness + fallback explicit.
- [ ] Output format is structured.
- [ ] README tables updated if a skill or major workflow was added/removed/renamed.
- [ ] `lint_skill.py` passes with zero errors.

## Conventional Commits for PR titles

Validate PR titles with a CI action (squash-merge makes the PR title the commit
subject). Format: `<type>(<scope>): <subject>`.

| type | when |
|------|------|
| `feat` | new skill, new workflow, new capability |
| `fix` | bug in a skill/workflow/script; broken link; misrouting |
| `docs` | README, CONTRIBUTING, templates, comments |
| `refactor` | restructure without behavior change |
| `chore` | scaffolding, deps, maintenance |
| `ci` | workflows, lint config |

Subject: imperative, lowercase first word, no trailing period, ≤72 chars.
Example: `feat(options): add iv-term-structure workflow`.

## Source-of-truth and sync

If the skills also live in `~/.claude/skills/` (symlinked) or another
distribution repo, keep one source of truth and `rsync` outward. Never let
copies drift — a user who installs the distribution repo must get the same
bytes as your local source. (See your memory rule on dual-repo sync.)

## When NOT to package as a library

A single personal skill doesn't need any of this. Plugin manifests, a
CONTRIBUTING file, and CI are overhead that pays off only when (a) you ship to
other people, or (b) you ship to multiple agent platforms. One skill, one user,
one machine → just keep it in `~/.claude/skills/`.
