# Processing Modes

Use this reference for `single`, `batch`, and non-Trellis `full` work-item
processing.

## Shared Pipeline

```text
query -> enrich -> normalize -> analyze -> implement/skip -> validate -> comment/status -> commit -> report
```

For every implemented work item, `comment/status` is a per-item completion
barrier. After verification passes, render the outcome comment, send it, apply
the configured status update when allowed, and record both outcomes in the run
ledger before moving to the next unrelated item.

Write steps are conditional. Only items with code changes and successful
verification should receive done comments, review/in-progress status updates,
and commits unless the user explicitly requests a different no-code write.

## Query Strategy

1. If the user names an exact item key or ID, fetch that item first.
2. Otherwise query assigned unfinished work items in the active Yunxiao project,
   constrained by selected mode and user filters.
3. Prefer statuses that mean pending review, pending processing, reopened,
   to-do, or active processing when the user asks to continue.
4. Avoid active-processing items unless the user asks for them or project config
   includes active items in the unfinished set.
5. In `single` without an exact item, pick one small clear item first. Prefer
   narrow UI defects with clear title and screenshot. Avoid payment, order-flow,
   API-contract, permissions, data migration, or cross-layer work from title
   alone.
6. In `batch`, respect the requested count/page/slice as a hard boundary.
7. In `full`, keep the same filters and re-query after each bounded round until
   a full stop condition is reached.
8. For unknown workflows, fetch or infer terminal statuses and exclude closed,
   done, fixed, canceled, and won't-fix states.

## Batch Infrastructure

1. Query a bounded list with `includeDetails=false`.
   - Use `includeDetails=true` only for exact items or a small candidate set
     where description is needed immediately.
2. Enrich only needed items with detail, comments, attachments, and activity
   history.
3. Normalize every item into a stable internal shape before analysis.
4. Analyze clarity, module, possible root cause, grouping candidates, and
   manual-review needs.
5. Report candidate groups and unmodified items before any write operation when
   the run is exploratory.
6. Apply comments/status updates only for items whose code outcome justifies it
   and whose project config or user request allows it.

Recommended normalized shape:

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

Batch grouping is advisory by default. Implement as one grouped change only
when items share module, root cause, and verification path. Decide and report
each work item separately.

## Full Mode

`full` is a bounded drain loop, not an unbounded one-shot fetch.

Use the project-config `runtime_limits` or defaults from `SKILL.md`.

For each round:

1. Query one bounded page.
2. Enrich no more than `max_enrich_per_round`.
3. Implement no more than `max_implement_per_round` independent unit.
4. Validate and complete per-item comment/status writeback.
5. Commit related changes if commits are expected.
6. Update the ledger.
7. Stop and report if `stop_after_code_change` is true; otherwise query the
   next bounded page only if it is still safe.

Full may stop only when:

- no matching items remain;
- all remaining matching items are unmodified/postponed with explicit reasons;
- validation, repository state, or Yunxiao write failures block safe progress;
- the user interrupts or changes scope;
- runtime limits require a checkpoint.

If full stops for anything except "no matching items remain", state the exact
stop reason and remaining keys.

## Ledger

Keep a run ledger for `batch` and `full`:

- handled keys
- skipped/unmodified keys and reasons
- postponed video items
- commits
- validation results
- comment/status attempts and failures
- remaining blockers

