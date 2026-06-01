# Frontmatter spec

The YAML frontmatter at the top of `SKILL.md` is the only thing always loaded
into Claude's context for every conversation. It's the primary discovery
surface. Keep it rich, but under 1024 chars total.

## Fields

| Field | Required? | Purpose |
|-------|-----------|---------|
| `name` | **yes** | Skill identifier. Lowercase kebab-case. Match the directory name. Namespace via `:` only if the skill belongs to a plugin. |
| `description` | **yes** | When to trigger. See `description-optimization.md`. The only mechanism the model has for deciding to load this skill. |
| `license` | recommended | MIT / Apache-2.0 / proprietary. Makes reuse and distribution unambiguous. |
| `compatibility` | recommended | Requirements that determine if the skill even *can* run (Python version, required tools, MCP servers, OS). |
| `metadata.author` | recommended | Accountability + credit. Useful when a skill misbehaves and someone needs to find who wrote it. |
| `metadata.version` | recommended | Semver. Lets `bump_version.py` + `CHANGELOG.md` work. |
| `metadata.tags` | recommended | Space-separated discoverability keywords. |
| `category` | optional | For grouping skills in indexes — useful when a repo contains many skills, and standard on router skills (`category: options`). |
| `tagline` | optional | One-liner for listings. Distinct from `description` (which is for triggering). |
| `input_data_source` | optional | Router convention: names the source of record the workflows pull from (the frontmatter half of the Evidence Contract). Keep it natural-language, not exact tool names. |

## Router skills

A router `SKILL.md` (one that indexes `workflows/*.md`) uses the same frontmatter
rules with two conventions:

- `description` still describes **when to use the whole category**, never a
  per-workflow summary. The same shortcut failure applies: if the description
  enumerates workflows, the model routes from the description and skips the
  routing rules.
- `category:` is expected, and `input_data_source:` is common, so indexes and
  the Evidence Contract have a stable anchor.

Workflow files (`workflows/*.md`) carry their own lightweight frontmatter —
`name` (human-readable), `description` (the one task), and an optional `pack:`
grouping. They are not separately discoverable; the router loads them. See
`router-and-workflows.md`.

## Minimal valid frontmatter

```yaml
---
name: pdf-to-markdown
description: Use when converting PDF files to markdown, when the user drops a
  PDF and asks for text extraction, or when they mention "convert this pdf",
  "pdf to md", or "extract text from pdf".
---
```

## Full pro-grade frontmatter

```yaml
---
name: pdf-to-markdown
description: Use when converting PDF files to markdown with CJK support.
  Triggers on "convert this pdf", "pdf to md", "extract text from this pdf",
  "把pdf转成markdown". Prefer this skill over generic extraction when the user
  cares about layout preservation or non-Latin text.
license: MIT
compatibility: >
  Requires Python 3.10+ and `pdfplumber` (`pip install pdfplumber`).
  macOS / Linux; Windows untested.
metadata:
  author: zwbao
  version: "0.3.2"
  tags: pdf markdown conversion cjk extraction
---
```

## Common mistakes

1. **Only what, no when** (or only when, no what): Anthropic's official shape is
   `<what it does>. Use when <triggers/keywords>.` — include BOTH. `"Converts
   PDFs to markdown"` lacks the *when*; `"Use when working with documents"`
   lacks specific *what/keywords*. State the capability AND the triggering
   conditions.
2. **Workflow summary in description**: any clause reciting the *steps* ("then...,
   next..., finally...") triggers the shortcut-instead-of-reading failure mode.
   Stating *what* the skill does is fine and required; reciting *how* it works
   is the red line. (what + when, never how.)
3. **Overly abstract description**: `"Use when dealing with documents"` — too
   vague, will misfire or miss.
4. **Mismatched name vs directory**: makes lint fail and breaks some harnesses.
5. **Non-semver version**: breaks `bump_version.py`. Always `x.y.z`.
6. **Description over 1024 chars**: the YAML has a total budget; trim or move
   content to the body.

## When to skip `metadata` entirely

For one-off personal skills that don't need versioning — e.g., a quick
project-specific helper — you can omit `metadata`. The lint will issue a
`warn`, not an error. Accepting the warn is fine; it's a recommendation, not
a hard requirement.
