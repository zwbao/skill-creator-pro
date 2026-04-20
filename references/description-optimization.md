# Description optimization

The frontmatter `description` is the **only** thing the model uses to decide
whether to load a skill for a given task. It's also the only thing loaded for
every skill in every conversation. So:

1. **Make it accurate** — trigger when it should, skip when it shouldn't.
2. **Make it concise** — burned context for every skill in the index.
3. **Make it focused** — when to use, not what it does.

## The one rule

> **Description = when to use, never what the skill does.**

Testing found that when a description summarizes the workflow ("performs code
review between tasks"), the model follows the *description* instead of
reading the skill body. A skill that required two review passes was
short-circuited to one pass by its own description.

**Fix**: strip workflow verbs and outcomes. Keep only the triggering
conditions.

### Good / bad examples

❌ `"Converts PDFs to markdown with OCR then extracts tables"`
✅ `"Use when converting PDFs to markdown or extracting text/tables from scanned PDFs"`

❌ `"Performs code review by checking specs first and then code quality"`
✅ `"Use when reviewing completed work, implementing major features, or before merging"`

❌ `"Write tests first, then implement, then refactor"`
✅ `"Use when implementing any feature or bugfix, before writing implementation code"`

❌ `"Helps with authentication"` *(too vague)*
✅ `"Use when implementing login flows, handling JWT/session tokens, or debugging auth redirects in React Router"`

## Writing the description

Structure: `"Use when <conditions>. Triggers on <concrete phrases>. <Optional disambiguation>."`

- **Conditions**: what the user is trying to do, observable symptoms, file
  types, environments. Technology-specific if the skill is
  technology-specific; technology-agnostic if the skill is.
- **Trigger phrases**: actual things a user would type — in multiple languages
  if you support them. Include common misspellings or abbreviations.
- **Disambiguation**: if the skill competes with a near-neighbor, say so.
  *"Prefer this over X when Y."*

Keep total length under 800 chars (1024 is the hard limit for the YAML).

## Description optimization loop

For skills shipped to others, iterate the description against a 20-query
eval set programmatically:

1. Split the eval set 60/40 train/test.
2. Evaluate the current description against each query 3× for reliability
   (the model's trigger decision is stochastic; average it).
3. Propose new descriptions with extended thinking based on what failed —
   misfires go into the prompt as counter-examples.
4. Re-evaluate on both splits; iterate up to 5 times.
5. Pick the winner by **test** score (not train) to avoid overfitting to
   the 12-query training sample.

The pipeline is straightforward enough to implement in ~150 lines of Python;
the discipline is in the eval set design and the test-vs-train split, not
in any specific tool.

## Writing good eval queries

The eval set is 20 queries: ~10 should-trigger, ~10 should-not-trigger. The
should-not-trigger queries are the valuable ones — **near-misses, not
obvious unrelated queries**.

### Should-trigger examples (for a PDF→markdown skill)

1. "convert this invoice.pdf to text"
2. "i have a pdf research paper and need the body text as md"
3. "把这个合同pdf变成markdown"
4. "extract the content from this scanned legal doc in my downloads"

### Should-not-trigger near-misses (NOT "write a fibonacci function")

1. "turn this markdown into a pdf" *(opposite direction)*
2. "summarize this pdf" *(summarization, not extraction)*
3. "delete all pdfs in this folder" *(file management)*
4. "convert this word doc to pdf" *(different format, easy to confuse)*

The easy negatives ("write fibonacci") test nothing.

## When you can't run the optimizer

Run a manual 3-query sniff test:
1. Pick one should-trigger phrase you're confident about.
2. Pick one near-miss.
3. Ask a fresh Claude conversation: "Given this description, would you load
   this skill for this user prompt? Why or why not?"

If the answers are wrong, the description is wrong.
