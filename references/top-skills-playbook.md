# Top-skills playbook — what makes a skill top-tier

Distilled from the highest-signal Agent-Skill repos (anthropics/skills incl.
skill-creator + the docx/pdf/xlsx/pptx production skills, obra/superpowers,
and the broader top-50 by GitHub stars) plus Anthropic's official "Skill
authoring best practices". This is the quality bar the PRD→skill pipeline
targets. Sources tagged: [DOCS] official best-practices, [ENG] Anthropic
engineering blog, [SC] skill-creator, [SP] superpowers/writing-skills.

## Contents

- [The two schools — pick one](#the-two-schools--pick-one)
- [The description is the product](#the-description-is-the-product)
- [Progressive disclosure — hard rules](#progressive-disclosure--hard-rules)
- [Degrees of freedom](#degrees-of-freedom)
- [Body craft](#body-craft)
- [Scripts](#scripts)
- [Anti-patterns catalog](#anti-patterns-catalog)
- [The pre-ship checklist](#the-pre-ship-checklist)

## The two schools — pick one

Every top skill is one of two shapes. Classify the skill before writing; do not
blend them incoherently.

| | **Capability / reference school** | **Discipline / process school** |
|---|---|---|
| Examples | pdf, docx, xlsx, pptx, mcp-builder, webapp-testing | TDD, systematic-debugging, brainstorming, writing-skills |
| Optimizes for | *doing a task correctly* | *making the agent comply under pressure* |
| Body is | table-first, ✅/❌ code recipes, script-backed, QA loop | flowchart + Iron Law + rationalization table + red-flags |
| Code | dense, inline + scripts | almost none |
| Trigger style | exhaustive keyword enumeration + `Do NOT` clause | minimal "Use when <moment of temptation>" |
| Verification | mandatory "assume failure" QA loop with fresh-eyes subagent | RED-GREEN-REFACTOR under multi-pressure scenarios |

A PRD that says "extract/convert/generate X" → capability school. A PRD that
says "always/never do X", "enforce Y", "stop the agent from Z" → discipline
school. [SP]

## The description is the product

The `description` is the ONLY text pre-loaded for every conversation; Claude
picks this skill from 100+ candidates using it alone. Triggering accuracy
dominates every other quality lever. [DOCS][ENG]

**Canonical shape:** `<what it does>. Use when <triggers / symptoms / keywords>.`
Encode BOTH what it does and when to use it — third person, ≤1024 chars. [DOCS]

- **Pack recall keywords**: every verb, synonym, file extension (`.xlsx`),
  error string, library, command a user might say. For format skills, name the
  deliverable nouns ("report", "memo", "letter"). [DOCS][SP]
- **Bound precision with a `Do NOT` / `SKIP` clause** naming the near-miss
  skills it competes with. Disambiguate on the **deliverable**, not the
  keyword ("Do NOT trigger when the primary deliverable is a Word doc, even if
  tabular data is involved"). [SP]
- **Be deliberately pushy** — Claude under-triggers. "Use this whenever the
  user mentions X, even if they don't explicitly ask." [ENG][SC]
- **Third person always.** "I can help…" / "You can use…" breaks discovery. [DOCS]
- **NEVER summarize the workflow / steps.** Stating the capability (what) is
  required; reciting the procedure (how — "first…then…finally") makes Claude
  follow the description and skip the body. This is the single most-tested
  failure mode. The line: **what + when, never how.** [SP]

Gold-standard example (docx): enumerate-then-exclude —
> "...create, read, edit, or manipulate Word documents (.docx). Triggers
> include 'Word doc', '.docx'... If the user asks for a 'report', 'memo',
> 'letter'... Do NOT use for PDFs, spreadsheets, Google Docs, or general
> coding tasks."

## Progressive disclosure — hard rules

Three-tier loading: Tier-1 metadata (name+description, always in context) →
Tier-2 SKILL.md body (on trigger) → Tier-3 bundled files (read on demand, zero
cost until read). Scripts are *executed*, not loaded — only stdout costs
tokens. [ENG][DOCS]

- **SKILL.md body < 500 lines.** It is a router/table-of-contents, not the
  detail. [DOCS][SC]
- **References exactly one level deep** from SKILL.md. Nested references
  (SKILL→advanced→details) make Claude partial-read with `head -100` and miss
  content. [DOCS]
- **Any reference file > 100 lines starts with a table of contents** (so a
  partial read still reveals full scope). [DOCS]
- **Name files for discovery**: `form_validation_rules.md`, not `doc2.md`.
  Forward slashes only (cross-platform). [DOCS]
- **Declare execution intent for every file/script**: "Run `x.py`" (execute)
  vs "See `x.py` for the algorithm" (read). [DOCS]
- **Never `@`-force-load links** — they burn context. Use plain relative
  links read on demand. [SP]
- Offload to references when content is **mutually exclusive / rarely used
  together** (domain-split: `reference/finance.md`, `reference/sales.md`). [DOCS]

## Degrees of freedom

Match instruction rigidity to task fragility (robot-on-a-path analogy): [DOCS]

- **High freedom** (prose): many valid approaches, context-dependent (e.g. code
  review). Describe principles.
- **Medium freedom** (parameterized script/pseudocode): a preferred pattern
  with acceptable variation.
- **Low freedom** (exact pinned script): fragile / destructive / consistency-
  critical (DB migration: "Run exactly this script. Do not modify the command
  or add flags.").

## Body craft

- **Concise is a public good.** Assume Claude is smart; add only what it
  doesn't know. Challenge every paragraph: "does this justify its token cost?"
  (Their example: cut "what a PDF is" — 150→50 tokens.) [DOCS]
- **One Core Principle line up top**, bolded for process skills ("If you didn't
  watch the test fail, you don't know if it tests the right thing"). [SP]
- **Quick-reference table early** — let the agent route before reading prose.
  Three uses: routing (`Task | Tool`), spec lookup, persuasion (`Excuse |
  Reality`). [DOCS][SP]
- **Teach with ✅/❌ before-after pairs** + inline `CRITICAL:` callouts at the
  point of use, not in a far-off section. [DOCS]
- **One excellent example, not five languages.** You're good at porting. [SP]
- **Explain the WHY**; reserve all-caps MUST/NEVER for true invariants. For
  discipline skills only, isolate the one inviolable rule as a fenced "Iron
  Law" block. [SC][SP]
- **Consistent terminology** — pick one term, never vary ("field", never
  "box/element/control"). [DOCS]
- **One default + an escape hatch, never a menu** ("Use pdfplumber… for scanned
  PDFs needing OCR, use pdf2image instead"). [DOCS]
- **No time-sensitive info** ("before August 2025"); put deprecated material in
  a collapsed `<details>` "Old patterns". [DOCS]
- **Bake in a verification loop that assumes failure**: "Your first output is
  almost never correct." Generate → fresh-eyes subagent inspects → fix →
  re-verify until a clean pass. [SC]
- For discipline skills: **rationalization table** (`Excuse | Reality`) + **red-
  flags STOP list**, capturing the real excuses from baseline testing, plus
  implementation-intention phrasing ("When X, IMMEDIATELY do Y"). [SP]

## Scripts

- **Bundle a script the moment you'd otherwise rewrite it every run** — more
  reliable, fewer tokens, consistent. Signal: all baseline runs independently
  wrote the same helper. [DOCS][SC]
- **Treat bundled scripts as black boxes**: `--help` first, don't read the
  source (context pollution). Document by one-line purpose + exact invocation. [SP]
- **Solve, don't punt** — handle errors in-script, don't fail to Claude. [DOCS]
- **No voodoo constants** — document every magic number. "If you don't know the
  right value, how will Claude?" [DOCS]

## Anti-patterns catalog

| Anti-pattern | Fix |
|---|---|
| Description summarizes the workflow | what + when only; never the steps [SP] |
| Description in 1st/2nd person | third person (it's injected into system prompt) [DOCS] |
| All-caps MUST with no reason | explain why; LLMs have theory of mind [SC] |
| Menu of options ("pypdf or pdfplumber or PyMuPDF…") | one default + escape hatch [DOCS] |
| Nested references (>1 level deep) | flatten to one level [DOCS] |
| >100-line reference without a TOC | add a TOC at the top [DOCS] |
| Multi-language example dilution | one excellent example, port on demand [SP] |
| Reading scripts into context | black-box, `--help` first [SP] |
| Reading all reference files eagerly | router loads one; "do NOT read all" [SP] |
| Overfitting the skill to its test cases | generalize; it runs a million times [SC] |
| Declaring success on first render | mandatory fix-and-verify cycle [SC] |
| Hardcoding computed values in artifacts | emit live formulas/logic [DOCS] |
| Time-sensitive info in the body | collapsed "old patterns" `<details>` [DOCS] |
| Narrative war-story examples | strip to the generalizable pattern [SP] |
| `@`-force-load links | plain relative on-demand links [SP] |

## The pre-ship checklist

Reproduce Anthropic's official pre-share checklist as a gate. [DOCS][SC][ENG]

- [ ] description: states **what + when**, third person, packed with key terms,
      `Do NOT`/`SKIP` clause if near-miss skills exist, no workflow summary
- [ ] name: lowercase-kebab, ideally gerund (`processing-pdfs`); not
      `helper/utils/tools/data`
- [ ] SKILL.md body < 500 lines; heavy detail in references
- [ ] references exactly one level deep; >100-line refs start with a TOC
- [ ] progressive disclosure used; execution intent declared per file
- [ ] consistent terminology; concrete (not abstract) examples
- [ ] one default + escape hatch (no option menus)
- [ ] no time-sensitive info (or in a collapsed "old patterns")
- [ ] scripts solve-not-punt, no voodoo constants, deps listed/verified
- [ ] forward-slash paths everywhere
- [ ] ≥3 evaluations written from observed real failures (eval-first)
- [ ] tested on the models you ship (Haiku/Sonnet/Opus differ)
- [ ] right school applied (capability vs discipline), not blended
- [ ] no malware/exploit code; untrusted-source skills audited
