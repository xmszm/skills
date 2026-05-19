---
name: yunxiao-workitem
description: "Handle Yunxiao project collaboration work items across projects, including `$yunxiao-workitem init` project-config bootstrap, scripted config scanning/linting, comment rendering, project configuration discovery, comments/images inspection, clarity scoring, implementation, verification, and outcome-matched comments."
---

# Yunxiao Work Item

Use this skill when the user asks to initialize, query, inspect, process,
continue, fix, comment on, or update Yunxiao project collaboration work items.

## Scope

This is the reusable Yunxiao workflow. Keep common mechanics here and keep
project IDs, workflow status IDs, owner names, package commands, and repository
rules in a project-local JSON config.

Treat this skill as shared infrastructure:

- Keep the global skill responsible for a stable process, data shape, reusable
  scripts, comment rendering, and safety rules.
- Keep project-specific statuses, fields, owner mappings, validation commands,
  reply style, and apply permissions in the project-local config.
- Keep task- or project-specific grouping heuristics in local derived scripts or
  reports first. Promote them into this global skill only after they are proven
  useful across projects.
- Every mode should be reproducible as stages: `query`, `enrich`,
  `normalize`, `analyze`, `report`, and optional `apply`.

Before querying or editing, load project-local instructions when present:

- `AGENTS.md`
- `.trellis/`
- `.trellis/config/yunxiao-workitem.json`
- repo documentation that names Yunxiao organization/project/status IDs

If a project-local Yunxiao JSON config exists, treat it as the project config:

- It supplies organization, project, type, status, owner, and validation
  defaults.
- It may override any rule in this global skill.
- Rules here still apply for anything not explicitly overridden.

Do not hard-code a single project's values in this global skill.

## Modes

This skill has one initialization mode and three runtime modes.

### Initialization Mode

Use this mode for `$yunxiao-workitem init` or explicit bootstrap/update
requests.

- Create or update the project-local Yunxiao config.
- Discover project IDs, status IDs, owner mappings, validation commands, and
  repository rules.
- Do not query implementation batches, edit product code, write Yunxiao
  comments, or update Yunxiao statuses.

### Runtime Mode Selection

When the user asks to process work items, choose exactly one runtime mode before
querying. If the user does not specify a mode, infer the narrowest mode that
matches the request:

- `single`: one exact key/ID, or the user says to handle one item.
- `batch`: a bounded count, sample, page, module, priority slice, or "先做几个".
- `full`: continue until the configured query has no remaining actionable
  items, or the user says "全部", "都做", "直到没有", or equivalent.

Runtime modes share the same item pipeline:

```text
query -> enrich -> normalize -> analyze -> implement/skip -> validate -> comment/status -> commit -> report
```

The write steps are conditional. Only items with code changes and successful
verification should receive done comments, review/in-progress status updates, and
commits, unless the user explicitly requests a different no-code write.

### Single Runtime Mode

Use `single` for one exact work item.

1. Fetch the item detail, comments, attachments, and rich-text image manifest.
2. Inspect the latest relevant comment as the current requirement signal.
3. Inspect required screenshots, rich-text images, and attachments before
   scoring whenever image evidence exists or the text references visual changes.
4. Apply the clarity gate only after steps 2 and 3 are complete. If comment or
   image inspection is still incomplete, the item is not ready for scoring or
   implementation.
5. If actionable, implement, validate, comment, update configured status, and
   commit the related changes.
6. If not actionable, leave Yunxiao unchanged by default and report the reason.
   Low clarity blocks code edits only; it does not justify silently dropping the
   item without a blocked, needs-info, unmodified, or postponed outcome.

Stop condition: the single item has a final outcome of handled, skipped,
blocked, or postponed.

### Batch Runtime Mode

Use `batch` for a bounded run, such as a requested count, one page, one module,
or one priority/status slice.

1. Query the bounded list with `includeDetails=false` first.
2. Enrich candidates one by one or in small groups.
3. Prefer completing clear, small, same-package items first.
4. Group implementation only when items share module, root cause, and
   verification path; still decide and report each work item separately.
5. After each implemented item or cohesive grouped change, validate and commit
   before moving too far ahead.
6. At the end of the bounded set, report handled, unmodified, and postponed
   items.

Stop condition: the requested bounded set is exhausted, not the whole query
space. Do not continue into another page or batch unless the user asked for
`full` mode or explicitly asks to continue.

### Full Runtime Mode

Use `full` when the user wants all matching items completed.

1. Run the same bounded query/enrich/implement loop as `batch`.
2. After each bounded batch completes, query again with the same filters.
3. Skip items already handled in the current run if Yunxiao status lag makes
   them reappear.
4. Keep a run ledger of handled keys, skipped keys and reasons, postponed video
   items, commits, failed status/comment writes, and remaining blockers.
5. Continue until the query returns no remaining actionable items.

Full mode must not stop merely because one bounded batch or page was completed.
It may stop only when:

- no matching items remain;
- all remaining matching items are unmodified/postponed with explicit reasons;
- validation, repository state, or Yunxiao write failures block safe progress;
- the user interrupts or changes scope.

If full mode stops for anything except "no matching items remain", state the
exact stop reason and the remaining keys.

## Explicit Init

This skill follows the generic skill initialization convention:

```text
$<skill-name> init
```

For this skill, use the initialization flow when the user invokes
`$yunxiao-workitem init` or asks to initialize/bootstrap Yunxiao work item
handling for the current repo.

Init creates or updates a project-local Yunxiao JSON config. It does not process
work items, edit product code, update Yunxiao statuses, or write Yunxiao
comments.

Default config path:

```text
.trellis/config/yunxiao-workitem.json
```

### Init Flow

1. Inspect local project context:
   - `AGENTS.md`
   - `.trellis/`
   - existing `.trellis/config/yunxiao-workitem.json`
   - package directories, package manager files, and README/docs that mention
     Yunxiao project IDs or validation commands
2. If a project-local Yunxiao JSON config already exists:
   - Treat it as authoritative.
   - Do not overwrite it wholesale.
   - Patch only missing or stale fields the user asked to refresh.
   - Preserve project-specific overrides.
3. If no config exists, discover or ask for:
   - organization name and `organizationId`
   - project/space name and ID
   - project code, such as `RJJV`
   - work item types to query
   - unfinished, active/in-progress, and terminal status IDs per relevant type
   - owner mapping for backend/API, UI/product, QA/test, and other handoff roles
   - production implementation targets and reference-only folders
   - validation commands per package
   - repository rules such as read-only paths or forbidden sub-agents
4. Draft local repo-derived values with the bundled scanner when useful:
   `python3 <skill-dir>/scripts/scan_profile.py --root . --output /tmp/yunxiao-profile.json`
   - The scanner can infer package targets, validation commands, project code
     hints, repository rules, and documented IDs.
   - Treat scanner output as a draft. Review it before generating config.
   - Status IDs usually require Yunxiao workflow metadata or user confirmation.
5. Prefer Yunxiao tools for discoverable values:
   - use `search_projects` for organization/project selection
   - fetch workflow/status metadata when the tools expose it
   - inspect a small sample of existing work items only to infer labels/statuses
     when workflow metadata is unavailable
6. Ask the user before writing config if any required value has multiple
   plausible choices or cannot be discovered safely.
7. Create the config with the bundled renderer whenever possible:
   `python3 <skill-dir>/scripts/init_profile.py ...`
   - Use `--print` to preview generated JSON.
   - Use `--config <json>` when many values were discovered, so the script
     performs deterministic rendering and the model does not hand-write config.
   - Use `--overwrite` only after reading the existing config and confirming
     replacement is intentional.
   - If the existing config only needs a small patch, edit that JSON field
     directly instead of regenerating the entire file.
8. Validate the generated config:
   `python3 <skill-dir>/scripts/profile_lint.py --config-path .trellis/config/yunxiao-workitem.json`
   - Fix `ERROR` results before normal work item processing.
   - `WARN` results are acceptable only when the missing field is intentionally
     deferred and the corresponding risky action remains disabled.
9. Report:
   - config path
   - values discovered automatically
   - values supplied by the user
   - remaining unknowns
   - whether normal work item processing is now safe

### Init Safety Rules

- Without a project config, status updates are disabled by default.
- Without known status IDs, never call `update_work_item`.
- Without a known project/space ID, do not query broad organization-wide work
  items except as a bounded discovery step.
- Do not put team-private project values into this global skill. Write them to
  the project-local JSON config.
- Do not create project-local Yunxiao skills. The current format is the JSON
  config at `.trellis/config/yunxiao-workitem.json`.

### Init Script

Bundled scripts:

```text
scripts/scan_profile.py
scripts/init_profile.py
scripts/profile_lint.py
scripts/extract_rich_text_manifest.py
scripts/render_comment.py
```

Useful invocations:

```bash
python3 /path/to/yunxiao-workitem/scripts/scan_profile.py --root . --output /tmp/yunxiao-profile.json
python3 /path/to/yunxiao-workitem/scripts/init_profile.py --help
python3 /path/to/yunxiao-workitem/scripts/init_profile.py --print --project-code RJJV
python3 /path/to/yunxiao-workitem/scripts/init_profile.py --config /tmp/yunxiao-profile.json --output .trellis/config/yunxiao-workitem.json
python3 /path/to/yunxiao-workitem/scripts/profile_lint.py --config-path .trellis/config/yunxiao-workitem.json
python3 /path/to/yunxiao-workitem/scripts/extract_rich_text_manifest.py --input /tmp/yunxiao-richtext.json --item-key RJJV-56
python3 /path/to/yunxiao-workitem/scripts/render_comment.py done --config /tmp/yunxiao-comment.json
```

`init_profile.py` supports deterministic field flags such as `--organization`,
`--organization-id`, `--project`, `--project-id`, `--project-code`,
`--work-item-types`, repeated `--status '<type>|<status>|<id>|<meaning>'`,
repeated `--production-target`, repeated `--reference-target`, repeated
`--validation '<package>|<command>'`, and repeated project-rule flags. Run
`--help` for the exact interface before generating config.

`render_comment.py` supports `done`, `blocked`, and `backend-gap` comment
kinds. Use it for every Yunxiao work item comment that this skill writes; the
script output is the canonical comment text.

Reference guides:

- `references/rich_text_images.md`: embedded image extraction, download, cache,
  and validation rules.

## Project Config

Before querying work items, collect these values from the current project
config, user message, or Yunxiao tools:

- `organizationId`
- project/space ID
- project code, if the user references keys such as `RJJV-21`
- work item type IDs, such as Bug, Task, Requirement, or Req
- unfinished status IDs and active/in-progress status IDs
- terminal statuses to exclude, such as closed, fixed, done, canceled, or
  won't-fix
- project owners for backend/API, UI/product, QA/test, or other handoff roles
- production implementation targets and reference-only folders
- package-specific validation commands and runtime automation notes

## Tool Discovery

If Yunxiao MCP tools are not already visible, use tool discovery for
`yunxiao work item`.

Common tools:

- `search_projects`: find project/space information.
- `get_work_item`: fetch full work item detail.
- `list_work_item_comments`: fetch discussion and review comments.
- `get_workitem_file`: fetch work item file metadata and signed download URL.
- `update_work_item`: update status, assignee, priority, fields, or title only
  when allowed by the user request or project config.
- `create_work_item_comment`: add a concise final or blocked comment.

Use code-management tools only for change request comments or repository review
workflows.

## Query Strategy

1. If the user names an exact item key or ID, fetch that item first.
2. Otherwise query assigned unfinished work items in the active Yunxiao project,
   constrained by the selected runtime mode and any user filters.
3. Prefer statuses that mean pending review, pending processing, reopened,
   to-do, or active processing when the user asks to continue.
4. Avoid items already in active processing unless the user explicitly asks for
   them or the project config includes active items in the unfinished set.
5. In `single` mode without an exact item, pick one small clear item first:
   - Prefer narrow UI defects with clear title and screenshot.
   - Avoid starting payment, order-flow, API-contract, permissions, data
     migration, or cross-layer work from title alone.
6. In `batch` mode, respect the requested count/page/slice as the hard boundary.
7. In `full` mode, keep the same filters and re-query after each bounded batch
   until no matching actionable items remain.
8. For unknown workflows, fetch or infer terminal statuses and exclude closed,
   done, fixed, canceled, and won't-fix states.

## Batch Infrastructure Flow

Use this flow when the user asks to process, group, or evaluate multiple work
items:

1. Query a bounded list from project-config or user-supplied filters.
   - For broad batches, start with `includeDetails=false`. Rich-text
     descriptions can inline screenshots, base64 images, or signed image URLs
     and make list responses too large for reliable analysis.
   - Use `includeDetails=true` only for exact items or a small candidate set
     where the description is needed immediately.
2. Enrich only the needed items with detail, comments, attachments, and activity
   history. Prefer a two-pass approach: list first, then details for candidates.
   - Treat comments as a separate enrichment signal. A reopened item may
     already have old completion comments, backend notes, or user clarification;
     do not infer current outcome from status alone.
   - Do not score clarity or choose an implementation path until the latest
     relevant comments have been fetched and read. Missing comment inspection is
     a blocked enrichment step, not permission to skip the item.
   - Treat attachments and rich-text screenshots separately. Attachment APIs may
     return no files even when the description or comments contain embedded
     images.
   - When the requirement, title, comment, or description depends on screenshots
     or other visual evidence, inspect the required images before scoring
     clarity. Missing image inspection is a blocked enrichment step, not
     permission to skip the item.
   - If any required evidence is a video attachment or video embedded in rich
     text, stop processing that item. Do not edit code, write Yunxiao comments,
     or update status for video-evidence items; list them in the final response
     as postponed.
3. Save or keep a raw snapshot when the run is exploratory or script design is
   being evaluated.
4. Normalize every item into a stable internal shape before analysis. Downstream
   reasoning should use normalized fields rather than Yunxiao's raw response
   structure.
5. Analyze for clarity, module, possible root cause, grouping candidates, and
   manual-review needs.
6. Report candidate groups and unmodified items before any write operation.
7. Apply comments or status updates only for items whose code outcome justifies
   it and whose project config/user request allows the write.

Recommended normalized item shape:

```json
{
  "item": {
    "id": "",
    "key": "",
    "title": "",
    "type": "",
    "status": "",
    "priority": "",
    "assignee": ""
  },
  "content": {
    "description_text": "",
    "comments_text": [],
    "attachments": []
  },
  "signals": {
    "clarity_score": null,
    "has_screenshot": false,
    "has_attachment": false,
    "has_video": false,
    "possible_module": "",
    "possible_root_cause": "",
    "candidate_group_key": "",
    "comment_status": "",
    "needs_manual_review": false
  },
  "trace": {
    "raw_files": [],
    "normalized_at": ""
  }
}
```

Batch grouping is advisory by default. Code may be implemented as one grouped
change when items share module, root cause, and verification path, but each work
item must still get its own outcome decision. Items inspected without code
changes remain unmodified and are listed in the final response.

If the Yunxiao tool response does not expose a relation graph, do not claim
items are formally related. Report title/content/comment-based groups as
candidate groups only, and mark items for single handling when their root cause
or verification path differs.

## Work Item Inspection

For each candidate item:

1. Fetch full detail with `get_work_item`.
2. Fetch comments with `list_work_item_comments`.
3. Read title, description, comments, status, assignee, type, priority, and
   referenced pages/modules.
4. Extract user-visible text, image positions, screenshots, and files from
   rich-text fields before deciding clarity.
   - Treat screenshot-visible labels, section headers, tabs, breadcrumbs, and
     dialog titles as the primary evidence for the user-facing target surface.
   - Do not infer the page/module path from a similar code filename, route
     guess, or work item title alone when screenshot evidence points to a
     different UI surface.
5. Confirm whether the latest relevant comment has been inspected and whether
   screenshots or other images are required evidence for the reported problem or
   expected result.
6. If required comment or image evidence has not been inspected yet, stop the
   item at blocked or needs-info. Do not score clarity, do not implement, and
   do not silently skip it.
7. Check normal attachments and rich-text manifests for video files before
   editing. Video evidence is not supported in this workflow; postpone the item
   and leave Yunxiao unchanged.
8. Avoid feeding raw HTML/JSONML or signed URLs back into the model when a
   compact manifest is enough.

### Rich-Text Images

For embedded screenshots, follow `references/rich_text_images.md`. In short:
parse description/comment rich text with `scripts/extract_rich_text_manifest.py`,
extract stable `fileIdentifier` values, fetch image metadata through
`get_workitem_file`, download fresh signed URLs immediately to the manifest
paths, validate local files before using them, and represent screenshots through
a compact manifest instead of raw HTML or signed URLs.

## Clarity Gate

Preconditions before scoring:

- The latest relevant comments have been fetched and inspected.
- Required screenshots, rich-text images, and attachments have been inspected
  when the requirement depends on visual evidence.
- If either precondition is not met, the item is blocked on evidence review and
  is not ready for clarity scoring or implementation.

Score requirement clarity out of 10 only after the preconditions are satisfied:

| Dimension | Points |
| --- | ---: |
| Target project/surface is identifiable | 1.0 |
| Page/module is identifiable | 1.5 |
| Current problem is clear | 1.5 |
| Expected result is clear | 2.0 |
| Evidence exists: screenshot, comment, description, or exact code match | 1.0 |
| Impact scope is small and controlled | 1.0 |
| Data/API dependency is clear, or change is pure UI | 1.0 |
| Acceptance can be judged after implementation | 1.0 |

Rules:

- `> 8`: may implement.
- `6-8`: inspect and ask or comment; edit only if trivial and unambiguous.
- `< 6`: do not edit; request or comment for more information, and record an
  explicit blocked, needs-info, or unmodified outcome.
- A low score blocks code edits only. It does not permit silently dropping the
  item from the run after it has been inspected.
- If payment, checkout, order state, API contracts, permissions, or data
  migrations are involved without a confirmed contract, cap score at `8`.

## Before Editing

Always follow the current repo's development flow:

1. Load the relevant project workflow and coding guidelines before changing
   code.
2. Locate the production implementation target.
3. Treat `*-ui`, mock, demo, and prototype directories as references unless the
   user or project config explicitly says otherwise.
4. Search first before changing any value, style, payload, or route.
5. Preserve unrelated dirty worktree changes.

Before making edits on an item that will be implemented:

1. Do not write a separate "started processing" comment unless the project
   config requires it.
2. Do not move the work item status unless the user request or project config
   explicitly allows it.
3. If the project config requires an active/in-progress status, move only to
   that configured status. If it is already active, keep it there.
4. If the item depends on video evidence, do not start implementation. Leave it
   unchanged and report it as postponed in the final response.

## Implementation Rules

- Keep the edit scoped to the work item.
- Use existing enums/constants for type/status/action fields instead of
  scattered strings. Add a small local enum/constant only when the codebase has
  no suitable existing one.
- Do not hard-code speculative API parameters.
- For UI work, prefer existing styling and component patterns in the target
  project.
- Do not modify generated `dist` output by hand.
- If a frontend task exposes a backend/API gap that blocks the target behavior,
  do not modify backend/API code unless the user explicitly asks and the project
   rules allow it. Add a concise Yunxiao comment for the configured backend/API
  owner instead.
- Backend gap comments should include only: target path, missing capability,
  and the smallest API response/request change needed. Do not propose broad
  alternative designs when a single ID or field is enough.

Backend gap comment shape:

```text
@<backend owner> <work item key> 需要后端补一下。

目标路径：
<frontend path and user action>

缺少功能：
<missing API capability and why frontend cannot complete the target>

建议调整：
<minimal endpoint/request/response change, e.g. return new ID only>
```

## After Editing

1. Run the applicable project check workflow.
2. Run the smallest meaningful validation for the affected package.
3. Decide the verification level before calling the item done, then run the
   required level:
   - Level 0, no requirement-level functional verification: docs/comments only,
     dead-code removal, or a change that cannot affect runtime behavior. Still
     run syntax/lint/build when applicable.
   - Level 1, lightweight verification: small copy, label, spacing, color,
     icon, one-field display, or a narrow conditional render. Compare against
     the Yunxiao screenshot/comment or inspect the exact rendered/code path;
     automation is not required.
   - Level 2, interactive flow verification: form field changes,
     list/detail/drawer/modal behavior, create/edit/delete interactions, API
     payload changes, or data mapping changes. Add or edit at least one
     realistic record through the actual page flow when a local/dev server or
     existing mock/API path makes it possible, and verify affected surfaces such
     as list row, details drawer, edit form, and saved state.
   - Level 3, automated visual or end-to-end verification: new UI structure,
     major layout reconstruction, cross-page workflow, tab/scroll behavior,
     mini-program visual behavior, or screenshot-driven implementation where
     regressions are likely. Use browser/mini-program automation, screenshots,
     or equivalent runtime comparison against the Yunxiao screenshot/reference
     implementation.
   - For API-backed flows at Level 2 or 3, verify the page sends/receives the
     expected existing API payload without silently falling back to mock data.
   - If the required runtime or automation environment is blocked, record the
     blocker and perform the closest deterministic substitute, such as
     typecheck/build plus code-path inspection. Do not silently downgrade; state
     the intended level and performed substitute.
   - When uncertain between two levels, choose the higher level.
4. Apply any project-config status update rule, such as moving the item to the
   configured in-progress status. Never move an item to a terminal/final status
   unless the user explicitly asks for that exact status.
5. If code was changed and verification passed, apply the project-config
   post-implementation review status when one is configured, for example a
   non-terminal status used by the human reviewer. If Yunxiao rejects the
   transition, do not force another status or chain speculative intermediate
   transitions; report the failed target status in the final response.
6. If code was changed for the item, add one concise outcome-matched Yunxiao
   comment.
   - First build a structured comment record with the actual project,
     trigger path, changes, verification level, verification result, and notes.
   - `trigger path` means the user-facing product path or visible page section,
     not the source file path. Ground it in title/comment/screenshot evidence.
   - When screenshots are available, prefer the visible UI path from the
     screenshot over code-path inference. If the exact product path is still not
     provable, use the narrowest evidence-backed surface description, such as
     `后台 > 项目详情 > 核心角色与职责`, instead of guessing a menu path.
   - Keep changed file paths as implementation evidence only. Do not substitute
     them for the user-facing trigger path in the Yunxiao comment.
   - Render the final text with `scripts/render_comment.py done --config ...`
     or equivalent `--set/--list` flags.
   - Send exactly the rendered script output to Yunxiao. Do not hand-write,
     paraphrase, translate, reformat, or "match the style manually".
   - If the comment was not produced by `render_comment.py`, do not call
     `create_work_item_comment` and do not update the work item status.
   - If no code was changed for the item, do not add a Yunxiao comment by
     default unless the user explicitly asks for a no-code/blocked comment.
7. Stage and commit only files related to the item when the user expects
   commits or pushes.

## Yunxiao Comment Discipline

- The comment result must match the actual outcome. If no code was changed, do
  not write `已处理`, `完成度：100%`, or wording that implies the defect was
  fixed.
- Do not include internal review noise such as unrelated component checks,
  "this round did not touch X", or validation commands that do not prove the
  requested outcome.
- Do not add local tooling errors, transient environment failures, or unrelated
  implementation details to Yunxiao comments unless the user explicitly asks.
- For a recheck/reopened item where the frontend cannot complete the target,
  write `暂未处理` and state exactly what is missing.
- If the missing piece is an API/backend capability, mention the configured
  backend/API owner when known and use the backend-gap shape above.
- `核验` for no-code comments must state the actual result, for example
  `结果：未处理，缺少创建后返回客户/档案 ID，前端无法跳转到详情页。`
- Do not create duplicate progress comments. If the comment API cannot update
  existing comments, write only the final concise outcome comment after work is
  done.
- If an item was inspected but no code was changed, do not write a Yunxiao
  comment by default. Summarize it in the final response under an unmodified
  list instead, unless the user explicitly asks to leave a no-code/blocked
  comment.
- If an item was not actionable because comments or required images were missing,
  unread, or still ambiguous after inspection, report that reason explicitly in
  the final response. Do not treat it as silently skipped.
- If an item contains video evidence, do not write a Yunxiao comment even if it
  is blocked or unclear. Report it only in the final response as postponed.
- `scripts/render_comment.py done|blocked|backend-gap` is mandatory for every
  skill-written Yunxiao comment. Treat the script output as the canonical
  template and the only allowed content for `create_work_item_comment`.
- Before calling `create_work_item_comment`, verify that the prepared comment
  text came from `render_comment.py` in the current run. A manually typed
  template-like comment is not acceptable.
- Keep a run ledger entry for each comment with: work item key, comment kind,
  config path or command used to render it, and whether the rendered text was
  sent unchanged.
- Done comments require structured fields for requirement, clarity,
  completion, project, trigger path, concrete changes, changed files, and
  verification.
- Blocked comments require structured fields for requirement, clarity, result,
  project, trigger path, and missing information/capability.

## Status Update Safety Rule

Changing Yunxiao status is config-driven or user-driven:

- Do not move an item to "已修复", "已完成", "关闭", "Done", "Fixed",
  "Resolved", or any terminal/final state unless the user explicitly says to
  set that exact status.
- A project may configure a post-implementation review status, such as
  "待处理", when the human reviewer needs the item moved after code and comment
  are complete. This is allowed only when the status is non-terminal and the
  item has code changes plus successful verification.
- Do not infer that "code changed", "build passed", "committed", or "pushed"
  means the item should be marked fixed.
- If Yunxiao rejects the configured transition, leave the status unchanged and
  report the rejection. Do not guess an alternative review status.
- If the project config requires starting work by status update, move it only
  to the configured active/in-progress status. If it is already active, keep it
  unchanged.
- If available status IDs are uncertain, do not call `update_work_item`; mention
  the uncertainty in the final response.
- If no code was changed for the item, do not update Yunxiao status by default.
  Leave the item unchanged and report it in the final response as unmodified
  unless the user explicitly asks for a status move.
- If an item contains video evidence, never update Yunxiao status in this
  workflow. Leave it unchanged and report it as postponed.

## Final Response

Tell the user:

- The selected mode and whether its stop condition was reached.
- Which Yunxiao items were handled.
- Validation result at package or batch level.
- Yunxiao status/comment update when applicable.
- Which inspected items were left unmodified, with a short reason, when no code
  change was made and the item was intentionally left without Yunxiao
  comment/status updates.
- Which items were postponed because they require video evidence. These items
  must have no Yunxiao comment or status update.

Keep the final response compact and follow project-local reply style when
configured or learned from the user. For batch/full runs, group by project or
package, list each item as `<key> <title> <comment outcome> <status outcome>`,
and include an `未改` section for skipped or blocked items. Do not list changed
file paths unless the user asks for them or a path is needed to explain a
blocker.
