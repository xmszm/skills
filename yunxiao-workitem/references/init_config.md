# Init And Project Config

Use this reference for `$yunxiao-workitem init` or explicit project-config
bootstrap/update requests.

## Contract

- Create or update the project-local config at
  `.trellis/config/yunxiao-workitem.json`.
- Discover project IDs, status IDs, owner mappings, validation commands, runtime
  limits, and repository rules.
- Do not process work items, edit product code, update Yunxiao statuses, or
  write Yunxiao comments.
- If a config already exists, treat it as authoritative and patch only requested
  missing or stale fields.

## Discovery Flow

1. Inspect local context:
   - `AGENTS.md`
   - `.trellis/`
   - existing `.trellis/config/yunxiao-workitem.json`
   - package directories and docs that mention Yunxiao IDs or validation
     commands
2. If no config exists, discover or ask for:
   - organization name and `organization_id`
   - project/space name and `project_id`
   - project code, such as `RJJV`
   - work item types to query
   - unfinished, active/in-progress, and terminal status IDs per relevant type
   - owner mapping for backend/API, UI/product, QA/test, and handoff roles
   - production targets and reference-only targets
   - validation commands per package
   - runtime limits for batch/full/trellis-intake
3. Prefer Yunxiao tools for discoverable values:
   - `search_projects` for organization/project selection
   - workflow/status metadata when available
   - a small sample of existing work items only when metadata is unavailable
4. Ask the user before writing config if required values have multiple plausible
   choices or cannot be discovered safely.

## Scripts

Use bundled scripts where possible:

```bash
python3 <skill-dir>/scripts/scan_profile.py --root . --output /tmp/yunxiao-profile.json
python3 <skill-dir>/scripts/init_profile.py --help
python3 <skill-dir>/scripts/init_profile.py --print --project-code RJJV
python3 <skill-dir>/scripts/init_profile.py --config /tmp/yunxiao-profile.json --output .trellis/config/yunxiao-workitem.json
python3 <skill-dir>/scripts/profile_lint.py --config-path .trellis/config/yunxiao-workitem.json
```

Fix `ERROR` lint results before normal work-item processing. Warnings may be
acceptable only when the missing behavior is not needed for the selected mode.

## Recommended Config Fields

Project-specific values belong in the config, not in this global skill:

- `organization_id`, `project_id`, `project_code`
- `owners`
- `work_item_types`
- `statuses`, `unfinished_statuses`, `active_status`
- `production_targets`, `reference_targets`
- `status_policy`, `post_implementation_status`
- `validations`
- `runtime_limits`
- `trellis_intake`

