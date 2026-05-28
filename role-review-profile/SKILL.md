---
name: role-review-profile
description: Use when Codex needs to interview a target person such as a frontend lead, backend lead, product owner, QA, designer, architect, or operator, then turn their real working judgment into a role-specific AI review profile, readiness checklist, AGENTS.md guidance, or frontend/backend/product handoff review rules through ongoing dialogue.
---

# Role Review Profile

Use this skill to talk with a real target person and extract how they judge work. The output is not a personality prompt. The output is an executable review profile that lets future AI agents review handoffs the way that role actually thinks.

Core idea:

```text
Target person speaks naturally.
Codex asks small, concrete questions.
Codex converts answers into role review rules.
The person corrects the rules until they say: this matches how I judge work.
```

## Operating Mode

Run this as an iterative conversation, not a one-shot form.

- Ask 1-3 focused questions per round.
- Prefer concrete past examples over abstract preferences.
- After each answer, update the review profile draft.
- Show the target person only the parts they can correct naturally.
- Do not ask them to maintain Markdown, JSON, checklists, or status fields.
- Stop when the profile is useful enough for another AI to perform a realistic review.

Use the user's language unless the repository explicitly requires another language.

## Role Boundary

First identify:

```text
Target role:
Target repository or work surface:
What this role reviews:
What this role must not decide:
Main downstream user of the profile:
```

Examples:

- Frontend lead reviews product handoff readiness before implementation.
- Backend lead reviews API/data readiness before implementation.
- Product owner reviews whether a preview matches product intent.
- QA lead reviews whether acceptance criteria are black-box testable.

## Interview Loop

### Round 1: Capture Judgment Anchors

Ask for one recent or imagined work item and how the target person would judge it.

Good questions:

```text
When a product handoff reaches you, what makes you say "we can start"?
What kinds of missing details usually cause frontend/backend rework?
Which vague words do you distrust, such as "real-time", "lightweight", "dashboard", or "workbench"?
What is one example where a handoff looked clear but implementation still diverged?
```

Avoid:

```text
Please define your full review process.
Please list all frontend/backend standards.
Please choose a framework or technical stack.
```

### Round 2: Extract Review Lenses

Translate answers into review lenses. A review lens is a repeatable way the role inspects work.

Frontend review lenses usually include:

```text
Page and route clarity
User-visible state coverage
Flow continuity
Visual density and experience anchors
Empty/loading/error/recovery states
Component and data binding ambiguity
Mobile/desktop behavior if relevant
```

Backend review lenses usually include:

```text
Business object boundaries
State machine completeness
API capability coverage
Async, retry, idempotency, and failure rules
Data ownership and overwrite rules
Permissions and identity assumptions
Integration contract ambiguity
```

Product review lenses usually include:

```text
Primary user goal
MVP boundary
Main flow continuity
Experience anchors
What AI may infer by default
What requires product correction
```

### Round 3: Convert To Rules

For each review lens, write rules in this shape:

```text
Rule:
Why this matters:
What a good handoff includes:
What ambiguity looks like:
What the AI should ask or flag:
What the AI must not decide:
```

Keep rules actionable. Prefer:

```text
Flag "real-time" unless the handoff says stream, polling, refresh interval, or acceptable delay.
```

Over:

```text
Care about real-time behavior.
```

### Round 4: Test Against A Sample Handoff

Use a real or simulated handoff and apply the draft profile.

Output:

```text
Can this role start? yes / partly / no
Top execution ambiguities:
Minimum questions or additions needed:
What the role can safely infer:
What must return to product:
Risk level: low / medium / high
```

Then ask the target person:

```text
Does this review sound like how you would judge it?
What is too strict, too loose, or missing?
```

## Final Artifact

Produce a concise profile that can be copied into a role repository `AGENTS.md`, a readiness-review skill, or a product handoff gate.

Use this structure:

```markdown
# <Role> Review Profile

## Purpose

## Review Scope

## Do Not Decide

## Start/No-Start Judgment

## Review Lenses

## Required Handoff Signals

## Common Ambiguity Triggers

## Minimal Follow-Up Questions

## Output Shape For Reviews

## Example Review
```

For frontend/backend readiness profiles, include this review output shape:

```text
Can start: yes / partly / no
Safe to implement:
Likely divergence points:
Missing minimum signals:
Assumptions I would make if forced:
Questions that must go back to product:
Execution consistency risk: low / medium / high
```

## Quality Bar

A finished role profile is good when:

- Another AI can use it to review a handoff without imitating a fake personality.
- The target person recognizes their judgment in the rules.
- The profile distinguishes product decisions from implementation preferences.
- The profile flags ambiguity that would cause frontend/backend/product divergence.
- The profile asks for the smallest useful clarification, not a questionnaire.

## Guardrails

- Do not turn personal preferences into product requirements.
- Do not let frontend/backend roles choose product direction.
- Do not let product roles choose implementation technology unless it is a business constraint.
- Do not write vague traits such as "senior", "careful", or "experienced" unless they become concrete review behavior.
- Do not ask the target person to review every line of the profile. Ask whether the review output feels right on examples.
- Do not mark a profile complete until it has been tested against at least one sample handoff or scenario.
