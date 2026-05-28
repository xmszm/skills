# Yunxiao Comments And Status

Use this reference before writing any Yunxiao comment or status update.

## Comment Discipline

- The comment result must match the actual outcome.
- If no code was changed, do not write `已处理`, `完成度：100%`, or wording that
  implies the defect was fixed.
- Do not include internal review noise, unrelated component checks, transient
  tooling failures, or unrelated implementation details unless the user asks.
- For reopened/recheck items where frontend cannot complete the target, write
  `暂未处理` and state exactly what is missing.
- If the missing piece is an API/backend capability, mention the configured
  backend/API owner when known and use the backend-gap shape.
- Yunxiao rich-text mentions should be sent as the original mention HTML when
  available, for example
  `<span class="sc-jJcwTH fUUHak"><span data-cangjie-key="1666" id="..." data-type="mention" class="sc-cPyLVi jAgzPW">@姓名</span></span>`.
  Store or pass it as `backend_owner_mention_html`, `owner_mentions.backend`,
  or `mentions.backend`; plain `@姓名` is only a fallback. If storing structured
  data instead, keep the Yunxiao identifiers as
  `backend_owner_mention.id`/`backend_owner_mention.data_cangjie_key` or the
  same object under `owner_mentions.backend`/`mentions.backend`; do not invent
  these values.
- If an item was inspected but no code was changed, do not write a Yunxiao
  comment by default. Summarize it in the final response unless the user asks
  for a no-code/blocked comment.
- If an item contains video evidence, do not write a Yunxiao comment. Report it
  only in the final response as postponed.

## Rendering Rule

`scripts/render_comment.py done|blocked|backend-gap` is mandatory for every
skill-written Yunxiao comment.

Before calling `create_work_item_comment`, verify that the prepared text came
from `render_comment.py` in the current run. Send exactly the rendered output.
Do not hand-write, paraphrase, translate, or reformat the final comment.

Done comments require structured fields for:

- requirement
- clarity
- completion
- project
- trigger path
- concrete changes
- changed files
- verification

Blocked comments require structured fields for:

- requirement
- clarity
- result
- project
- trigger path
- missing information/capability

Keep a ledger entry for each comment:

- work item key
- comment kind
- config path or command used to render it
- whether rendered text was sent unchanged

## Trigger Path

`trigger path` means the user-facing product path or visible page section, not
the source file path. Ground it in title/comment/screenshot evidence. When
screenshots are available, prefer the visible UI path from the screenshot. If
the exact product path is not provable, use the narrowest evidence-backed
surface description.

## Status Safety

Changing Yunxiao status is config-driven or user-driven.

- Do not move an item to "已修复", "已完成", "关闭", "Done", "Fixed",
  "Resolved", or any terminal/final state unless the user explicitly says to
  set that exact status.
- A project may configure a post-implementation review status, such as
  "处理中", when the human reviewer needs the item moved after code and comment
  are complete. This is allowed only when the status is non-terminal and the
  item has code changes plus successful verification.
- Attempt post-implementation status updates per item immediately after that
  item's outcome comment is written. Do not accumulate successful items for a
  final pass.
- Do not infer that code changed, build passed, committed, or pushed means the
  item should be marked fixed.
- If Yunxiao rejects the configured transition, leave status unchanged and
  report the rejection.
- If available status IDs are uncertain, do not call `update_work_item`.
- If no code was changed, do not update status by default.
- If an item contains video evidence, never update Yunxiao status.

