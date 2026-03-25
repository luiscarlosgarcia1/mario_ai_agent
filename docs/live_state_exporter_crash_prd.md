# PRD: Live State Exporter Crash Hardening

## Problem Statement

The `live_state_exporter` mod can crash Balatro during `love.update` when it builds the snapshot signature for change detection. The current `make_signature` implementation pushes values into a `parts` table and then calls `table.concat(parts, "::")`. If any of those values are `nil`, Lua raises an error and the game crashes.

From the player's perspective, the observer mod should never crash the game just because a piece of state is temporarily unavailable or missing from a snapshot.

## Solution

Harden the live exporter so missing or partially unavailable state is treated as normal and does not crash signature generation or snapshot export.

The exporter should:

- tolerate missing optional state fields while building a signature
- keep writing `live_state.json` when snapshot fields are partial
- preserve deterministic change detection so redundant writes are still avoided
- stay compatible with the Python observer contract already in the repo

## User Stories

1. As the Balatro agent developer, I want the live exporter to survive missing snapshot fields, so that the game does not crash during observation.
2. As the Balatro agent developer, I want signature generation to be nil-safe, so that partially available game state is still exportable.
3. As the Balatro agent developer, I want the exporter to keep producing stable signatures, so that rate-limited change detection still works correctly.
4. As the Balatro agent developer, I want this crash covered by regression checks, so that future exporter refactors do not reintroduce it.

## Implementation Decisions

- The public behavior to preserve is: `live_state.json` export should continue even when some snapshot fields are absent.
- Missing values in signature generation should be normalized to safe strings instead of being passed through as raw `nil`.
- The fix should be narrowly scoped to exporter crash hardening and should not redesign the full observation schema.
- The crash-hardening work should preserve compatibility with the expanded observation contract already implemented in Python.

## Testing Decisions

- Good tests should verify behavior, not helper internals.
- The most important behavior is that partial snapshot state does not crash signature generation or export.
- Regression coverage should focus on deterministic, nil-safe signature behavior for partial snapshots.
- If direct Lua execution is unavailable in the dev environment, the test strategy should still validate the intended behavior as closely as possible and document any remaining manual verification step.

## Out of Scope

- New observation categories
- Policy changes
- Executor changes
- Screenshot pipeline changes

## Further Notes

- This PRD is intentionally narrow because it exists to unblock the crashing mod quickly and safely.
