# Trellis Intake And Full

Use this reference when Yunxiao items should become Trellis work tasks instead
of being handled as ad hoc Yunxiao-only implementation work.

## Intent

There are two Trellis strategies under the normal mode names:

- `trellis-intake`: create or update Trellis tasks from Yunxiao evidence, then
  stop.
- `full` in a Trellis repo: first drain all creatable Yunxiao items into
  Trellis tasks, then execute the created Trellis task queue through the normal
  Trellis workflow and perform configured writeback/marking.

Plain intake is a planning/import flow:

```text
query Yunxiao -> read evidence/images -> split/group -> create Trellis tasks -> stop
```

`full` in a Trellis repo is an end-to-end orchestration flow:

```text
query/enrich/split/create loop until no creatable items remain
-> execute created Trellis tasks one by one
-> validate/commit/write back per source Yunxiao item
-> report
```

Do not stop `full` in a Trellis repo merely because one Trellis task was created,
one Trellis task was implemented, one bounded query page was consumed, or
`runtime_limits.stop_after_code_change` is true. That setting applies only to
direct non-Trellis Yunxiao processing.

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
`task.py create`, create tasks in `planning` during the intake phase. In
`full` in a Trellis repo, start and execute those tasks only after the
intake-drain phase has no remaining creatable Yunxiao items.

## Bounded Intake Rounds

Use project-config limits or these defaults:

- `query_page_size`: 5
- `max_enrich_per_round`: 3
- `max_trellis_tasks_per_round`: 5

These are per-round limits, not total-run limits.

For `trellis-intake`, stop after the requested bounded set unless the user asks
to continue.

For `full` in a Trellis repo, repeat bounded intake rounds automatically:

1. Query one bounded page.
2. Enrich up to `max_enrich_per_round`.
3. Create or update up to `max_trellis_tasks_per_round`.
4. Record source keys in the intake ledger.
5. Query again with the same filters.
6. Stop intake only when no remaining item can become a Trellis task, all
   remaining items are explicitly uncreatable/postponed, Yunxiao/tooling fails,
   or the user interrupts.

Skip keys already imported in the current run if Yunxiao status lag makes them
reappear.

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
or epic task. Do not run `task.py start` during the intake-drain phase. In
`full` in a Trellis repo, run `task.py start` only after the final intake query
confirms there are no more creatable Yunxiao items.

When multiple tasks are created, the Trellis active-task pointer may point at
the last created task. Keep an explicit ordered queue and do not rely on the
active pointer alone.

## Full Execution In Trellis Repos

After intake-drain completes, execute the created Trellis task queue in a stable
order:

1. Pick the first not-yet-executed Trellis task from the queue.
2. Follow `.trellis/workflow.md` for that task:
   - ensure `prd.md` and context are complete;
   - run `task.py start <task-dir>`;
   - execute through the normal Trellis implementation/check/update-spec/commit
     flow;
   - finish/archive or otherwise mark the Trellis task according to the local
     workflow.
3. Validate the implementation at the level required by the task.
4. Write back to the source Yunxiao item(s) only after the Trellis task's code
   work and validation pass.
5. Record the Trellis task outcome and Yunxiao writeback outcome in the ledger.
6. Continue with the next created Trellis task until the queue is exhausted or a
   validation/repo/Yunxiao write failure blocks safe progress.

Do not execute Trellis tasks before intake-drain completes. This prevents one
implemented task from stopping a run that still has more Yunxiao items to import.

If multiple Yunxiao items map to one Trellis task, write back each source item
separately and truthfully. If one Trellis task cannot fully satisfy a source
item, leave that source item unmodified or blocked with an explicit reason.

## Yunxiao Writeback

For `trellis-intake`, default is to leave Yunxiao unchanged.

Only write a Yunxiao comment during intake if the user explicitly requests it.
If a comment is requested, it must be a no-code/intake comment and must not say
the item is fixed.

For `full` in a Trellis repo, writeback happens after each Trellis task is
implemented and validated:

- render comments with `scripts/render_comment.py`;
- do not write done comments for source items that were only imported but not
  implemented;
- apply the configured non-terminal post-implementation status when allowed;
- update any local Trellis task status/marker according to `.trellis/workflow.md`;
- never move Yunxiao to terminal/final status unless explicitly requested.

## Final Report

Report:

- selected mode: `trellis-intake` or `full` with Trellis strategy
- source query/filter
- created or updated Trellis task paths
- source Yunxiao keys mapped to each task
- local image paths saved
- for `full` in a Trellis repo, executed Trellis task outcomes and commits
- for `full` in a Trellis repo, Yunxiao comment/status writeback outcomes per
  source key
- postponed/unmodified items and reasons
- remaining blockers, if the full queue was not exhausted
