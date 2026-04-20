#!/usr/bin/env python3
"""
Audit a skill against skill-creator-pro conventions + skill-creator + writing-skills best practices.

Usage:
    python lint_skill.py <name>                    # looks in ~/.claude/skills/<name>/
    python lint_skill.py <name> --dest ~/my-skills
    python lint_skill.py --path /abs/path/to/skill
    python lint_skill.py <name> --json

Exit code: 2 if any `error`-severity finding, 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SEVERITIES = ("error", "warn", "info")

# Hard-required YAML frontmatter keys (the minimum that makes a skill valid).
FRONTMATTER_REQUIRED = ["name", "description"]
# Pro-grade recommended (warn if missing).
FRONTMATTER_RECOMMENDED = ["license", "metadata"]
METADATA_RECOMMENDED = ["author", "version", "tags"]

# Phrases that indicate the description is summarizing workflow (anti-pattern).
DESC_WORKFLOW_SMELLS = (
    " then ",
    " next ",
    " finally ",
    " step 1",
    " step one",
    "workflow:",
    "process:",
    "steps:",
    " after that ",
)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Minimal YAML parser — handles flat keys, folded scalars, one-level nesting."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    data: dict = {}
    current_key = None
    buf: list[str] = []
    for line in fm_block.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            if current_key is not None and buf:
                if isinstance(data.get(current_key), str) and data[current_key] == "":
                    data[current_key] = "\n".join(buf).strip()
            current_key = m.group(1)
            val = m.group(2).strip()
            buf = []
            if val in (">", "|", ">-", "|-"):
                data[current_key] = ""
            elif val == "":
                data[current_key] = {}  # nested
            else:
                data[current_key] = val.strip('"').strip("'")
                current_key = None
        elif current_key and line.startswith((" ", "\t")):
            stripped = line.strip()
            m2 = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", stripped)
            if m2 and isinstance(data.get(current_key), dict):
                data[current_key][m2.group(1)] = m2.group(2).strip().strip('"').strip("'")
            else:
                buf.append(stripped)
    if current_key is not None and buf:
        if isinstance(data.get(current_key), str) and data[current_key] == "":
            data[current_key] = "\n".join(buf).strip()
    return data, body


class Linter:
    def __init__(self, skill_dir: Path):
        self.dir = skill_dir
        self.name = skill_dir.name
        self.findings: list[dict] = []

    def add(self, severity: str, code: str, message: str, fix_hint: str = "", file: str = ""):
        self.findings.append({
            "severity": severity,
            "code": code,
            "message": message,
            "fix_hint": fix_hint,
            "file": file,
        })

    # ---- Checks ----

    def check_structure(self):
        if not self.dir.exists():
            self.add("error", "DIR_MISSING", f"Skill directory not found: {self.dir}")
            return
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.dir.name):
            self.add("warn", "DIR_NAME",
                     f"Directory name '{self.dir.name}' is not lowercase kebab-case",
                     "Rename to lowercase letters/numbers/hyphens only")
        if not (self.dir / "SKILL.md").exists():
            self.add("error", "MISSING_SKILL_MD", "SKILL.md is missing",
                     "Run init_skill.py to scaffold", file="SKILL.md")
        # README.md is recommended but not required (keeps parity with official skill-creator minimums).
        if not (self.dir / "README.md").exists():
            self.add("info", "NO_README",
                     "README.md not found — humans browsing the repo benefit from one",
                     "Add a minimal README with install + usage", file="README.md")

    def check_skill_md(self):
        path = self.dir / "SKILL.md"
        if not path.exists():
            return
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        # Required keys
        for key in FRONTMATTER_REQUIRED:
            if key not in fm or not fm[key]:
                self.add("error", "FM_MISSING_REQUIRED",
                         f"frontmatter missing required field '{key}'",
                         f"Add '{key}:' with a real value", file="SKILL.md")

        # Recommended keys
        for key in FRONTMATTER_RECOMMENDED:
            if key not in fm:
                self.add("warn", "FM_MISSING_RECOMMENDED",
                         f"frontmatter missing recommended field '{key}'",
                         f"Add '{key}' for pro-grade skill metadata", file="SKILL.md")

        name = fm.get("name", "") or ""
        if name and name != self.dir.name and name != f"{self.dir.name}":
            # Allow namespaced names like "plugin:skill" if directory is just "skill".
            if ":" not in name:
                self.add("warn", "FM_NAME_MISMATCH",
                         f"frontmatter name '{name}' does not match directory '{self.dir.name}'",
                         f"Set name: {self.dir.name} (or explain the namespace)", file="SKILL.md")

        # Description quality
        desc = fm.get("description", "") or ""
        if isinstance(desc, str) and desc:
            if len(desc) < 80:
                self.add("warn", "FM_DESC_TOO_SHORT",
                         f"description is {len(desc)} chars — likely too thin for reliable triggering",
                         "Add symptoms, concrete trigger phrases, and adjacent-case disambiguation",
                         file="SKILL.md")
            if len(desc) > 1024:
                self.add("warn", "FM_DESC_TOO_LONG",
                         f"description is {len(desc)} chars — the YAML frontmatter has a 1024-char total budget",
                         "Trim the description; move overflow into the body",
                         file="SKILL.md")
            desc_lower = desc.lower()
            if "use when" not in desc_lower and "triggers on" not in desc_lower:
                self.add("warn", "FM_DESC_NO_TRIGGER",
                         "description does not start with 'Use when' and has no 'Triggers on' clause",
                         "Rewrite: 'Use when <conditions>. Triggers on <phrases>.'",
                         file="SKILL.md")
            for smell in DESC_WORKFLOW_SMELLS:
                if smell in desc_lower:
                    self.add("warn", "FM_DESC_WORKFLOW_SUMMARY",
                             f"description appears to summarize workflow (smell: '{smell.strip()}')",
                             "Descriptions must describe WHEN to use, not WHAT the skill does. "
                             "Workflow summaries cause the model to shortcut past the body.",
                             file="SKILL.md")
                    break

        # Metadata nested keys
        meta = fm.get("metadata")
        if isinstance(meta, dict):
            for k in METADATA_RECOMMENDED:
                if k not in meta:
                    self.add("info", "FM_META_MISSING",
                             f"metadata.{k} missing",
                             f"Add metadata.{k}", file="SKILL.md")
            version = meta.get("version", "")
            if version and not re.match(r"^\d+\.\d+\.\d+$", version):
                self.add("warn", "FM_VERSION_FORMAT",
                         f"metadata.version '{version}' is not semver x.y.z",
                         "Use semver format (0.1.0, 1.2.3)", file="SKILL.md")

        # Body checks
        if re.search(r"TODO:\s", body) or "TODO_CN" in body or "TODO_EN" in body:
            self.add("error", "BODY_TODO",
                     "body contains TODO placeholders",
                     "Replace all TODOs with real content", file="SKILL.md")

        line_count = len(body.splitlines())
        if line_count > 500:
            self.add("warn", "BODY_TOO_LONG",
                     f"body has {line_count} lines (>500) — progressive disclosure recommended",
                     "Split long sections into references/ and link from SKILL.md",
                     file="SKILL.md")

        # Interactive skills should either use AskUserQuestion or declare non-interactive.
        has_workflow = "## Workflow" in body or "## workflow" in body.lower()
        mentions_askuser = "AskUserQuestion" in body
        declares_noninteractive = any(
            phrase in body.lower()
            for phrase in ("fully automatic", "non-interactive", "no interactive", "do not ask the user")
        )
        if has_workflow and not mentions_askuser and not declares_noninteractive:
            self.add("info", "BODY_NO_ASKUSER",
                     "workflow does not mention AskUserQuestion — interactive skills should collect options first",
                     "Either call AskUserQuestion or explicitly declare 'fully automatic'",
                     file="SKILL.md")

    def check_scripts(self):
        scripts_dir = self.dir / "scripts"
        if not scripts_dir.exists():
            return
        for py in scripts_dir.glob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            rel = f"scripts/{py.name}"
            if "if __name__" in text and "argparse" not in text:
                self.add("warn", "SCRIPT_NO_ARGPARSE",
                         f"{py.name} is a CLI but does not use argparse",
                         "Add argparse for consistent CLI surface", file=rel)
            if re.search(r"pip install .*--break-system-packages", text):
                if re.search(r"(subprocess\.(run|call|Popen)|os\.system)", text):
                    self.add("info", "SCRIPT_PIP_IN_CODE",
                             f"{py.name} shells out `pip install --break-system-packages`",
                             "Put install guidance in README/SKILL.md, not in code", file=rel)

    def check_changelog(self):
        path = self.dir / "CHANGELOG.md"
        if not path.exists():
            self.add("info", "NO_CHANGELOG",
                     "CHANGELOG.md not found",
                     "Run bump_version.py to create an initial entry",
                     file="CHANGELOG.md")

    def run(self) -> list[dict]:
        self.check_structure()
        self.check_skill_md()
        self.check_scripts()
        self.check_changelog()
        return self.findings


def resolve_skill_dir(name: str, path: str | None, dest: str) -> Path:
    if path:
        return Path(path).expanduser().resolve()
    return (Path(dest).expanduser() / name).resolve()


def format_text(findings: list[dict], skill_dir: Path) -> str:
    if not findings:
        return f"✓ {skill_dir.name}: no issues found\n"
    lines = [f"Lint report for {skill_dir.name}:", ""]
    by_sev = {s: [f for f in findings if f["severity"] == s] for s in SEVERITIES}
    marks = {"error": "✗", "warn": "!", "info": "·"}
    for sev in SEVERITIES:
        for f in by_sev[sev]:
            loc = f" [{f['file']}]" if f["file"] else ""
            lines.append(f"  {marks[sev]} {sev.upper():5} {f['code']:28}{loc}  {f['message']}")
            if f["fix_hint"]:
                lines.append(f"      → {f['fix_hint']}")
    lines.append("")
    lines.append(
        f"Summary: {len(by_sev['error'])} errors, "
        f"{len(by_sev['warn'])} warnings, {len(by_sev['info'])} info"
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a skill against pro-grade conventions")
    ap.add_argument("name", nargs="?", help="Skill name (directory basename)")
    ap.add_argument("--path", help="Absolute path to skill directory (overrides name)")
    ap.add_argument("--dest", default=str(Path.home() / ".claude" / "skills"),
                    help="Parent directory where <name>/ lives (default: ~/.claude/skills)")
    ap.add_argument("--json", action="store_true", help="Output findings as JSON")
    args = ap.parse_args()

    if not args.name and not args.path:
        ap.error("provide a skill name or --path")

    skill_dir = resolve_skill_dir(args.name or "", args.path, args.dest)
    linter = Linter(skill_dir)
    findings = linter.run()

    if args.json:
        print(json.dumps(
            {"skill": skill_dir.name, "path": str(skill_dir), "findings": findings},
            ensure_ascii=False, indent=2,
        ))
    else:
        sys.stdout.write(format_text(findings, skill_dir))

    return 2 if any(f["severity"] == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
