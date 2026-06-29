# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.5.0] - 2026-06-29

### Added

- Put TEETH on the prompt/script boundary — close the loop-argument gaps (prose→enforcement)
- An adversarial completeness audit (9 Arbor build-logic principles) found 0.4.0 taught the boundary in prose but enforced only the script←judgment direction; a builder could ship a stateful harness with no observe/validate, an LLM writing state.json directly, an auto-filled judgment field, and a write-only failure log, and lint reported GREEN
- prompt-script-boundary.md: add 'The dispatch contract — scope-bound subagents with typed returns' (E) + 'Structured search beats a bigger budget' (H); expand failures to the read-half (F: observe must render pruned reasons); make forcing-function #3 (D) operational (reminder / observe-surfaces-gap / no non-None default); split the smell test into write+read boxes
- lint_skill.py teeth on the judgment←script direction: STATEFUL_HARNESS_NO_OBSERVE_VALIDATE, STATE_DIRECT_WRITE, SUBAGENT_NO_RETURN_CONTRACT, SCRIPT_AUTOFILL_JUDGMENT (all documented in lint-rules.md)
- SKILL.md: expand 'moves to ship' (typed verb set + validate, failure read-half, dispatch contract, structure-over-agents); de-quarantine held-out admit (G) + honest explored-vs-merged reporting (I) into the core EVAL step + 2 rationalization-table rows

## [0.4.0] - 2026-06-29

### Added

- Add the prompt/script boundary doctrine (harness vs brain), distilled from Arbor/HTR
- references/prompt-script-boundary.md: the one-line rule (script = deterministic fn of state; prompt = interpret meaning/assign worth), command-by-command worked example from Arbor's tree.py, three forcing-functions (observe re-projection / validate / split mechanical-write from judgment-write), failures-as-negative-constraints, and a boundary smell test
- SKILL.md: new 'Draw the Prompt/Script Boundary (harness vs brain)' design-decision section + Where-to-go-next pointer
- lint_skill.py: SCRIPT_LLM_CALL (warn — LLM call inside a harness script) + SCRIPT_KEYWORD_JUDGMENT (info — domain judgment frozen as a keyword/tier collection); documented in references/lint-rules.md

## [0.3.0] - 2026-06-01

### Added

- PRD-driven generation + top-50-skills playbook + multi-platform packaging, from researching the most-starred skill repos
- Add references/top-skills-playbook.md: two-schools taxonomy (capability vs discipline), description craft (what+when, never how), progressive-disclosure hard rules, degrees of freedom, anti-patterns catalog, Anthropic pre-ship checklist
- Add references/prd-to-skill.md + SKILL.md PRD-Driven Generation section: ingest/classify -> derive evals from acceptance criteria -> RED/GREEN/lint/bump/package -> report against PRD; includes PRD intake template
- Correct Iron Law #2 doctrine: description = what + when, never how (was 'never what it does'); aligns with Anthropic official shape; fixed in SKILL.md, README, frontmatter-spec
- lint_skill.py: new official-rule checks REF_NESTED (one level deep), REF_NO_TOC (>100-line refs need a TOC), FM_DESC_PERSON (third person); added TOCs to all long references to comply
- shipping-a-skill-library.md: exact .claude-plugin/.codex-plugin/.cursor-plugin + marketplace.json schemas from Anthropic docs + npx skills CLI source, plus install-breaking gotchas
- skill-creator-pro is now itself installable via npx skills add zwbao/skill-creator-pro (added 3 plugin manifests + marketplace.json + CONTRIBUTING.md)

## [0.2.0] - 2026-05-31

### Added

- absorb LLMQuant/skills router+workflows architecture and multi-platform packaging
- Add router + workflows skill shape: decision rule in SKILL.md, references/router-and-workflows.md, templates/SKILL_ROUTER_TEMPLATE.md + WORKFLOW_TEMPLATE.md
- init_skill.py --router scaffolds router SKILL.md + workflows/ + .claude-plugin/.codex-plugin/.cursor-plugin manifests
- lint_skill.py: router checks (ROUTER_DEAD_LINK, ROUTER_WORKFLOW_NOT_INDEXED, ROUTER_NO_INDEX/NO_WORKFLOWS/NO_EVIDENCE_CONTRACT, WORKFLOW_NO_USE_WHEN/NO_OUTPUT/NO_GUARDRAILS/TODO)
- Add Evidence Contract pattern to GREEN body guidance (sources of record / fallback / never-fabricate)
- PACKAGE/SYNC: multi-platform npx skills add + references/shipping-a-skill-library.md (CONTRIBUTING contract, Conventional Commits, bilingual README)
- frontmatter-spec.md: category / input_data_source / router + workflow frontmatter conventions

## [0.1.0] - 2026-04-20

### Added

- Initial release: pro-grade skill lifecycle covering scaffold, baseline testing, evals, lint, semver, CHANGELOG, and description optimization.
- Scripts: `init_skill.py` (scaffold), `lint_skill.py` (audit), `bump_version.py` (semver + CHANGELOG).
- References: frontmatter spec, TDD-for-skills, description optimization, evals and benchmark, lint rules.
