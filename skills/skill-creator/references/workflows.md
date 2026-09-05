# Workflow Patterns

Read when a skill needs distinct operating modes or dependencies. A short task does not need a workflow diagram or a fixed number of steps.

## Dependencies

Prescribe order where a later action needs verified output from an earlier one. Filling a supplied PDF form requires identifying fields, checking the mapping, applying values and verifying output. It does not require review pauses between steps when the values and action are already authorized.

Describe inputs, outputs and failure conditions. Independent reads or checks may run together when supported; dependent writes remain sequential.

## Conditional Loading

Put the branch decision before detailed instructions. Text extraction uses the extraction helper; form filling loads field-mapping guidance; existing-document edits load scope-preservation guidance. Explain when another branch becomes necessary. Do not load all references before choosing, or make a narrow correction repeat the creation workflow.

## Stopping Conditions

Distinguish missing evidence, user decisions and routine implementation failures. Continue authorized work independent of pending decisions. Retry correctable failures within scope; stop when the next action requires new scientific definitions, unavailable inputs or additional authorization. After relevant checks pass, deliver without inventing another review stage.
