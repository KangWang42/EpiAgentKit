---
name: skill-creator
description: Create, revise, optimize or package an agent skill and its supporting resources. Use for skill authoring, not ordinary work performed with an existing skill.
license: Complete terms in LICENSE.txt
---

# Skill Creator

Write task-specific guidance for Claude Code and Codex. Follow the root rules' priority order and use `epiagentkit-maintenance` for EpiAgentKit changes. Preserve user choices, scope and existing authorization.

## Optimize, Don't Accumulate

Identify the observed gap, required old behavior and representative old and new evaluations. Classify material as `keep / rewrite / merge / move / script / delete` before adding requirements. Read the affected branch and callers; expand when shared behavior changes.

Assume the agent is capable. Retain non-obvious domain knowledge, constraints and tool requirements. Delete generic tutorials, duplicate rules and speculative exceptions; remove superseded text in the same edit. When both versions pass the same evaluations, prefer the smaller and easier-to-navigate version.

Prescribe fixed sequences only where order protects correctness, permissions or a fragile operation. Otherwise describe the outcome, evidence, decision criteria and stopping conditions. A model upgrade alone does not justify changing scientific methods or weakening verification.

## Discovery and Resources

Keep descriptions short: capability, actual trigger and exclusions that prevent likely misrouting. Put explicit exclusions and companion skills in the relevant body branch when they explain execution rather than selection. Move tool lists, quality claims and detailed steps out of metadata.

Keep shared decisions in `SKILL.md`. Link conditional references with their loading conditions; do not load every branch or create a router for a simple skill. Reuse already read, unchanged instructions.

- `scripts/`: repeated transformations and deterministic checks. Read implementation when changing it; otherwise use verified help and commands.
- `references/`: task-specific schemas, requirements and substantial workflow variants.
- `assets/`: templates or media used in the output.

Read [workflow patterns](references/workflows.md) when designing branches or dependencies, and [output patterns](references/output-patterns.md) when a fixed schema or style example is needed. A wording correction does not require these references.

## Authoring

1. Establish the requested capability from available instructions and examples. Ask only for missing information that materially changes the result.
2. List an existing skill's directory and preserve useful resources and supported metadata. For a new skill, run `python skills/skill-creator/scripts/init_skill.py <skill-name> --path <parent>` from the repository. Never reinitialize an existing skill. Remove unused examples and replace placeholders.
3. For each branch cover trigger, exclusion, unique input, domain action, companion skill when needed, minimum checks, changes that require wider checks, and completion evidence. These are questions to resolve, not mandatory headings or fields.
4. Run `python skills/skill-creator/scripts/quick_validate.py skills/<skill-name>` and execute new or changed scripts with representative inputs. Verify realistic tasks and boundaries; metadata validation does not prove good routing or completion.
5. Complete applicable repository review, commit and synchronization. Package only when a distributable `.skill` archive is requested or required: `python skills/skill-creator/scripts/package_skill.py <skill-folder> <output-directory>`. Ordinary repository edits do not create an archive.

Use lowercase kebab-case names of at most 64 characters, matching the directory. YAML requires `name` and `description`; preserve supported `license`, `metadata`, `allowed-tools` and `disable-model-invocation` fields. Client invocation settings are not interchangeable; verify current client documentation before changing them. Preserve invocation mode unless the user requests a change; side effects alone do not imply explicit-only discovery.

## Verification and Completion

Every check must name a concrete error the change could cause. Content skills own professional meaning; file skills own structure and display. Reuse evidence when input, method and examined content are unchanged, and do not let a local correction reopen project- or release-level checks.

For substantial routing or execution changes, compare representative old and new tasks for selected branches, unintended work, approval pauses and actual completion. Prompt length is not a performance result; measure time or tool use only with comparable runs. Static wording checks protect explicit contracts but do not replace behavioral evaluation.

When authorized and available, use an independent subagent for complex or risky behavioral evaluation while other useful work proceeds. Supply the user request, skill and minimum artifacts, without the expected answer or suspected failure. Use an isolated workbench and inspect actual outcomes. Small edits do not require delegation.

Once applicable checks pass, finish the delivery. Expand verification only for new changes, failures or uncovered impact. New-skill review requirements belong to `epiagentkit-maintenance`; do not copy them into the authored skill's daily workflow.
