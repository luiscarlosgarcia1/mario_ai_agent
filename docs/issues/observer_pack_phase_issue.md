## Parent PRD

#1

## What to build

Teach the observer to distinguish pack-opening and reward-selection screens from blind-select state. This slice should export the relevant pack-interaction phase and any immediately actionable reward-selection context so the policy can choose cards or skip correctly after buying a pack.

## Acceptance criteria

- [ ] Live export distinguishes pack-opening or reward-selection screens from blind selection and normal shop browsing.
- [ ] The observer exposes that pack-interaction phase through the public observation model.
- [ ] The observation harness makes the pack-interaction state readable during manual verification.
- [ ] Contract coverage verifies that purchased-pack flow is not mislabeled as blind select.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 13
- User story 14
- User story 15
- User story 16
- User story 27
- User story 28
