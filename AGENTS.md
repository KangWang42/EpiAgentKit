# Repository Guidelines

## Project Structure & Module Organization

This repository provides shared Claude Code and Codex guidance for epidemiology and biostatistics. `CLAUDE.md` holds cross-task rules; `README.md` covers installation and architecture. Each `skills/` directory is self-contained: keep `SKILL.md` concise, detailed guidance in `references/`, utilities in `scripts/`, and templates or media in `assets/`. Enforcement scripts live in `hooks/`. The allowlist `.gitignore` excludes runtime state, credentials, caches, histories, and local settings.

## Build, Test, and Development Commands

There is no unified build or test runner. Validate the component you changed:

```bash
python skills/skill-creator/scripts/quick_validate.py skills/<skill-name>
bash -n hooks/*.sh
python -m py_compile path/to/changed_script.py
Rscript -e 'parse(file="path/to/changed_script.R")'
python scripts/epiagentkit.py doctor --target all
```

The validator checks skill metadata and structure; the other commands check syntax and installed Claude/Codex parity. Changes to the installer or synchronizer must also pass `python scripts/audit_workflow_contracts.py`, which performs an isolated dual-platform install and idempotency check. Run affected scripts with representative inputs when behavior changes.

## Coding Style & Naming Conventions

Use UTF-8 Markdown, imperative instructions, and descriptive headings. Skill directories use lowercase kebab-case, such as `academic-publishing/`. Every `SKILL.md` starts with YAML fields `name` and `description`. Use four spaces in Python, two in R, and portable Bash with `#!/usr/bin/env bash`. Keep shell files LF-only. Prefer relative paths and reusable scripts over large embedded code blocks.

## Testing Guidelines

There is no central coverage target or test tree. Use validators, syntax checks, and focused execution. Reproduce bugs before fixing them, record verification commands in the pull request, and never use private research data as fixtures.

## Commit & Pull Request Guidelines

Use Conventional Commits: `feat(scope): summary`, `fix(scope): summary`, `docs(scope): summary`, or `refactor(scope): summary`. Make each commit one coherent, reversible unit; use a specific scope and action-object summary, and add a body covering motivation, key behavior, validation, and compatibility for non-trivial changes. After a completed request passes validation, the standing preference is to commit and normally push the current branch without asking again; never force-push or rewrite remote history. Review the entire worktree and do not sweep unexplained pre-existing changes into the commit. Pull requests must explain the problem, affected skills or hooks, verification commands, and compatibility effects. Link issues; include screenshots only for visual or document output.

## Agent-Specific Instructions

Read `CLAUDE.md` before changing domain workflows. Preserve raw data and never guess analytical definitions. Claude Code and Codex share one rule, skill, and hook set; synchronize both runtime homes after changes and verify file parity. Update references and helpers together when a workflow contract changes.
