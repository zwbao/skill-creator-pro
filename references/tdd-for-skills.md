# TDD for skills — RED-GREEN-REFACTOR for documentation

**The core insight**: a skill is production documentation that runs tens,
hundreds, or thousands of times. Untested documentation has the same failure
profile as untested code — it works for you, then breaks for someone else in
a way you never imagined.

## Contents

- [The cycle](#the-cycle)
- [RED — pressure scenarios](#red--pressure-scenarios)
- [Pressure types](#pressure-types)
- [GREEN — minimal skill](#green--minimal-skill)
- [REFACTOR — close loopholes](#refactor--close-loopholes)
- [When the baseline succeeds](#when-the-baseline-succeeds)
- [Stopping criteria](#stopping-criteria)

## The cycle

| Phase | For code | For skills |
|-------|----------|-----------|
| RED | Write failing test | Run baseline subagent scenario WITHOUT the skill; watch what goes wrong |
| GREEN | Write minimal code to pass | Write minimal skill addressing those specific failures |
| REFACTOR | Close edge cases | Close new rationalizations surfaced by re-running scenarios |

## RED — pressure scenarios

A pressure scenario is a realistic user prompt that would invoke the skill.
The more realistic, the better. Abstract prompts ("convert this PDF") test
nothing; they're too easy. Specific prompts with personal context, vague
phrasing, and constraints are what reveal failure modes.

**Bad baseline prompt** (tests nothing):
> "Convert this PDF to markdown."

**Good baseline prompt**:
> "ok so my boss sent me this pdf of a lease (it's in my downloads, the file
> has a weird name with brackets) and i need to pull out the rent amount and
> the renewal clause. the thing is it's scanned, not a proper text pdf, and
> half of it is in Chinese. can you get me those two bits?"

The good version tests: OCR vs text extraction, CJK handling, selective
extraction, ambiguous file location.

### Dispatch via Agent tool

```
Use the Agent tool (subagent_type=general-purpose) to run:

Execute this task exactly:
[pressure prompt]

No skill is available for this task. After attempting it, report what you
did, what decisions you made and why, and anything you found tricky.
Report verbatim — do not polish.
```

The "verbatim" ask is essential. Polished reports hide the rationalizations
you need to see.

## Pressure types

Different skills need different pressures:

| Skill type | Pressure |
|-----------|----------|
| **Discipline skill** (TDD, verification) | Time pressure + sunk cost + authority (user insisting) |
| **Technique skill** (condition-waiting) | Variation + missing information |
| **Pattern skill** (flatten-with-flags) | Counter-examples + recognition scenarios |
| **Reference skill** (API docs) | Retrieval + gap testing |

For discipline skills, **combine 3 pressures**. Single-pressure tests are too
easy; models comply. Combined-pressure tests reveal the "just this once"
escape hatch.

## GREEN — minimal skill

Write only what's needed to address the baseline failures. Do not pre-empt
hypothetical failures. The lean skill tests faster and reveals real problems;
the bloated skill teaches you nothing.

Run the same scenarios with the skill present. Expect partial success — the
second-round failures are your next iteration.

## REFACTOR — close loopholes

Every new rationalization goes into two places:

1. **A rule with the *why***: "Do X, because [reason from transcript]."
2. **The rationalization table** at the end of the skill.

Capture excuses verbatim. "I skipped the test because the change is tiny"
goes in the table as-is — don't sanitize it. The raw voice is what future
Claude recognizes.

## When the baseline succeeds

If the subagent nails the task without the skill, the skill is probably
unnecessary. **Tell the user this**. It's a better outcome than shipping
a no-op skill that clutters the description index and slows down every
future conversation.

Exception: the success is luck, not pattern. Run 2 more baselines with
varied phrasings. If it still works, no skill needed. If it fails 1 of 3,
you have something to document.

## Stopping criteria

Stop iterating when:

- Scenarios all pass with the skill and fail without it.
- User feedback (from eval-viewer) is empty.
- You can't articulate what the next improvement would address.

Don't chase asymptotic improvements. A skill that passes 4/5 scenarios is
shippable; the 5th is a future `minor` or `patch` release.
