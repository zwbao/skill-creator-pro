#!/usr/bin/env python3
"""
Bump a skill's semver version and prepend a dated entry to CHANGELOG.md.

Source of truth priority:
  1. README.md version badge (if present)
  2. SKILL.md frontmatter metadata.version

Both are updated when they exist.

Usage:
    python bump_version.py <name> --type patch -m "fix wording"
    python bump_version.py <name> --type minor -m "add --verbose" -c "shortcut -v"
    python bump_version.py <name> --set 0.2.0 -m "..."
    python bump_version.py <name> --dest ~/my-skills --type minor -m "..."
    python bump_version.py --path /abs/skill --type patch -m "..." --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path


BADGE_COLOR = "CC785C"  # terracotta
BADGE_RE = re.compile(
    r"!\[Version\]\(https://img\.shields\.io/badge/version-(\d+\.\d+\.\d+)-[A-Za-z0-9]+\)"
)
FM_VERSION_RE = re.compile(r'(\n\s*version:\s*")(\d+\.\d+\.\d+)(")')


def resolve_skill_dir(name: str, path: str | None, dest: str) -> Path:
    if path:
        return Path(path).expanduser().resolve()
    return (Path(dest).expanduser() / name).resolve()


def read_current_version(skill_dir: Path) -> str:
    readme = skill_dir / "README.md"
    if readme.exists():
        m = BADGE_RE.search(readme.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        m = FM_VERSION_RE.search(skill_md.read_text(encoding="utf-8"))
        if m:
            return m.group(2)
    return "0.0.0"


def bump(version: str, kind: str) -> str:
    try:
        major, minor, patch = (int(x) for x in version.split("."))
    except ValueError:
        raise ValueError(f"current version '{version}' is not semver")
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown bump type: {kind}")


def badge_line(version: str) -> str:
    return f"![Version](https://img.shields.io/badge/version-{version}-{BADGE_COLOR})"


def update_readme(skill_dir: Path, new_version: str, dry: bool) -> bool:
    readme = skill_dir / "README.md"
    if not readme.exists():
        return False
    text = readme.read_text(encoding="utf-8")
    new_badge = badge_line(new_version)
    if BADGE_RE.search(text):
        new_text = BADGE_RE.sub(new_badge, text, count=1)
    else:
        # Insert badge right after the first H1.
        lines = text.splitlines()
        out, inserted = [], False
        for line in lines:
            out.append(line)
            if not inserted and line.startswith("# "):
                out.append("")
                out.append(new_badge)
                inserted = True
        new_text = "\n".join(out)
        if not text.endswith("\n"):
            new_text += "\n"
    if new_text != text and not dry:
        readme.write_text(new_text, encoding="utf-8")
    return new_text != text


def update_skill_md_version(skill_dir: Path, new_version: str, dry: bool) -> bool:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False
    text = skill_md.read_text(encoding="utf-8")
    if not FM_VERSION_RE.search(text):
        return False
    new_text = FM_VERSION_RE.sub(rf'\g<1>{new_version}\g<3>', text, count=1)
    if new_text != text and not dry:
        skill_md.write_text(new_text, encoding="utf-8")
    return new_text != text


CHANGELOG_HEADER = """# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

"""


def update_changelog(skill_dir: Path, new_version: str, message: str,
                     changes: list[str], kind: str, dry: bool) -> None:
    path = skill_dir / "CHANGELOG.md"
    today = date.today().isoformat()
    section_title = {"major": "Changed", "minor": "Added", "patch": "Fixed"}.get(kind, "Changed")

    entry_lines = [f"## [{new_version}] - {today}", "", f"### {section_title}", "", f"- {message}"]
    for c in changes:
        entry_lines.append(f"- {c}")
    entry_lines.append("")
    entry = "\n".join(entry_lines) + "\n"

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing.startswith("# Changelog"):
            head_end = existing.find("\n## ")
            if head_end == -1:
                body = existing.rstrip() + "\n\n" + entry
            else:
                body = existing[:head_end].rstrip() + "\n\n" + entry + existing[head_end + 1:]
        else:
            body = CHANGELOG_HEADER + entry + existing
    else:
        body = CHANGELOG_HEADER + entry

    if not dry:
        path.write_text(body, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Bump version + update CHANGELOG for a skill")
    ap.add_argument("name", nargs="?", help="Skill name (directory basename)")
    ap.add_argument("--path", help="Absolute path to skill directory (overrides name)")
    ap.add_argument("--dest", default=str(Path.home() / ".claude" / "skills"),
                    help="Parent directory where <name>/ lives (default: ~/.claude/skills)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--type", choices=["patch", "minor", "major"], help="Semver bump kind")
    g.add_argument("--set", dest="set_version", help="Explicit version (e.g. 0.2.0)")
    ap.add_argument("--message", "-m", required=True, help="Primary changelog entry")
    ap.add_argument("--change", "-c", action="append", default=[], help="Additional bullets (repeatable)")
    ap.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = ap.parse_args()

    if not args.name and not args.path:
        ap.error("provide a skill name or --path")

    skill_dir = resolve_skill_dir(args.name or "", args.path, args.dest)
    if not skill_dir.exists():
        print(f"ERROR: skill directory not found: {skill_dir}", file=sys.stderr)
        return 1

    current = read_current_version(skill_dir)
    if args.set_version:
        if not re.match(r"^\d+\.\d+\.\d+$", args.set_version):
            print(f"ERROR: --set value must be semver (got {args.set_version})", file=sys.stderr)
            return 1
        new_version = args.set_version
        kind = "minor"  # default label when manually set
    else:
        try:
            new_version = bump(current, args.type)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        kind = args.type

    print(f"skill:    {skill_dir.name}")
    print(f"current:  {current}")
    print(f"new:      {new_version}")
    print(f"message:  {args.message}")
    if args.dry_run:
        print("(dry run — no files written)")

    readme_changed = update_readme(skill_dir, new_version, args.dry_run)
    skill_md_changed = update_skill_md_version(skill_dir, new_version, args.dry_run)
    update_changelog(skill_dir, new_version, args.message, args.change, kind, args.dry_run)

    print(f"README.md:   {'updated' if readme_changed else 'no change or missing'}")
    print(f"SKILL.md:    {'updated' if skill_md_changed else 'no change or missing'}")
    print(f"CHANGELOG.md: {'would update' if args.dry_run else 'updated'}")
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
