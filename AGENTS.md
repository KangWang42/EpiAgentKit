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

## Skill Maintenance

Treat skill improvement as regression-safe optimization, not append-only documentation. Before editing, identify the observed failure or new use case, behaviors that must remain unchanged, the smallest coherent change, and representative old and new evaluations. Classify existing material as keep, rewrite, merge, move, script, or delete before adding rules or files. Keep each concept in one source: global constraints in `CLAUDE.md`, core routing and workflow in `SKILL.md`, conditional detail and examples in `references/`, and repeated deterministic operations in `scripts/`. Prefer the smaller change when two designs pass the same evaluations; remove stale, redundant, conflicting, speculative, or overly project-specific content. Do not trade away existing behavior under the label of simplification unless the user explicitly changes the contract.

## Testing Guidelines

There is no central coverage target or test tree. Use validators, syntax checks, and focused execution. Reproduce bugs before fixing them, record verification commands in the pull request, and never use private research data as fixtures.

## Commit & Pull Request Guidelines

Use Conventional Commits: `feat(scope): summary`, `fix(scope): summary`, `docs(scope): summary`, or `refactor(scope): summary`. Make each commit one coherent, reversible unit; use a specific scope and action-object summary, and add a body covering motivation, key behavior, validation, and compatibility for non-trivial changes. After a completed request passes validation, commit the coherent change automatically unless the user says not to commit, but only when Git is available and the current directory is a repository. If Git is unavailable or the directory is not a repository, skip all Git operations; do not initialize a repository or install Git. Push only when the user explicitly requests it in the current turn; do not ask, remind, or batch-push on the user's behalf. Never force-push or rewrite remote history. Review the entire worktree before committing and do not sweep unexplained pre-existing changes into the commit. Pull requests must explain the problem, affected skills or hooks, verification commands, and compatibility effects. Link issues; include screenshots only for visual or document output.

## Agent-Specific Instructions

Use `epiagentkit-maintenance` for changes to this repository's rules, skills, hooks, scripts, synchronization contracts, or maintenance documentation. Read `CLAUDE.md` before changing domain workflows. Preserve raw data and never guess analytical definitions. Claude Code and Codex share one rule, skill, and hook set; synchronize both runtime homes after changes and verify file parity. Update references and helpers together when a workflow contract changes.
