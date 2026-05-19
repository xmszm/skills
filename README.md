# Skills

This repository stores reusable Codex skills maintained outside individual
product repositories.

## Layout

- `yunxiao-workitem/`: Yunxiao work item processing workflow, scripts, and
  references.

## Conventions

- Keep global reusable workflow rules in each skill directory.
- Keep project-specific IDs, owners, and validation commands in project-local
  config files inside the product repository.
- Prefer script-backed deterministic behavior for comment rendering, config
  generation, and evidence extraction.
- Add tests for every script that parses or renders structured data.

