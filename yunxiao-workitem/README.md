# yunxiao-workitem

`yunxiao-workitem` is a reusable workflow skill for handling Yunxiao work
items across repositories.

It is designed as shared infrastructure:

- `SKILL.md` defines the runtime process and safety rules.
- `scripts/` contains deterministic helpers for config bootstrap, linting,
  comment rendering, and rich-text image extraction.
- `references/` contains focused reference docs for tricky evidence handling.
- `schema/` defines the intended shape of the project-local config.
- `examples/` contains starter payloads and config examples.
- `tests/` covers the script behavior.

## Current Strengths

- Strong evidence gate for comments, screenshots, and video blocking.
- Good separation between global workflow and project-local config.
- Script-backed comment rendering and config generation.
- Clear mode model: `init`, `single`, `batch`, `full`.

## Current Weak Spots

- `SKILL.md` is long and mixes policy, usage, and operational detail.
- Config shape is only weakly validated by script logic.
- Scripts mostly exchange untyped dicts.
- Comment kinds are still limited relative to the policy described in
  `SKILL.md`.
- No formal release/versioning workflow yet.

## Recommended Next Iteration

1. Split `SKILL.md` into smaller docs without losing the current rules.
2. Make `profile_lint.py` enforce the JSON schema in `schema/`.
3. Extract shared config/work-item models for the Python scripts.
4. Expand `render_comment.py` to support more outcome kinds and required-field
   validation.
5. Add a small run-ledger artifact format for `batch` and `full` runs.

## Local Project Contract

The intended project-local config path remains:

```text
.trellis/config/yunxiao-workitem.json
```

Global skill values must stay generic. Project IDs, owner names, workflow
status IDs, and validation commands belong in the local config.

