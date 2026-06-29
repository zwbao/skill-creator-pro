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

# Prompt/script boundary (Arbor / HTR doctrine, references/prompt-script-boundary.md):
# a harness script should be a deterministic function of state and must not embed
# an LLM call (that smuggles judgment into the deterministic layer) nor freeze
# domain judgment as a hardcoded keyword/tier collection.
SCRIPT_LLM_CALL_PATTERNS = (
    r"\bimport\s+openai\b",
    r"\bfrom\s+openai\b",
    r"\bimport\s+anthropic\b",
    r"\bfrom\s+anthropic\b",
    r"\bimport\s+litellm\b",
    r"\bfrom\s+litellm\b",
    r"\bimport\s+cohere\b",
    r"\bgoogle\.generativeai\b",
    r"\bfrom\s+google\s+import\s+genai\b",
    r"\bchat[./]completions\b",
    r"\bOpenAI\s*\(",
    r"\bAnthropic\s*\(",
    r"\bollama\b",
    r"api\.minimaxi?\.com",
)
# Names that suggest a collection is being used as a frozen domain classifier.
SCRIPT_JUDGMENT_NAME = re.compile(
    r"^([A-Z0-9_]*("
    r"KEYWORD|KEYWORDS|CATEGOR|CATEGORIES|TIER|TIERS|TIER_DEFS|LABEL|LABELS|"
    r"TAXONOM|SYNONYM|SYNONYMS|CLASSIF|INTENT|INTENTS|ROUTE|ROUTES|CANCER_TYPES"
    r")[A-Z0-9_]*)\s*[:=]\s*[\[{(]"
)

# A CLI arg that holds a JUDGMENT the model is supposed to author. If it carries
# a non-None default it gets auto-filled and skipped — the no-auto-fill violation.
JUDGMENT_ARG = re.compile(
    r"""add_argument\(\s*["']--(insight|lesson|abstraction|rationale|summary|takeaway)["']"""
)
# A stateful harness is one that persists a state file AND exposes mutating
# subcommands. Such a harness must also ship a read-only projection (observe) so
# a long run re-grounds on durable state, not lossy memory.
MUTATING_SUBPARSER = re.compile(
    r"""add_parser\(\s*["'](add|set|write|update|merge|prune|init|create|append|record|remove|delete)[\w-]*["']"""
)
PROJECTION_SUBPARSER = re.compile(
    r"""add_parser\(\s*["'](observe|status|show|render|state|view|list|projection|inspect)[\w-]*["']"""
)
# Body instruction telling the LLM to write a STATE file directly (it must only
# mutate state through the harness's typed commands).
STATE_DIRECT_WRITE = re.compile(
    r"(?i)\b(edit|writ|updat|modif|overwrit)(?:e|es|ing|ed|y|ies)?\s+(?:\w+\s+){0,3}?(\S*\.(?:json|ya?ml|db))\b"
)
DISPATCH_WORDS = ("dispatch", "subagent", "sub-agent", "agent tool", "fan out", "fan-out", "spawn")
RETURN_CONTRACT_WORDS = (
    "return exactly", "report exactly", "typed return", "return contract",
    "named fields", "final message is", "return a structured", "schema",
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
            if re.match(r"(?i)^\s*(i\s|i'll|i can|let me|we'll|we can)\b", desc):
                self.add("info", "FM_DESC_PERSON",
                         "description appears to use first person — use third person",
                         "The description is injected into the system prompt; write it in third person",
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
        is_router = (self.dir / "workflows").is_dir() or "Workflow Index" in body
        if has_workflow and not mentions_askuser and not declares_noninteractive and not is_router:
            self.add("info", "BODY_NO_ASKUSER",
                     "workflow does not mention AskUserQuestion — interactive skills should collect options first",
                     "Either call AskUserQuestion or explicitly declare 'fully automatic'",
                     file="SKILL.md")

    def check_references(self):
        """Anthropic official rules: references exactly one level deep; >100-line refs need a TOC."""
        refs_dir = self.dir / "references"
        if not refs_dir.is_dir():
            return
        # Nested references (>1 level deep) cause partial-read misses.
        for md in refs_dir.rglob("*.md"):
            rel = md.relative_to(self.dir)
            if len(rel.parts) > 2:  # references/<sub>/<file>.md
                self.add("warn", "REF_NESTED",
                         f"{rel} is nested more than one level deep under references/",
                         "Flatten to one level — nested refs get partial-read with head -100 and missed",
                         file=str(rel))
        # >100-line reference files must start with a table of contents.
        for md in sorted(refs_dir.glob("*.md")):
            lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
            if len(lines) > 100:
                head = "\n".join(lines[:50])
                has_toc = bool(re.search(r"(?im)^#+\s*(contents|table of contents)\b", head)) \
                    or len(re.findall(r"\]\(#", head)) >= 3
                if not has_toc:
                    self.add("warn", "REF_NO_TOC",
                             f"references/{md.name} is {len(lines)} lines (>100) but has no table of contents",
                             "Add a '## Contents' TOC at the top so a partial read reveals full scope",
                             file=f"references/{md.name}")

    def check_router(self):
        """Checks specific to router + workflows skills (no-op for single-file skills)."""
        skill_md = self.dir / "SKILL.md"
        if not skill_md.exists():
            return
        text = skill_md.read_text(encoding="utf-8")
        _, body = parse_frontmatter(text)
        workflows_dir = self.dir / "workflows"
        workflow_files = sorted(workflows_dir.glob("*.md")) if workflows_dir.is_dir() else []
        declares_router = "Workflow Index" in body or "Routing Rules" in body

        # Not a router and no workflows/ → nothing to check.
        if not workflow_files and not declares_router:
            return

        # Declared as a router but ships no workflows.
        if declares_router and not workflow_files:
            self.add("warn", "ROUTER_NO_WORKFLOWS",
                     "SKILL.md reads like a router (has Workflow Index / Routing Rules) but workflows/ is empty or missing",
                     "Add workflow files under workflows/, or convert to a single-file skill",
                     file="SKILL.md")
            return

        # Workflow files exist but the router scaffolding is missing.
        if workflow_files and not declares_router:
            self.add("warn", "ROUTER_NO_INDEX",
                     "workflows/ has files but SKILL.md has no 'Workflow Index' / 'Routing Rules'",
                     "Add a Workflow Index table and Routing Rules so the agent loads only one workflow",
                     file="SKILL.md")

        # Filenames referenced in the body (e.g. workflows/foo.md).
        referenced = set(re.findall(r"workflows/([A-Za-z0-9._-]+\.md)", body))
        actual = {p.name for p in workflow_files}

        # Dead links: referenced in body but file missing.
        for ref in sorted(referenced - actual):
            self.add("error", "ROUTER_DEAD_LINK",
                     f"Workflow Index references workflows/{ref} but the file does not exist",
                     "Create the file or fix the link", file="SKILL.md")

        # Orphans: file exists but not referenced in the body.
        for orphan in sorted(actual - referenced):
            self.add("warn", "ROUTER_WORKFLOW_NOT_INDEXED",
                     f"workflows/{orphan} exists but is not linked from SKILL.md — it is invisible to the router",
                     "Add a row to the Workflow Index pointing to it", file="SKILL.md")

        # Evidence Contract is strongly recommended for routers.
        if "Evidence Contract" not in body and "Data Contract" not in body:
            self.add("info", "ROUTER_NO_EVIDENCE_CONTRACT",
                     "router has no Evidence Contract / Data Contract section",
                     "Declare sources of record, fallback, and what the agent must never fabricate",
                     file="SKILL.md")

        # Per-workflow required sections.
        for wf in workflow_files:
            wtext = wf.read_text(encoding="utf-8", errors="replace")
            wlower = wtext.lower()
            rel = f"workflows/{wf.name}"
            if "use when" not in wlower:
                self.add("warn", "WORKFLOW_NO_USE_WHEN",
                         f"{wf.name} has no 'Use When' section",
                         "State the one task this workflow handles", file=rel)
            if "output format" not in wlower and "## output" not in wlower:
                self.add("warn", "WORKFLOW_NO_OUTPUT",
                         f"{wf.name} has no 'Output Format' section",
                         "Add a numbered output format so results are reproducible", file=rel)
            if "guardrail" not in wlower:
                self.add("info", "WORKFLOW_NO_GUARDRAILS",
                         f"{wf.name} has no 'Guardrails' section",
                         "Add the lines you'd most regret omitting", file=rel)
            if re.search(r"TODO:\s", wtext):
                self.add("error", "WORKFLOW_TODO",
                         f"{wf.name} contains TODO placeholders",
                         "Replace all TODOs with real content", file=rel)

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
            self.check_prompt_script_boundary(text, py.name, rel)

    def check_prompt_script_boundary(self, text: str, fname: str, rel: str):
        """Harness scripts should be a deterministic function of state — no LLM
        call inside the deterministic layer, no domain judgment frozen as a
        keyword/tier collection. See references/prompt-script-boundary.md."""
        for pat in SCRIPT_LLM_CALL_PATTERNS:
            if re.search(pat, text):
                self.add("warn", "SCRIPT_LLM_CALL",
                         f"{fname} appears to call an LLM from a harness script",
                         "Harness scripts must be deterministic — move the judgment to a "
                         "prompt/subagent. If this genuinely is the model-driver layer, "
                         "isolate it from the state/validation scripts and say so.", file=rel)
                break
        for line in text.splitlines():
            stripped = line.strip()
            if SCRIPT_JUDGMENT_NAME.match(stripped):
                # Count quoted string literals on/after the assignment as a cheap
                # proxy for "this is a frozen domain vocabulary".
                window = text[text.find(stripped):]
                n_strings = len(re.findall(r"""(['"])(?:(?!\1).){2,}\1""", window[:1500]))
                if n_strings >= 8:
                    self.add("info", "SCRIPT_KEYWORD_JUDGMENT",
                             f"{fname} holds a large hardcoded domain-term collection used for branching",
                             "Domain judgment frozen into code misfires on unseen phrasings — "
                             "route classification/extraction through a prompt or subagent.", file=rel)
                    break

        # no-auto-fill: a judgment-bearing CLI arg with a non-None default.
        for m in JUDGMENT_ARG.finditer(text):
            window = text[m.start():m.start() + 300]
            dm = re.search(r"default\s*=\s*([^,)\n]+)", window)
            if dm and dm.group(1).strip() not in ("None",):
                self.add("warn", "SCRIPT_AUTOFILL_JUDGMENT",
                         f"{fname}: judgment arg --{m.group(1)} has a non-None default",
                         "A judgment field with a default gets auto-filled and the model skips it. "
                         "Leave it default=None (or required); the model must author it deliberately.",
                         file=rel)
                break

        # stateful harness with mutating subcommands but no read-only projection.
        mut = len(MUTATING_SUBPARSER.findall(text))
        proj = len(PROJECTION_SUBPARSER.findall(text))
        persists = ("json.dump(" in text) or bool(re.search(r"write_text\([^)]*json", text))
        if mut >= 2 and persists and proj == 0:
            self.add("warn", "STATEFUL_HARNESS_NO_OBSERVE_VALIDATE",
                     f"{fname} is a stateful harness ({mut} mutating subcommands) with no read-only observe/validate",
                     "A long run re-grounds on lossy memory and drifts. Add an `observe` projection "
                     "(objective/done/pending/lessons/best) + a `validate` invariant-checker; tell the "
                     "workflow to re-read observe each cycle. See arbor tree.py.", file=rel)

    def check_boundary_body(self):
        """Guard the judgment->script direction in prose: the LLM must not be told
        to write state files directly, and dispatched subagents need a typed return
        contract. Scans SKILL.md + workflows/*.md."""
        sm = self.dir / "SKILL.md"
        bodies: list[tuple[str, str]] = []
        if sm.exists():
            bodies.append(("SKILL.md", sm.read_text(encoding="utf-8", errors="replace")))
        wf = self.dir / "workflows"
        if wf.is_dir():
            for f in sorted(wf.glob("*.md")):
                bodies.append((f"workflows/{f.name}", f.read_text(encoding="utf-8", errors="replace")))

        for fname, text in bodies:
            for m in STATE_DIRECT_WRITE.finditer(text):
                fn = m.group(2).lower()
                ctx = text[max(0, m.start() - 60):m.end() + 60].lower()
                if "state" in fn or "state" in ctx:
                    self.add("warn", "STATE_DIRECT_WRITE",
                             f"{fname} instructs the LLM to write a state file directly ({m.group(0).strip()})",
                             "The LLM must mutate durable state ONLY through the harness's typed commands, "
                             "never by editing the state file — else it drifts/corrupts and can't be audited.",
                             file=fname)
                    break

        if sm.exists():
            tl = bodies[0][1].lower()
            dispatches = any(k in tl for k in DISPATCH_WORDS)
            has_contract = any(k in tl for k in RETURN_CONTRACT_WORDS)
            if dispatches and not has_contract:
                self.add("info", "SUBAGENT_NO_RETURN_CONTRACT",
                         "body dispatches subagents but specifies no typed return contract",
                         "Tell each dispatched subagent to return EXACTLY a fixed set of named fields "
                         "(not free prose) and a scope it may not redefine — see the dispatch contract "
                         "in references/prompt-script-boundary.md.", file="SKILL.md")

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
        self.check_references()
        self.check_router()
        self.check_scripts()
        self.check_boundary_body()
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
