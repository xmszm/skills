# Evidence And Clarity

Use this reference before scoring or implementing any Yunxiao item.

## Inspection Steps

For each candidate item:

1. Fetch full detail with `get_work_item`.
2. Fetch comments with `list_work_item_comments`.
3. Read title, description, comments, status, assignee, type, priority, and
   referenced pages/modules.
4. Extract user-visible text, image positions, screenshots, and files from
   rich-text fields before deciding clarity.
5. Confirm whether the latest relevant comment has been inspected.
6. Confirm whether screenshots or other images are required evidence for the
   reported problem or expected result.
7. Check normal attachments and rich-text manifests for video files before
   editing.
8. Avoid feeding raw HTML/JSONML or signed URLs back into the model when a
   compact manifest is enough.

Treat screenshot-visible labels, section headers, tabs, breadcrumbs, and dialog
titles as primary evidence for the user-facing target surface. Do not infer the
page/module path from a similar code filename, route guess, or title alone when
screenshot evidence points to a different UI surface.

## Comments And Images Are Preconditions

Do not score clarity until:

- latest relevant comments have been fetched and inspected;
- required screenshots, rich-text images, and attachments have been inspected
  when the requirement depends on visual evidence.

If either precondition is not met, the item is blocked on evidence review and is
not ready for clarity scoring or implementation.

If any required evidence is a video attachment or video embedded in rich text,
stop processing that item. Do not edit code, write Yunxiao comments, or update
status. Report the item as postponed.

For embedded screenshots, follow `references/rich_text_images.md`.

## Clarity Score

Score requirement clarity out of 10 only after preconditions are satisfied:

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
- Low score blocks code edits only. It does not permit silently dropping an
  inspected item.
- If payment, checkout, order state, API contracts, permissions, or data
  migrations are involved without a confirmed contract, cap score at `8`.

