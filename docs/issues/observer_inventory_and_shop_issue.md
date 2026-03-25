## Parent PRD

#1

## What to build

Complete the observer's view of actionable inventory and shop state. This slice should export the actual consumables currently held in inventory, the full visible shop inventory rather than a partial first-item-only subset, and the current reroll cost, then carry that data through parser normalization and harness output.

## Acceptance criteria

- [ ] Live export reports the actual consumables currently held in inventory with stable item identity and kind fields.
- [ ] Live export reports every currently visible actionable shop item rather than only a partial subset.
- [ ] Live export reports reroll cost while in the shop.
- [ ] The Python observer and harness expose the complete inventory and shop view without regressing existing shop sections.
- [ ] Contract coverage verifies full-shop and inventory completeness for representative payloads.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 6
- User story 7
- User story 8
- User story 9
- User story 14
- User story 15
- User story 16
- User story 19
- User story 20
- User story 21
