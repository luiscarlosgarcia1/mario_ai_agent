## Parent PRD

#1

## What to build

Expose run-metadata fields that the policy needs to understand progression and ruleset context. This slice should make the live observer report the current ante, total round progression, and the chosen stake or difficulty for the run, then normalize and display those fields through the Python observer and observation harness.

## Acceptance criteria

- [ ] Live export includes ante, total round progression, and stake or difficulty in a stable gameplay-facing schema.
- [ ] The Python observer normalizes those fields into the public observation model from live export and fallback-safe paths.
- [ ] The observation harness prints the new run-metadata fields clearly enough for in-run verification.
- [ ] Contract coverage verifies the fields survive exporter-to-parser normalization.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 1
- User story 14
- User story 15
- User story 16
- User story 22
- User story 23
- User story 24
