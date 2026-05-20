---
name: yunxiao-workitem
description: "Handle Yunxiao project collaboration work items across projects. Use for `$yunxiao-workitem init`, querying or inspecting Yunxiao items, reading comments/images/attachments, creating Trellis tasks from Yunxiao items, implementing one item or a bounded batch, validating, rendering outcome comments, and config-driven status updates."
---

# Yunxiao Work Item

Use this skill to connect Yunxiao work items with local project workflows. Keep
this file as the routing and safety contract. Load only the reference file that
matches the selected mode.

## Reference Map

- Init or config bootstrap: read `references/init_config.md`.
- Trellis intake, especially `trellis full`: read `references/trellis_intake.md`.
- Single/batch/full implementation processing: read `references/processing_modes.md`.
- Evidence, comments, screenshots, rich-text images, and clarity scoring: read
  `references/evidence_clarity.md`; for embedded images also read
  `references/rich_text_images.md`.
- Code changes, validation, commits, final reporting: read
  `references/implementation_writeback.md`.
- Yunxiao comments and status updates: read `references/comment_status.md`.

## Core Split

There are two different jobs:

1. **Trellis intake** creates local Trellis work tasks from Yunxiao evidence.
   It reads Yunxiao items and images, writes Trellis task artifacts, and stops.
   It does not edit product code, write done comments, or update Yunxiao status.
2. **Work-item processing** handles Yunxiao items directly. It inspects one item
   or a bounded set, implements only actionable items, validates, writes the
   outcome comment/status when allowed, commits, and then moves to the next item.

Do not mix these jobs in one mode. If the user says `trellis` together with
`full`, `全部`, `拆分`, `创建任务`, `导入`, or equivalent, select
`trellis-intake`, not implementation `full`.

## Preflight

Before querying or editing, load project-local instructions when present:

- `AGENTS.md`
- `.trellis/workflow.md`
- `.trellis/config/yunxiao-workitem.json`
- repo documentation that names Yunxiao organization/project/status IDs

If `.trellis/config/yunxiao-workitem.json` exists, treat it as authoritative.
It may override this global skill for project IDs, statuses, owner mappings,
validation commands, runtime limits, reply style, and apply permissions.

Do not hard-code one project's IDs or owners in this global skill.

## Mode Selection

Choose exactly one mode before querying.

- `init`: `$yunxiao-workitem init` or explicit bootstrap/update of local config.
- `trellis-intake`: the user wants Yunxiao items turned into Trellis work tasks,
  especially `trellis full`.
- `single`: one exact key/ID, or the user says to handle one item.
- `batch`: a bounded count, page, module, priority slice, or "先做几个".
- `full`: the user explicitly wants all matching Yunxiao items processed without
  Trellis task creation.

If no mode is explicit, infer the narrowest mode. Prefer `single` or `batch`
over `full`.

## Runtime Limits

For any mode that queries multiple Yunxiao items, enforce project-config limits
or these defaults:

```json
{
  "query_page_size": 5,
  "max_enrich_per_round": 3,
  "max_implement_per_round": 1,
  "max_trellis_tasks_per_round": 5,
  "stop_after_code_change": true,
  "full_requires_explicit_confirmation": true
}
```

`full` means repeated bounded rounds, not one large fetch. Query a small page,
enrich a smaller candidate set, complete at most one implementation unit, then
write back and report progress before continuing when `stop_after_code_change`
is true.

## Mode Summaries

### Init

Use only for config/profile bootstrap. Do not query implementation batches,
edit product code, write Yunxiao comments, or update Yunxiao statuses. Follow
`references/init_config.md`.

### Trellis Intake

Use when the user asks Trellis to consume Yunxiao items, including `trellis full`.

Pipeline:

```text
query -> enrich evidence/images -> normalize -> split/group -> create Trellis tasks -> report
```

Stop after creating or updating Trellis task artifacts. Leave Yunxiao unchanged
unless the user explicitly asks for a separate no-code comment. Follow
`references/trellis_intake.md`.

### Single

Fetch one item detail, comments, attachments, and rich-text image manifests.
Inspect the latest relevant comment and required images before clarity scoring.
If actionable, implement, validate, write outcome comment/status when allowed,
and commit. If not actionable, leave Yunxiao unchanged by default and report
the explicit blocked, unmodified, or postponed reason.

### Batch

Process a bounded set. Query with `includeDetails=false`; enrich candidates one
by one or in small groups. Prefer clear, small, same-package items first. Group
implementation only when module, root cause, and verification path match. After
each implemented item or cohesive group, validate, comment/status, and commit
before moving too far ahead.

### Full

Use only for explicit non-Trellis "process everything" requests. Run bounded
batch rounds with the same filters, skip keys already handled in the current
run, and keep a ledger. Full may stop only when no matching items remain, all
remaining items are explicitly unmodified/postponed, a validation/repo/Yunxiao
write failure blocks safe progress, or the user interrupts/changes scope.

## Non-Negotiable Rules

- Read comments before clarity scoring.
- Inspect required screenshots/images before clarity scoring when the text or
  latest comment depends on visual evidence.
- Missing required evidence blocks scoring and implementation.
- Video evidence is out of scope: postpone the item and leave Yunxiao unchanged.
- Low clarity blocks code edits only; it does not permit silent item drops.
- No code change means no done comment and no status update by default.
- A done comment requires code changes plus successful verification.
- Render every skill-written Yunxiao comment with `scripts/render_comment.py`.
- Attempt applicable comment/status writeback per item immediately after that
  item's verification passes; never defer successful writeback to a final sweep.
- Never move an item to terminal/final status unless the user explicitly asks
  for that exact status.
- Preserve unrelated dirty worktree changes.

## Tool Discovery

If Yunxiao MCP tools are not visible, use tool discovery for `yunxiao work item`.

Common tools:

- `search_projects`: find project/space information.
- `get_work_item`: fetch full work item detail.
- `list_work_item_comments`: fetch discussion and review comments.
- `list_workitem_attachments`: fetch normal attachments when available.
- `get_workitem_file`: fetch file metadata and signed download URL.
- `update_work_item`: update status, assignee, priority, fields, or title only
  when allowed by user request or project config.
- `create_work_item_comment`: add a concise rendered final or blocked comment.

Use code-management tools only for change request comments or repository review
workflows.

## Final Response

Tell the user the selected mode, what was handled or created, validation result
when code changed, Yunxiao comment/status outcomes already attempted per item,
and any unmodified/postponed items with short reasons. For Trellis intake, list
created/updated Trellis task paths and source Yunxiao keys; do not imply code
has been implemented.
