# PRD: Observer Expansion For Full Run-Relevant Balatro State

## Problem Statement

The current observer is good enough to prove the project direction, but it does not yet expose all of the run-relevant Balatro state that a strong policy needs. It can read core run values like money, hands, discards, blind, hand cards, and shallow joker information, but it does not yet provide a complete structured view of the things that drive real gameplay decisions.

Right now, the agent cannot reliably reason about the full state of a run because important information is missing from observation output. Missing areas include richer joker state, the active deck being played, vouchers, consumables, booster packs, tags, and shop-visible consumables. This makes it hard to build a policy that can make strong decisions in blinds, shops, and long-run deckbuilding situations.

The user wants the observer expansion to make the live observation layer capable of seeing and outputting the run-relevant state needed for gameplay decisions, while keeping `live_state.json` as the primary source and `save.jkr` as a fallback and debugging source.

## Solution

Expand the observation stack so the Balatro mod exports a much richer `live_state.json` contract and the Python observer parses that contract into a stable gameplay-facing observation model.

The expanded observer should expose:

- current joker state, including gameplay-relevant modifiers and statuses
- the active deck identity for the current run
- active and run-relevant vouchers
- consumables with a `kind` field, separated into inventory consumables and shop-visible consumables
- consumable inventory size and current capacity
- hand card modifiers such as enhancements, seals, editions, and other gameplay-relevant values
- joker editions and other joker properties only when they affect gameplay
- booster packs that are currently relevant and visible to the run
- currently relevant tags
- blind type information

The system should prefer live exported state from the game whenever available and only fall back to save parsing when the live export is missing or unusable. The goal is not just to dump raw internal memory, but to provide a structured, gameplay-facing observation that policy code can use directly.

## User Stories

1. As the Balatro agent developer, I want the observer to expose the current deck identity, so that the policy can reason differently for different deck starts.
2. As the Balatro agent developer, I want the observer to expose the current blind name and blind key, so that the policy can respond to blind-specific constraints and effects.
3. As the Balatro agent developer, I want the observer to expose all current jokers in structured form, so that the policy can reason about synergies, scaling, and ordering decisions.
4. As the Balatro agent developer, I want the observer to include gameplay-relevant joker properties, so that the policy can distinguish between jokers that look similar but behave differently.
5. As the Balatro agent developer, I want the observer to expose hand card enhancements, seals, editions, and card modifiers, so that the policy can choose stronger hands and understand long-term card value.
6. As the Balatro agent developer, I want the observer to expose the player’s consumable inventory, so that the policy can decide when to hold, use, or replace consumables.
7. As the Balatro agent developer, I want the observer to report consumable inventory capacity, so that the policy can reason about whether a shop purchase can be stored.
8. As the Balatro agent developer, I want the observer to expose shop-visible consumables separately from stored consumables, so that the policy can reason about buying or immediately consuming shop items.
9. As the Balatro agent developer, I want tarot, planet, and spectral items represented through one shared consumable structure with a `kind` field, so that policy logic can stay simple while still preserving type differences.
10. As the Balatro agent developer, I want the observer to expose active and currently relevant vouchers, so that the policy can incorporate permanent run upgrades into decision making.
11. As the Balatro agent developer, I want the observer to expose currently relevant booster packs, so that the policy can reason about pack choices and shop value.
12. As the Balatro agent developer, I want the observer to expose currently relevant tags, so that the policy can account for run modifiers and tag-driven strategy changes.
13. As the Balatro agent developer, I want the observer output to favor gameplay-relevant state over raw internal noise, so that policy code can work from stable abstractions instead of game internals.
14. As the Balatro agent developer, I want the Python observer to normalize live exported state into one consistent observation schema, so that policy code does not need to care whether data came from the live exporter or the save fallback.
15. As the Balatro agent developer, I want the observation harness to surface the new state in human-readable form, so that I can verify correctness while playing.
16. As the Balatro agent developer, I want contract tests for the exporter and parser, so that future observer changes do not silently break policy inputs.
17. As the Balatro agent developer, I want the observer expansion to focus on persistent run state rather than hover-only or transient UI state, so that the first version stays stable and useful.
18. As the Balatro agent developer, I want only active and visible run-relevant state exported for vouchers, tags, packs, and consumables, so that the observation model stays focused on decisions the agent can make right now.

## Implementation Decisions

- `live_state.json` is the primary observation source for this feature. Save-file parsing remains a fallback and debugging source.
- The observation model should expand from a small core run snapshot into a richer gameplay-facing schema that includes deck identity, richer joker state, consumables, vouchers, tags, booster packs, and blind details.
- Consumables should use one shared structure with a `kind` field such as tarot, planet, or spectral.
- Consumables must be split into at least two observation sections:
  - inventory consumables currently held by the player
  - shop consumables that are visible and actionable without first entering inventory
- The observation model must include consumable inventory capacity, because the number of slots can change over a run.
- Joker output should include gameplay-relevant properties rather than all raw internal fields. Cosmetic-only properties are not required. Any property that changes decision quality should be included.
- Joker editions or stickers should be exported when they materially affect gameplay and omitted when they are purely cosmetic.
- Hand card output should continue to include enhancement, seal, edition, and gameplay-relevant modifiers.
- Blind output should include structured blind identity rather than only loose display text.
- Voucher, booster pack, and tag output should represent active or currently visible run-relevant state, not every historical artifact the engine may have tracked earlier in the run.
- Persistent game state is in scope. Hover-only, cursor-only, or other purely transient UI state is out of scope for this PRD.
- The live exporter should remain compact and policy-oriented rather than a full raw game-memory dump.
- The Python observer should normalize live-exported data into a stable schema that can also accept save-derived fallback data where possible.
- The observation harness should display the expanded data clearly enough for manual verification during play.
- Suggested deep modules for this work are:
  - a live observation schema module that defines the stable gameplay-facing contract
  - an exporter summarization module inside the Balatro mod that converts raw game objects into compact structured payloads
  - an observer normalization layer that converts live JSON into Python observation objects
  - an observation presentation layer for harness output and debugging

## Testing Decisions

- Good tests should verify observable behavior through public interfaces and stable output contracts, not exporter implementation details or private helper structure.
- Tests should assert that given a live-export payload with run-relevant state, the observer produces the correct normalized observation model.
- Tests should also assert that the observation harness surfaces the new high-level sections in a readable way without depending on exact internal helper functions.
- Exporter and parser contract tests are equally important for this feature.
- Modules to test:
  - live exporter output contract
  - Python observer normalization and fallback handling
  - observation model behavior for newly added gameplay-relevant fields
  - observation harness formatting for expanded sections
- Prior art in the current codebase is light. There is not yet a mature automated test suite for the observer. The closest behavioral reference is the existing observation harness, which acts as a manual end-to-end verification surface. This feature should introduce contract-focused automated tests rather than implementation-coupled unit tests.
- Tests should prioritize behavior such as:
  - deck identity is present when available
  - blind details are preserved
  - jokers include gameplay-relevant fields
  - consumables are split correctly between inventory and shop-visible items
  - consumable kinds are preserved
  - vouchers, packs, and tags appear when active or visible
  - fallback behavior remains safe when live export is absent or partial

## Out of Scope

- Policy logic for using the expanded observation data
- Input automation or executor behavior
- Training, self-play, or learning systems
- Hover-only state, cursor state, and other purely transient UI details
- Screenshot-only inference for state that can be exported structurally
- Exhaustive export of every raw internal Balatro field regardless of gameplay relevance

## Further Notes

- The initial goal is to expose all run-relevant state needed for strong decision making, not to expose every internal engine detail.
- This PRD intentionally favors a compact, stable, gameplay-facing observation contract because that will make policy implementation and testing much easier.
- If a field’s gameplay relevance is uncertain, the default rule should be: include it when it changes action quality, exclude it when it is cosmetic noise.
- This PRD sets up the next likely workflow:
  - break the observer expansion into implementation issues
  - implement the schema and exporter changes in slices
  - use TDD for exporter/parser contract coverage
