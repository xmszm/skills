# Trellis Intake

Use this reference when Yunxiao items should become Trellis work tasks instead
of being implemented directly. This is the default meaning of `trellis full`.

## Intent

Trellis intake is a planning/import flow:

```text
query Yunxiao -> read evidence/images -> split/group -> create Trellis tasks -> stop
```

It is not a code-execution flow. Do not edit product code, run implementation
agents, write "done" Yunxiao comments, or update Yunxiao statuses.

## Preconditions

Load these files when present:

- `.trellis/workflow.md`
- `.trellis/config/yunxiao-workitem.json`
- `AGENTS.md`

Confirm the repo has Trellis task tooling, usually:

```bash
python3 ./.trellis/scripts/task.py create "<title>" --slug <slug>
```

If `.trellis/workflow.md` says that implementation work must start from
`task.py create`, follow that flow and leave created tasks in `planning`.

## Bounded Intake

Use project-config limits or these defaults:

- `query_page_size`: 5
- `max_enrich_per_round`: 3
- `max_trellis_tasks_per_round`: 5

For `trellis full`, repeat bounded intake rounds only when the user asks to keep
importing. A single round should produce clear Trellis tasks rather than a large
unreviewed backlog.

## Evidence Collection

For each candidate:

1. Query a list with `includeDetails=false`.
2. Fetch detail and comments only for selected candidates.
3. Extract rich-text image manifests for descriptions and relevant comments.
4. Download embedded images through `get_workitem_file` and store them under a
   stable Trellis workspace path, for example:
   `.trellis/workspace/yunxiao-images/<KEY>/<image-name>.png`.
5. Inspect images needed to understand the requirement.
6. Postpone video-evidence items and do not create implementation tasks from
   unsupported video-only evidence unless the PRD explicitly says evidence is
   incomplete.

## Splitting Rules

Create one Trellis task per independently implementable work package.

Split when:

- Yunxiao item covers unrelated pages/modules.
- Frontend and backend/API work have separate owners or acceptance paths.
- A screenshot describes one UI defect while comments describe a different
  reopened issue.
- Verification paths differ.

Group when:

- Multiple Yunxiao items share the same module, root cause, and verification
  path.
- One code change can satisfy all grouped items without hiding separate
  acceptance criteria.

If grouping is title/comment-based rather than a formal Yunxiao relation, say
it is a candidate group, not an official relation.

## Trellis Task Shape

For each created task, write or update `prd.md` with:

- Source Yunxiao key(s), title(s), and URL/ID when available.
- Latest relevant comment summary.
- Local image paths and what each image proves.
- Current problem.
- Expected result.
- Scope and affected package/module.
- Acceptance criteria.
- Out-of-scope items.
- Open questions or missing evidence.

Use `task.py create` with `--parent` when creating child tasks under an intake
or epic task. Do not run `task.py start` during intake; the normal Trellis
planning workflow starts after intake.

When multiple tasks are created, the Trellis active-task pointer may point at
the last created task. In the final response, explicitly list the recommended
first task to continue and do not rely on the active pointer alone.

## Yunxiao Writeback

Default: leave Yunxiao unchanged.

Only write a Yunxiao comment during intake if the user explicitly requests it.
If a comment is requested, it must be a no-code/intake comment and must not say
the item is fixed.

## Final Intake Report

Report:

- selected mode: `trellis-intake`
- source query/filter
- created or updated Trellis task paths
- source Yunxiao keys mapped to each task
- local image paths saved
- postponed/unmodified items and reasons
- recommended next Trellis task to start

