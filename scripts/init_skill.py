#!/usr/bin/env python3
"""
Scaffold a new skill with skill-creator-pro conventions.

Creates <dest>/<name>/ with SKILL.md (pro frontmatter), README.md (version
badge + install snippet), empty scripts/ and references/ dirs.

Usage:
    python init_skill.py <name>                       # dest defaults to ~/.claude/skills
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

    print(f"created: {skill_dir}")
    print(f"next steps:")
    print(f"  1. Edit {skill_dir}/SKILL.md — replace all TODOs, especially frontmatter description")
    print(f"  2. Edit {skill_dir}/README.md — fill in options table, usage")
    print(f"  3. (Optional) Run baseline subagent test BEFORE finalizing body")
    print(f"  4. python scripts/lint_skill.py {args.name} --dest {args.dest}")
    print(f"  5. python scripts/bump_version.py {args.name} --dest {args.dest} --type patch -m 'initial scaffold'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
