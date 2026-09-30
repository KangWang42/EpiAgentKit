---
name: git-commit-helper
description: "Review diffs and create Conventional Commit messages or commits; push only on explicit request. Use in an existing Git repository, without installing Git or initializing one."
---

# Git Commit Helper

Create a coherent, reversible Conventional Commit from the complete diff and validation evidence. Follow the root rules for commit authorization, push authority and history safety.

## Availability and Scope

Verify Git is already available and the current directory is a repository. Otherwise report "Git skipped" and continue the parent task; do not install Git or run `git init` for this skill.

Read `git status --short`, `git diff` and `git diff --staged`. Distinguish the requested changes from pre-existing work and preserve unexplained changes. Stage explicit paths or reviewed hunks; do not use a broad `git add .` when unrelated changes exist. Each commit should cover one coherent change, including its directly coupled rules, helpers, templates and tests.

## Message

Use this format:

```text
<type>(<scope>): <imperative action and object>

<motivation, behavior, validation and compatibility when non-trivial>

<issue reference or BREAKING CHANGE footer when applicable>
```

Choose `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `perf`, `build` or `ci` from the actual change. Use a specific scope; keep the summary under 72 characters, without a trailing period. Avoid vague summaries such as `update files`, `misc fixes` or `完善一下`. For a non-trivial change, explain the problem, resulting behavior, validation commands and results, and any compatibility or rollback implications. Do not claim checks that were not run.

Mark incompatible behavior with `!` or a `BREAKING CHANGE:` footer and describe the required migration. Reference an issue only when one exists. Do not force a body or checklist for a trivial wording correction.

## Commit and Verification

1. Complete checks required for the affected component and resolve failures caused by the change.
2. Review the entire worktree and staged diff; ensure no unexplained files, credentials, raw data, runtime caches or backup batches enter the commit.
3. Create the commit when the user's standing policy or current request authorizes it. For multiline messages use a UTF-8 message file in the permitted workbench and `git commit --file <message-file>`; do not construct a shell command from message text.
4. Verify the new commit and remaining worktree. Run repository-specific post-commit synchronization and checks when required.

## Push and History Changes

Push only when the user explicitly requests push in the current turn; otherwise finish after the commit without prompting about push. Before a normal push, verify branch, remote and divergence. Never force-push or rewrite remote history.

Amend or reorganize local commits only on an explicit history-edit request, after confirming they are unpublished and preserving a recoverable baseline. An ordinary fix after a commit uses a new commit. A rejected push is a reason to inspect divergence, not permission to reset, rebase or force-push.

## Completion

Report the commit hash and summary, validation outcome, material compatibility effects and any remaining worktree changes. If Git is unavailable or the directory is not a repository, state that version control was skipped without treating the completed parent task as a failure.
