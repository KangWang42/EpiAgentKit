---
name: git-commit-helper
description: Create or execute reviewable Conventional Commits from the complete diff, validation evidence and compatibility impact. Use for commit messages, staged-change review, commits, explicit push requests or repository-history cleanup. Only run when Git exists and the current directory is already a repository; never install Git or initialize one for this skill.
---

# Git Commit Helper

## Availability preflight

Before any Git command, verify that Git is already available and the current directory is a repository. If either check fails, report that Git was skipped and continue the parent task without version-control actions. Do not install Git, do not create an environment for it, and do not run `git init` unless the user explicitly requested repository initialization and Git is already available.

## Quick start

Analyze staged changes and generate commit message:

```bash
# View staged changes
git diff --staged

# Generate commit message based on changes
# (The active agent will analyze the diff and suggest a message)
```

## Commit message format

Follow conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

## Reviewable history contract

Write each commit so a future reader can understand the completed unit without opening every diff:

1. Make one commit represent one coherent user request or independently reversible change. Split unrelated changes; do not split tightly coupled rule, helper, template, and test updates.
2. Use a specific scope and an imperative summary naming both action and object. Avoid vague summaries such as `update files`, `changes`, `完善一下`, or `misc fixes`.
3. For any non-trivial or multi-file change, include a body with:
   - why the change was needed;
   - the key behavioral changes;
   - validation commands and results;
   - compatibility, migration, or rollback implications when present.
4. Review the complete worktree and staged diff before committing. Do not mix unexplained pre-existing changes into the commit.
5. After validation, create the commit automatically when the user's standing policy authorizes it and the availability preflight passes. If it does not pass, skip the commit without treating that as task failure. Push only when the user explicitly requests push in the current turn; do not ask, remind, or batch-push accumulated commits. Never force-push or rewrite remote history.

### Examples

**Feature commit:**
```
feat(auth): add JWT authentication

Implement JWT-based authentication system with:
- Login endpoint with token generation
- Token validation middleware
- Refresh token support
```

**Bug fix:**
```
fix(api): handle null values in user profile

Prevent crashes when user profile fields are null.
Add null checks before accessing nested properties.
```

**Refactor:**
```
refactor(database): simplify query builder

Extract common query patterns into reusable functions.
Reduce code duplication in database layer.
```

## Analyzing changes

Review what's being committed:

```bash
# Show files changed
git status

# Show detailed changes
git diff --staged

# Show statistics
git diff --staged --stat

# Show changes for specific file
git diff --staged path/to/file
```

## Commit message guidelines

**DO:**
- Use imperative mood ("add feature" not "added feature")
- Keep the first line under 72 characters; prefer under 50 when it remains specific
- No period at end of summary
- Explain WHY, key impact, and validation in the body

**DON'T:**
- Use vague messages like "update" or "fix stuff"
- Include technical implementation details in summary
- Write paragraphs in summary line
- Use past tense

## Multi-file commits

When committing multiple related changes:

```
refactor(core): restructure authentication module

- Move auth logic from controllers to service layer
- Extract validation into separate validators
- Update tests to use new structure
- Add integration tests for auth flow

Breaking change: Auth service now requires config object
```

## Scope examples

**Frontend:**
- `feat(ui): add loading spinner to dashboard`
- `fix(form): validate email format`

**Backend:**
- `feat(api): add user profile endpoint`
- `fix(db): resolve connection pool leak`

**Infrastructure:**
- `chore(ci): update Node version to 20`
- `feat(docker): add multi-stage build`

## Breaking changes

Indicate breaking changes clearly:

```
feat(api)!: restructure API response format

BREAKING CHANGE: All API responses now follow JSON:API spec

Previous format:
{ "data": {...}, "status": "ok" }

New format:
{ "data": {...}, "meta": {...} }

Migration guide: Update client code to handle new response structure
```

## Template workflow

1. **Check availability**: Continue only when Git is installed and the current directory is a repository; otherwise skip without installing or initializing Git
2. **Review worktree**: `git status --short`, `git diff`, and `git diff --staged`
3. **Confirm validation**: Record the commands run and their outcomes
4. **Identify type**: Is it feat, fix, refactor, docs, etc.?
5. **Determine scope**: What coherent subsystem changed?
6. **Write summary**: Specific imperative action + object
7. **Add body**: Motivation, key changes, validation, compatibility / rollback
8. **Note breaking changes**: If applicable
9. **Push only on explicit request**: If the current user turn asks for push, verify branch and remote divergence, then use a normal push; otherwise stop after commit without prompting about push

## Interactive commit helper

Use `git add -p` for selective staging:

```bash
# Stage changes interactively
git add -p

# Review what's staged
git diff --staged

# Commit with message
git commit -m "type(scope): description"
```

## Amending commits

Fix the last commit message:

```bash
# Amend commit message only
git commit --amend

# Amend and add more changes
git add forgotten-file.js
git commit --amend --no-edit
```

## Best practices

1. **Atomic commits** - One logical change per commit
2. **Test before commit** - Ensure code works
3. **Reference issues** - Include issue numbers if applicable
4. **Keep it focused** - Don't mix unrelated changes
5. **Write for humans** - Future you will read this

## Commit message checklist

- [ ] Type is appropriate (feat/fix/docs/etc.)
- [ ] Scope is specific and clear
- [ ] Summary is under 72 characters and as concise as specificity allows
- [ ] Summary uses imperative mood
- [ ] Body explains WHY, key behavior, and validation for non-trivial changes
- [ ] Breaking changes are clearly marked
- [ ] Related issue numbers are included
- [ ] Commit contains one coherent, reversible unit
- [ ] Commit was created after validation unless the user opted out
- [ ] Git availability and repository status were confirmed, or all Git operations were explicitly skipped without installation or initialization
- [ ] If push was explicitly requested, it is a normal fast-forward update with no force push
