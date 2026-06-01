#!/usr/bin/env python3
"""
Scaffold a new skill with skill-creator-pro conventions.

Creates <dest>/<name>/ with SKILL.md (pro frontmatter), README.md (version
badge + install snippet), empty scripts/ and references/ dirs.

Usage:
    python init_skill.py <name>                       # dest defaults to ~/.claude/skills
    python init_skill.py <name> --router              # router + workflows/ + plugin manifests
    python init_skill.py <name> --dest ~/my-skills
    python init_skill.py <name> --dest . --author me  # custom author
    python init_skill.py <name> --force               # overwrite existing dir
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


SKILL_MD = """---
name: {name}
description: >
  Use when TODO: describe the specific triggering conditions (not what it does).
  Triggers on "TODO: concrete user phrase 1", "TODO: 中文触发短语",
  "TODO: adjacent phrasing". Keep this field focused on WHEN to use, never
  summarize the workflow (that shortcut causes the model to skip the body).
license: MIT
metadata:
  author: {author}
  version: "0.1.0"
  tags: TODO tag-a tag-b
---

# {name}

TODO: One-paragraph overview — what is this skill, what core principle does
it codify?

## When to Use

- TODO: Symptom 1 (concrete, observable)
- TODO: Symptom 2
- TODO: User-phrased intent 3

## When NOT to Use

- TODO: Adjacent case where a different skill is better
- TODO: Mechanically enforceable rules that belong in linters, not skills

## Workflow

### Step 1 — TODO

Explain WHY this step exists, not just what to do. Models have theory of
mind; reasoning beats rigid rules.

### Step 2 — TODO

TODO.

## Quick Reference

| Action | Command / Pattern |
|--------|-------------------|
| TODO | TODO |

## Common Mistakes

- **TODO mistake** — Why it happens, how to fix.

## Rationalization Table (fill in as you discover them)

| Excuse | Reality |
|--------|---------|
| TODO | TODO |
"""

ROUTER_SKILL_MD = """---
name: {name}
description: >
  Router skill for TODO-domain workflows. Use when TODO: describe the specific
  triggering conditions (not what it does). Triggers on "TODO: phrase 1",
  "TODO: 中文触发短语", "TODO: adjacent phrasing". Routes to one named workflow
  under workflows/ — never inline the procedure in this description.
license: MIT
category: TODO-category-slug
metadata:
  author: {author}
  version: "0.1.0"
  tags: TODO tag-a tag-b
---

# {name} Router

This is the router skill for `{name}`. It does NOT perform the work itself — it
identifies the user's task, selects the single closest workflow under
`workflows/`, and loads only that file. Progressive disclosure keeps the router
small and the relevant workflow focused.

## Routing Rules

1. Identify the task, the inputs, the scope/horizon, and the requested output.
2. Select the single closest workflow from the index below.
3. Open ONLY that workflow and the local resources it explicitly references.
4. Honor the Evidence Contract below for every external fact.
5. Report dates, source coverage, stale notices, and missing inputs.

## Workflow Index

| User intent | Workflow |
|---|---|
| TODO: one-line intent the user would actually express | [`workflows/example-workflow.md`](workflows/example-workflow.md) |

> Every file in `workflows/` MUST appear here, and every row MUST point to a
> file that exists. The lint checks both directions.

## Evidence Contract

- **Sources of record:** TODO — the API / DB / files / tools the workflows pull
  from. Prefer live retrieval over memory.
- **Fallback:** if a required input is unavailable, name the exact missing input
  and continue only with retrieved or user-provided evidence.
- **Never fabricate:** TODO — list the value types dangerous to guess (quotes,
  prices, citations, lab values, dosages, IDs).

## Output Requirements

1. Answer / recommendation
2. Evidence (table with sources + dates)
3. Risks / caveats
4. Data used, including coverage and stale notices
"""

SAMPLE_WORKFLOW_MD = """---
name: Example Workflow
description: TODO — one sentence; the single task this workflow performs.
pack: TODO-optional-pack
---

# Example Workflow

## Use When

Use this workflow when the user asks for TODO: the one narrow task. If the
request is broader or different, return to the router and pick another workflow.

## Inputs Needed

Required:
- TODO: input + why it is needed

Optional:
- TODO: input + how it changes the output

Freshness:
- TODO: dates / as-of stamps / versions to report with the result

Fallback:
- If a required input is unavailable, name the exact missing input and continue
  only with retrieved or user-provided evidence.

## Workflow

1. Confirm inputs, scope, and the output target.
2. Retrieve / compute the required evidence.
3. Check coverage, dates, and missing fields before interpreting.
4. Separate retrieved evidence from interpretation.
5. Produce the output in the format below.

## Output Format

1. **Answer**
2. **Evidence**
3. **Risks / Caveats**
4. **Data Used**

## Guardrails

- Do not invent missing values; name them as gaps.
- Do not present model output as if it were retrieved data.
- TODO: one domain-specific guardrail.
"""

CLAUDE_PLUGIN_JSON = """{{
  "name": "{name}",
  "version": "0.1.0",
  "description": "TODO: what this skill/library does.",
  "author": {{ "name": "{author}" }},
  "license": "MIT",
  "keywords": ["TODO-topic", "skills"]
}}
"""

CLAUDE_MARKETPLACE_JSON = """{{
  "name": "{author}",
  "owner": {{ "name": "{author}" }},
  "description": "TODO: one line.",
  "version": "0.1.0",
  "plugins": [
    {{
      "name": "{name}",
      "source": ".",
      "description": "TODO: skills bundled as one plugin.",
      "version": "0.1.0",
      "license": "MIT"
    }}
  ]
}}
"""

CODEX_PLUGIN_JSON = """{{
  "name": "{name}",
  "version": "0.1.0",
  "description": "TODO: one line.",
  "author": {{ "name": "{author}" }},
  "license": "MIT",
  "keywords": ["TODO-topic", "skills"],
  "skills": "./",
  "interface": {{
    "displayName": "{name}",
    "shortDescription": "TODO: short description.",
    "developerName": "{author}",
    "category": "TODO-category",
    "capabilities": ["Read", "Write", "Analyze"],
    "brandColor": "#0B5FFF",
    "defaultPrompt": ["TODO: example invocation."]
  }}
}}
"""

CURSOR_PLUGIN_JSON = """{{
  "name": "{name}",
  "version": "0.1.0",
  "description": "TODO: one line.",
  "skills": "./"
}}
"""

ROUTER_README_MD = """# {name}

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

TODO: One-line description for humans browsing the repo.

Router-shaped skill: a thin `SKILL.md` that indexes named procedures under
`workflows/` and loads only the one needed for the user's task.

## Install

```bash
# Multi-platform (auto-detects Claude Code / Codex / Cursor / OpenCode / …):
npx skills add <owner>/<repo>

# Or drop this directory under ~/.claude/skills/:
ln -s "$(pwd)/{name}" ~/.claude/skills/{name}
```

## Workflows

| Intent | Workflow |
|--------|----------|
| TODO | `workflows/example-workflow.md` |

## Changelog

See `CHANGELOG.md` (created on first `bump_version.py` run).
"""

README_MD = """# {name}

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

TODO: One-line description for humans browsing the repo.

## Install

```bash
# Drop this directory under ~/.claude/skills/
# Or symlink from your skills repo:
ln -s "$(pwd)/{name}" ~/.claude/skills/{name}
```

## Usage

Trigger by mentioning the skill by name or via natural-language phrases the
skill's `description` frontmatter matches.

## Options

| Argument | Default | Description |
|----------|---------|-------------|
| TODO | TODO | TODO |

## Dependencies

Python 3.8+ (stdlib only), unless the skill adds scripts that need more.

## Changelog

See `CHANGELOG.md` (created on first `bump_version.py` run).
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold a new skill-creator-pro skill")
    ap.add_argument("name", help="Skill name (kebab-case, letters/numbers/hyphens only)")
    ap.add_argument(
        "--dest",
        default=str(Path.home() / ".claude" / "skills"),
        help="Parent directory where <name>/ is created (default: ~/.claude/skills)",
    )
    ap.add_argument("--author", default=os.environ.get("USER", "unknown"),
                    help="Author name for frontmatter metadata.author")
    ap.add_argument("--router", action="store_true",
                    help="Scaffold a router + workflows/ skill (with plugin manifests) "
                         "instead of a single-file skill")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing directory (careful)")
    args = ap.parse_args()

    # Validate name
    import re
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.name):
        print(f"ERROR: name must be lowercase kebab-case (got '{args.name}')", file=sys.stderr)
        return 1

    dest = Path(args.dest).expanduser().resolve()
    skill_dir = dest / args.name

    if skill_dir.exists():
        if not args.force:
            print(f"ERROR: {skill_dir} already exists. Use --force to overwrite.", file=sys.stderr)
            return 1
        # Only overwrite SKILL.md/README.md, never nuke existing content.
        print(f"WARN: overwriting SKILL.md and README.md in {skill_dir}", file=sys.stderr)

    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)

    if args.router:
        (skill_dir / "workflows").mkdir(exist_ok=True)
        (skill_dir / "assets").mkdir(exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            ROUTER_SKILL_MD.format(name=args.name, author=args.author),
            encoding="utf-8",
        )
        (skill_dir / "workflows" / "example-workflow.md").write_text(
            SAMPLE_WORKFLOW_MD, encoding="utf-8",
        )
        (skill_dir / "README.md").write_text(
            ROUTER_README_MD.format(name=args.name), encoding="utf-8",
        )
        # Multi-platform plugin manifests.
        (skill_dir / ".claude-plugin").mkdir(exist_ok=True)
        (skill_dir / ".claude-plugin" / "plugin.json").write_text(
            CLAUDE_PLUGIN_JSON.format(name=args.name, author=args.author), encoding="utf-8",
        )
        (skill_dir / ".claude-plugin" / "marketplace.json").write_text(
            CLAUDE_MARKETPLACE_JSON.format(name=args.name, author=args.author), encoding="utf-8",
        )
        (skill_dir / ".codex-plugin").mkdir(exist_ok=True)
        (skill_dir / ".codex-plugin" / "plugin.json").write_text(
            CODEX_PLUGIN_JSON.format(name=args.name, author=args.author), encoding="utf-8",
        )
        (skill_dir / ".cursor-plugin").mkdir(exist_ok=True)
        (skill_dir / ".cursor-plugin" / "plugin.json").write_text(
            CURSOR_PLUGIN_JSON.format(name=args.name), encoding="utf-8",
        )
    else:
        (skill_dir / "references").mkdir(exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            SKILL_MD.format(name=args.name, author=args.author),
            encoding="utf-8",
        )
        (skill_dir / "README.md").write_text(
            README_MD.format(name=args.name),
            encoding="utf-8",
        )

    # Informational .gitignore (skills live in git often)
    (skill_dir / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n.DS_Store\n",
        encoding="utf-8",
    )

    shape = "router + workflows" if args.router else "single-file"
    print(f"created: {skill_dir}  ({shape})")
    print(f"next steps:")
    print(f"  1. Edit {skill_dir}/SKILL.md — replace all TODOs, especially frontmatter description")
    if args.router:
        print(f"  2. Edit {skill_dir}/workflows/example-workflow.md (rename it) and add more workflows")
        print(f"     Keep the Workflow Index in SKILL.md in sync with workflows/")
        print(f"  3. Fill in the plugin manifests (.claude-plugin / .codex-plugin / .cursor-plugin)")
    else:
        print(f"  2. Edit {skill_dir}/README.md — fill in options table, usage")
        print(f"  3. (Optional) Run baseline subagent test BEFORE finalizing body")
    print(f"  4. python scripts/lint_skill.py {args.name} --dest {args.dest}")
    print(f"  5. python scripts/bump_version.py {args.name} --dest {args.dest} --type patch -m 'initial scaffold'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
