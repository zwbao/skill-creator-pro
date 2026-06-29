# The Prompt/Script Boundary — harness vs brain

Most non-trivial skills are **two halves**: a deterministic *harness* (scripts,
state files, gates) and a reasoning *brain* (the host model + dispatched
subagents, driven by prompts). The single highest-leverage design decision in
such a skill is **where you draw the line between them** — which steps run as
hardcoded Python and which run as prompt/LLM judgment. Draw it wrong in either
direction and the skill rots: push judgment into Python and it becomes a brittle
keyword-matcher that breaks on the first unanticipated input; push bookkeeping
into the LLM and the state drifts, corrupts, and can't be audited.

This doctrine is distilled from **Arbor / Hypothesis-Tree Refinement** (Jin et
al., 2026, `arXiv:2606.11926`, `github.com/RUC-NLPIR/Arbor`), whose `tree.py`
state manager is the cleanest reference implementation of the boundary in the
wild. Read the `arbor` skill's `scripts/tree.py` if you want the worked code.

## Contents

- [The one-line rule](#the-one-line-rule)
- [The dividing question](#the-dividing-question)
- [Worked example: every command on one side or the other](#worked-example)
- [The script may "decide" — but only on values the world supplied](#script-may-decide)
- [Three forcing-functions the harness owes the brain](#three-forcing-functions)
- [The dispatch contract — scope-bound subagents with typed returns](#the-dispatch-contract)
- [Structured search beats a bigger budget](#structured-search)
- [Failures are durable negative constraints, not deletions](#failures-are-constraints)
- [The boundary smell test](#the-boundary-smell-test)
- [How the boundary shows up across skill shapes](#across-skill-shapes)
- [Lint hooks](#lint-hooks)

<a name="the-one-line-rule"></a>
## The one-line rule

> **Script owns everything that is a deterministic function of existing state**
> — persistence, traversal, projection, integrity checks, and pure comparison of
> values the world/LLM supplied.
> **Prompt owns everything that requires interpreting meaning or assigning
> worth** — forming a claim, judging whether a result is good, deciding what a
> finding *means*, naming the reusable lesson.

The boundary is **not** "hard things → script, easy things → prompt." Classifying
a cancer type is *easy* but it's judgment → prompt. Walking a tree to print it is
*tedious* but it's a pure function of state → script. The axis is **judgment vs.
determinism**, not difficulty.

<a name="the-dividing-question"></a>
## The dividing question

For any step, ask: **"Is the output fully determined by the current state, or
does it require interpreting meaning?"**

| If the step is… | It belongs in… | Because |
|---|---|---|
| Reading/writing the state file | **script** | persistence must be atomic + consistent |
| Walking/filtering/aggregating state | **script** | pure function of inputs |
| Rendering a projection of state for a human/model to read | **script** | deterministic view, no opinion |
| Checking an invariant ("every node has a parent", "every claim has a citation anchor") | **script** | structural truth, decidable |
| Comparing two numbers the LLM/evaluator produced | **script** | `a > b` is not judgment |
| Forming a hypothesis / deciding what to try | **prompt** | open-ended generation |
| Interpreting what a result implies | **prompt** | meaning, not arithmetic |
| Classifying / naming / extracting / routing on natural-language content | **prompt** | judgment under ambiguity |
| Deciding a finding is good enough to ship | **prompt** | worth, not structure |

Two hard invariants fall out of this and are worth stating explicitly, because
violating either is the usual way the boundary erodes:

1. **The script never calls an LLM.** A harness that embeds a model call has
   smuggled judgment into the deterministic layer; now its "validation" is
   itself non-deterministic and unauditable. Keep the model out of the harness;
   put it in a prompt/subagent the harness *invokes around*, not *inside*.
2. **The LLM never writes the state file directly.** It mutates state only
   through the script's typed commands. Every judgment then passes through a
   narrow, validated interface and stays auditable.

<a name="worked-example"></a>
## Worked example: every command on one side or the other

Arbor's `tree.py` owns a hypothesis tree; the model is the coordinator. Note how
*every* command is deterministic, and the one command that looks like a
"decision" (`merge`) is just a numeric comparison of a score the model supplied:

| Command / step | Side | Why |
|---|---|---|
| `init` / `set-status` / `cycle` | **script** | mint ids, flip status, count — pure bookkeeping |
| `observe` / `status` / `validate` | **script** | render a projection / check invariants — pure functions of state |
| `set-evidence` (write the report) | **script** | persist the strings the model produced |
| `propagate` (append the abstracted lesson) | **script** *writes*, **prompt** *authors* | the script appends; the model decides the wording |
| `prune` (flip subtree + store reason) | **script** | subtree walk; the *reason* came from the model |
| `merge` (`new > old` → promote) | **script** | a pure comparison of two model-supplied scores |
| Ideate / Select / interpret a report / name the insight | **prompt** | all judgment |

The model's verbs are a **small fixed set** (`init observe add-node set-evidence
propagate prune merge cycle status validate` — ten). A tight verb set is a
feature: it makes every state transition enumerable, testable, and auditable.

<a name="script-may-decide"></a>
## The script may "decide" — but only on values the world supplied

The merge gate is the subtle case. The script *does* decide whether to promote a
candidate — but only by comparing `test_score > best_score`, where both numbers
were produced by the model/evaluator, not by the script. That is safe. What is
**not** safe is the script encoding domain judgment itself:

- ❌ a hardcoded `CANCER_KEYWORDS = [...]` list the script greps to classify a
  document's cancer type
- ❌ a `TIER_DEFS` dict the script uses to bucket findings into P0/P1/P2
- ❌ a regex the script uses to decide whether a sentence is "a treatment
  recommendation"

Each of these is judgment frozen into code: it will misfire on the first phrasing
you didn't anticipate, and it can't explain itself. The rule: **a script may
branch on a value, but it must not be the thing that *judged* the value.** If a
human would need domain knowledge to produce the value, an LLM (prompt/subagent)
must produce it; the script may then compare or route on it.

This is the same principle as "needs-LLM-judgment tools go through a sub-skill
prompt or a dispatched subagent, never a hardcoded keyword list."

<a name="three-forcing-functions"></a>
## Three forcing-functions the harness owes the brain

The harness's job is not only to do the deterministic work — it is to **make the
brain's judgment reliable, un-skippable, and auditable.** Three moves:

1. **Re-projection (`observe`).** Over a long run the model's context gets
   compressed and its memory of "what we've done" goes lossy. So the harness
   exposes a *read-only command that re-renders the durable state* — objective,
   what's done, what's pending, accumulated lessons, current best. The model
   re-grounds on this projection at the start of each cycle instead of trusting
   its own summary. **Any stateful, multi-step skill should ship an `observe`.**
   The classic failure this prevents: the agent "remembers" it ran the full
   plan, but actually drifted and skipped steps — a deterministic re-projection
   makes the drift visible.

2. **Narrow typed mutation interface + `validate`.** The model changes state
   only through a small set of typed commands, and the harness ships a `validate`
   command that checks invariants and catches a corrupted/inconsistent state
   early. Judgment is forced through a checkable gate.

3. **Split the mechanical write from the judgment write.** Arbor deliberately
   splits `set-evidence` (mechanical: persist the leaf report) from `propagate`
   (judgment: abstract the lesson upward) into **two** commands — and
   `set-evidence` even *prints a reminder* to go do the abstraction. Why split
   what could be one call? Because the abstraction is the **highest-value
   judgment in the whole system** (in Arbor's ablation, a tree *without* this
   insight-propagation scored worse than no tree at all), so it must be done by
   the model, deliberately — never auto-filled by the script. **The deepest move
   here: use hardcoded structure to *force* the LLM to do the judgment, never to
   *replace* it.** The harness's highest purpose is to make judgment
   un-skippable, not to automate it away.

   "Two commands" does **not** by itself make the second one happen. Splitting
   is necessary, not sufficient — make the judgment write actually un-skippable
   with three concrete moves: **(i)** the mechanical-write command prints a
   reminder that *names the still-owed judgment command and the node it applies
   to*; **(ii)** `observe` surfaces any node that has a mechanical result but a
   missing judgment field as a visible gap/warning, so the skipped step shows up
   on the next re-grounding; **(iii)** never give the judgment-field CLI argument
   a non-`None` default, and never derive it from other fields inside the
   mechanical command — a templated or back-filled "insight" is the exact
   no-auto-fill violation, judgment-shaped but judgment-free.

<a name="the-dispatch-contract"></a>
## The dispatch contract — scope-bound subagents with typed returns

The harness/brain boundary recurses: **every subagent you dispatch is itself a
boundary.** When the brain fans work out to executors (parallel reviewers,
research workers, optimization trials), each one needs the same discipline the
top-level harness gives the coordinator — otherwise its output isn't trustworthy
evidence. Two requirements, both from Arbor's `executor-brief.md`:

1. **One fixed scope it MAY NOT redefine.** The subagent gets exactly one
   hypothesis/task. If its first attempt stalls, it repairs its own execution
   and reruns — it does **not** silently swap the task for an easier one. The
   moment a subagent changes its own scope, its return stops being evidence
   about the unit you assigned, and anything you aggregate from it is corrupted.
   (Arbor: "the executor may not change the hypothesis when the metric stalls.")
2. **A tight, typed return contract.** The subagent returns an explicit, fixed
   set of **named fields** — "return EXACTLY these fields; your final message IS
   the data the coordinator parses" — never free-form prose the coordinator then
   has to re-interpret. Arbor's executor returns exactly four: `dev_score`,
   `result`, `insight`, `branch_ref`. Free-prose hand-backs reintroduce judgment
   at the parse step and defeat the boundary.

This is the most common place ambitious skills break: a fan-out skill ships
executors that wander off-task under pressure and return essays. Specify the
scope and the return shape in the dispatch brief. Canonical template:
`arbor/references/executor-brief.md`.

<a name="structured-search"></a>
## Structured search beats a bigger budget (what the harness is FOR)

The reason to build `observe` + insight-propagation + prune-with-reason is not
neatness — it's that **gains come from how the budget is organized, not from
spending more of it.** Arbor's headline result was won at a token budget
*comparable to* single-trajectory baselines (~20–43M); the lift came from
maintaining competing hypotheses, comparing siblings under one parent, and
carrying lessons forward — structure, not sampling.

The design implication for a skill-builder: the harness must make rival
hypotheses **comparable** and **persist the lessons** between them. Do **not**
design the brain to just "spawn N subagents and pick the max" — that pushes the
*cost* lever, not the *structure* lever, and it's exactly the trap a fan-out
default falls into. **If your answer to "make it better" is "spawn more agents,"
you reached for budget when you should have reached for structure.** More agents
with no comparison, no carried lessons, and no frontier is a bigger bill for the
same blind search.

<a name="failures-are-constraints"></a>
## Failures are durable negative constraints, not deletions

When a direction is falsified, Arbor doesn't delete the node — it `prune`s it
*with a recorded reason*. But the write is only half the mechanism; persisting a
reason nothing ever reads is a **write-only failure graveyard**. The constraint
only works if both halves exist:

- **Write half:** the prune/reject command stores the *reason*, not just the
  fact of rejection.
- **Read half:** `observe`/the projection has a **dedicated section that renders
  those pruned reasons**, AND the ideation prompt is explicitly told to treat
  them as dead-ends to avoid. A `prune_reason` field that the projection never
  surfaces is the common, silent failure — the smell-test below splits it into
  two boxes for exactly this reason.

Persisting *why something failed* is often more valuable than persisting what
succeeded. A skill that discards (or buries) its dead ends re-walks them every
run.

<a name="the-boundary-smell-test"></a>
## The boundary smell test

Run this checklist on any skill that has both a `scripts/` harness and LLM steps:

- [ ] **No model call inside a harness/validation script.** (If a script *is* the
      model-driver layer, isolate it from the state/gate scripts and say so.)
- [ ] **No domain judgment frozen as a keyword list / regex / tier-dict** that a
      human would need expertise to author. That work is a prompt/subagent.
- [ ] **The LLM writes state only through typed commands**, never by editing the
      state file directly.
- [ ] **A read-only `observe`/projection command exists** for any multi-step
      stateful run, it renders the full contract (objective / done / pending /
      accumulated lessons / current best / pruned reasons), and the workflow
      tells the model to **re-read it at the start of every cycle**.
- [ ] **A `validate`/invariant command exists** and is run after mutations.
- [ ] **The highest-value judgment is a separate, named, un-skippable step** —
      not a side-effect of a mechanical write, not auto-filled by code (the
      mechanical command reminds; `observe` surfaces the gap; the judgment arg
      has no non-`None` default).
- [ ] **Falsified/rejected results persist WITH their reason** as negative
      constraints (write half), **AND `observe` renders those reasons and the
      ideation prompt conditions on them** (read half) — not a write-only
      graveyard.
- [ ] **Every dispatched subagent has a fixed scope it may not redefine AND a
      typed return contract** (named fields), not a free-prose hand-back.
- [ ] **"Make it better" reaches for structure, not just more agents** —
      competing hypotheses are comparable and lessons are carried, not a blind
      fan-out-and-pick-max.
- [ ] **Gates check structure, not content quality.** A gate may assert "a
      citation anchor is present"; it may **not** assert "the clinical reasoning
      is sound" — that's a subagent reviewer's judgment.

<a name="across-skill-shapes"></a>
## How the boundary shows up across skill shapes

- **Single-file skill, no scripts:** the boundary is trivial — everything is
  prompt. Nothing to do.
- **Skill with deterministic helpers:** the helpers are the harness. Keep them to
  parsing/formatting/validation/IO; don't let one quietly grow a classifier.
- **Router + workflows:** the router is a deterministic dispatcher (a projection
  of "which workflow fits"), but the *routing decision on ambiguous input is
  judgment* — so the router presents options and the model picks; it does not
  hardcode an intent-classifier. The workflows are prompts.
- **Harness/brain skill (engine + plugin):** this is the full case — a Python
  package of state + gates + IO, and a set of prompts/subagents that do all
  reasoning. The package must contain **no model call**; the prompts must contain
  **no state-file writes** except through the package's commands. This split is
  also what lets the two halves version independently.

<a name="lint-hooks"></a>
## Lint hooks

A doctrine with no enforcement is just prose — and the worst failure mode is a
builder who ships a broken boundary and gets a GREEN lint. So `lint_skill.py`
puts **teeth** on both directions of the boundary (see `references/lint-rules.md`):

Guarding **script → judgment** (don't freeze judgment into the harness):

- `SCRIPT_LLM_CALL` (warn) — a file under `scripts/` imports/calls an LLM SDK.
  Harness scripts should be deterministic; move the judgment to a prompt/subagent,
  or, if this genuinely is the model-driver layer, isolate it from the
  state/validation scripts.
- `SCRIPT_KEYWORD_JUDGMENT` (info) — a `scripts/` file holds a large hardcoded
  domain-term collection (KEYWORDS / CATEGORIES / TIERS / TAXONOMY / …) used for
  branching. Likely judgment frozen into code; route it through a prompt/subagent.
- `SCRIPT_AUTOFILL_JUDGMENT` (warn) — a CLI arg named `insight` / `lesson` /
  `abstraction` / `rationale` / `summary` / `takeaway` carries a non-`None`
  default. A judgment field with a default gets auto-filled and skipped (forcing
  -function #3 (iii)).

Guarding **judgment → script** (the model must not own the deterministic layer —
the direction the first cut missed):

- `STATEFUL_HARNESS_NO_OBSERVE_VALIDATE` (warn) — a `scripts/` file persists a
  state file AND defines ≥2 mutating subcommands but ships no read-only
  `observe`/projection and no `validate` invariant-checker. A long run then
  re-grounds on lossy memory and drifts.
- `STATE_DIRECT_WRITE` (warn) — `SKILL.md`/a workflow instructs the LLM to
  edit/write a state `*.json` / `*.yaml` / `*.db` directly. The LLM must mutate
  state only through the harness's typed commands.
- `SUBAGENT_NO_RETURN_CONTRACT` (info) — the body dispatches subagents but
  specifies no typed return contract ("return exactly …" / named fields). Likely
  a free-prose hand-back (the dispatch-contract gap).

These are heuristics — a flag is a prompt to re-examine the boundary, not a
verdict. The doctrine above is the real authority. (H — structured search over
sampling — and G/I honest-reporting are judgment-shaped and live as doctrine +
rationalization-table rows, not lint.)
