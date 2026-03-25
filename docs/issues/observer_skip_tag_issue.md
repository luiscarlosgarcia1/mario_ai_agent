## Parent PRD

#1

## What to build

Expose skip-derived tag state so the observer can tell when a blind was skipped for a tag and what the resulting tag state is for the run. This slice should export that tag-claim information, normalize it, and make it visible in the harness.

## Acceptance criteria

- [ ] Live export reports when a tag was claimed from skipping a blind and identifies the relevant resulting tag.
- [ ] The Python observer normalizes skip-derived tag state into the public observation schema.
- [ ] The observation harness shows skip-derived tag state clearly enough to verify during play.
- [ ] Contract coverage verifies that skip/tag state survives exporter-to-parser normalization.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 12
- User story 14
- User story 15
- User story 16
- User story 25
