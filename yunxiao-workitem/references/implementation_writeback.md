# Implementation, Validation, And Reporting

Use this reference after an item passes evidence and clarity gates.

## Before Editing

1. Load the relevant project workflow and coding guidelines.
2. Locate the production implementation target.
3. Treat `*-ui`, mock, demo, and prototype directories as references unless the
   user or project config explicitly says otherwise.
4. Search first before changing values, styles, payloads, or routes.
5. Preserve unrelated dirty worktree changes.
6. Do not write a separate "started processing" comment unless project config
   requires it.
7. Do not move item status unless user request or project config allows it.
8. If the item depends on video evidence, leave it unchanged and report it as
   postponed.

## Implementation Rules

- Keep edits scoped to the work item.
- Use existing enums/constants for type/status/action fields.
- Do not hard-code speculative API parameters.
- For UI work, follow existing styling and component patterns.
- Do not modify generated `dist` output by hand.
- If frontend work exposes a backend/API gap, do not modify backend/API code
  unless the user explicitly asks and project rules allow it. Write a backend
  gap outcome only when no frontend-only fix can complete the item.

Backend gap shape:

```text
<backend owner mention> <work item key> 需要后端补一下。

目标路径：
<frontend path and user action>

缺少功能：
<missing API capability and why frontend cannot complete the target>

建议调整：
<minimal endpoint/request/response change>
```

For Yunxiao rich-text writeback, `<backend owner mention>` should be the exact
mention HTML when available, such as the nested `span` with
`data-type="mention"` and the visible `@姓名`. Plain `@姓名` is only a fallback
when no mention HTML is known. If the mention is stored as structured data, keep
the real Yunxiao `id` and `data-cangjie-key` values with the display name, and
do not invent either value.

## Verification Levels

Run the applicable project check workflow and the smallest meaningful
validation for the affected package.

- Level 0: docs/comments only, dead-code removal, or no runtime behavior impact.
  Still run syntax/lint/build when applicable.
- Level 1: small copy, label, spacing, color, icon, one-field display, or narrow
  conditional render. Compare against screenshot/comment or inspect exact path.
- Level 2: form, list/detail/drawer/modal behavior, create/edit/delete flow,
  API payload, or data mapping. Use a realistic record through the page flow
  when local/dev runtime makes it possible.
- Level 3: new UI structure, major layout reconstruction, cross-page workflow,
  tab/scroll behavior, mini-program visual behavior, or screenshot-driven work
  where regressions are likely. Use browser/mini-program automation,
  screenshots, or equivalent runtime comparison.

For API-backed Level 2 or 3 flows, verify the page sends/receives the expected
existing API payload without silently falling back to mock data.

If runtime automation is blocked, record the blocker and perform the closest
deterministic substitute such as typecheck/build plus code-path inspection. Do
not silently downgrade.

## After Editing

1. Validate.
2. If verification passed, complete the Yunxiao writeback for that item
   immediately when allowed:
   - render one concise outcome-matched comment;
   - send exactly that rendered comment;
   - apply configured post-implementation review status when allowed;
   - record both outcomes in the ledger.
3. If Yunxiao rejects a transition, do not force another status or guess a
   speculative intermediate transition.
4. Stage and commit only files related to the item when commits are expected.

## Final Response

Report:

- selected mode and whether its stop condition was reached;
- handled items;
- validation result;
- Yunxiao comment/status outcomes already attempted per item;
- inspected items left unmodified with short reasons;
- postponed video-evidence items.

For batch/full runs, group by project or package and list each item as
`<key> <title> <comment outcome> <status outcome>`. Include an `未改` section
for skipped or blocked items. Do not list changed file paths unless the user
asks or a path explains a blocker.

