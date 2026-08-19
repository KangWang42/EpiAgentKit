# Repository Guidelines

## Project Structure & Module Organization

This repository provides shared Claude Code and Codex guidance for epidemiology and biostatistics. `CLAUDE.md` holds cross-task rules; `README.md` covers installation and architecture. Each `skills/` directory is self-contained: keep `SKILL.md` concise, detailed guidance in `references/`, utilities in `scripts/`, and templates or media in `assets/`. Enforcement scripts live in `hooks/`. The allowlist `.gitignore` excludes runtime state, credentials, caches, histories, and local settings.

Keep the two backup branches separate. Superseded formal repository deliverables that must remain recoverable belong in `09_backup/archive/YYYY-MM-DD_HHMM_<topic>_<stage>/`; `09_backup/INDEX.md` indexes only those archive batches. Repository-maintenance experiments, one-off scripts and diagnostic outputs belong in `09_backup/workbench/YYYY-MM-DD_HHMM_<topic>_<purpose>/`, with `PLAN.md` before execution and `FINDINGS.md` after execution. The entire `09_backup/` tree is local-only and must remain ignored by Git; do not add `.gitkeep` files or public-document links that depend on its contents. Run workbench tasks there; do not place agent-created work in the system temp directory or the repository root. Point the current test process's `TEMP`, `TMP` and `TMPDIR` to that batch's `runtime/` directory, then remove only that runtime cache after the command finishes.

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

On Windows, follow the shell-safety and process-encoding rules in `CLAUDE.md`. Treat `powershell.exe` as Windows PowerShell 5.1, and use `pwsh` only when it is already available. For this UTF-8 repository, read text with `Get-Content -Encoding utf8`. Treat mojibake as a failed read. Use `-LiteralPath` only for cmdlets that support it. Put multiline logic, JSON, regular expressions, non-ASCII paths, or complex native arguments in the appropriate workbench or persistent script, and check native-command exit codes immediately. Avoid nested `powershell|pwsh -Command`, `Invoke-Expression`, string-built commands, or unverified launchers.

## Skill Maintenance

Every request to add, revise, repair, rename or remove a skill automatically uses `epiagentkit-maintenance` together with `skill-creator`; the user does not need to restate this requirement. Follow the cause-first, single-source and regression-safe optimization workflow in `epiagentkit-maintenance`; this file only adds repository structure, validation, commit and synchronization requirements and does not restate that maintenance workflow.

## Testing Guidelines

There is no central coverage target or test tree. Use validators, syntax checks, and focused execution. Reproduce bugs before fixing them, record verification commands in the pull request, and never use private research data as fixtures.

## Commit & Pull Request Guidelines

Follow `CLAUDE.md` for Git availability, automatic commit authorization, push authority and history safety. Use Conventional Commits: `feat(scope): summary`, `fix(scope): summary`, `docs(scope): summary`, or `refactor(scope): summary`. Make each commit one coherent, reversible unit; use a specific scope and action-object summary, and add a body covering motivation, key behavior, validation and compatibility for non-trivial changes. New skill additions follow the pre-commit review gate in `epiagentkit-maintenance`; edits, repairs, renames and removals of existing skills use that gate only when the user explicitly requests review artifacts. After every successful commit in this repository, run `python scripts/epiagentkit.py sync --target all` followed by `python scripts/epiagentkit.py doctor --target all` so the local Claude Code and Codex installations match the committed source. If a post-commit check requires another commit, repeat synchronization and doctor. Review the entire worktree before committing and do not include unexplained pre-existing changes. Pull requests must explain the problem, affected skills or hooks, verification commands and compatibility effects; include screenshots only for visual or document output.

## Agent-Specific Instructions

Use `epiagentkit-maintenance` for changes to this repository's rules, skills, hooks, scripts, synchronization contracts, or maintenance documentation. Read `CLAUDE.md` before changing domain workflows. Preserve raw data and never guess analytical definitions. Claude Code and Codex share one rule, skill, and hook set; synchronize both runtime homes after changes and verify file parity. Update references and helpers together when a workflow contract changes.
