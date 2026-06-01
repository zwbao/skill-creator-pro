# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

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
