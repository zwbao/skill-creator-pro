---
name: <kebab-name>
description: Router skill for <domain> workflows. Use when <specific triggering
  conditions>. Triggers on "<phrase 1>", "<phrase 2>", "<中文触发短语>". Routes
  to one named workflow under workflows/ — never inlines the procedure here.
license: MIT
category: <category-slug>
metadata:
  author: <you>
  version: "0.1.0"
  tags: <space-separated>
---

# <Domain> Router

This is the router skill for `<kebab-name>`. It does **not** perform the work
itself — it identifies the user's task, selects the single closest workflow
under `workflows/`, and loads only that file. Everything else stays on disk
until needed (progressive disclosure: a 40-line router beats a 2000-line skill
the model must skim every time).

## Routing Rules

1. Identify the task, the inputs (files, identifiers, scope), the horizon, and
   the requested output shape.
2. Select the single closest workflow from the index below.
3. Open **only** that workflow and the local resources it explicitly references.
4. Honor the Evidence Contract below for every external fact.
5. Report dates, source coverage, stale notices, and missing inputs.

## Workflow Index

| User intent | Workflow |
|---|---|
| <one-line intent the user would actually express> | [`workflows/<workflow-a>.md`](workflows/<workflow-a>.md) |
| <next distinct intent> | [`workflows/<workflow-b>.md`](workflows/<workflow-b>.md) |

> Keep this table the single source of truth. Every file in `workflows/` MUST
> appear here, and every row MUST point to a file that exists. The lint checks
> both directions.

## Evidence Contract

Where ground truth comes from, and what the agent must never invent:

- **Sources of record:** <name the API / DB / files / tools the workflows pull
  from>. Prefer live retrieval when available.
- **Fallback:** if a required input is unavailable, name the exact missing
  input and continue only with retrieved or user-provided evidence.
- **Never fabricate:** <list the value types the agent must not synthesize from
  memory — e.g. quotes, lab values, prices, citations, dosages>. A model
  guessing these is the failure mode this contract exists to prevent.

## Output Requirements

Every workflow response includes, in order:

1. Answer / recommendation
2. Evidence (table with sources + dates)
3. Risks / caveats
4. Data used, including coverage and stale notices
