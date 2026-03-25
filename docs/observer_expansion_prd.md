# PRD: Observer Expansion For Full Run-Relevant Balatro State

## Problem Statement

The current observer is good enough to prove the project direction, but it does not yet expose all of the run-relevant Balatro state that a strong policy needs. It can read core run values like money, hands, discards, blind, hand cards, and shallow joker information, but it does not yet provide a complete structured view of the things that drive real gameplay decisions.

Right now, the agent cannot reliably reason about the full state of a run because important information is missing from observation output. Missing areas include richer joker state, the active deck being played, vouchers, consumables, booster packs, tags, and shop-visible consumables. This makes it hard to build a policy that can make strong decisions in blinds, shops, and long-run deckbuilding situations.

The newest gaps are about completeness and phase accuracy rather than just field presence. The observer still misses or mislabels several gameplay-critical details:

- which consumables are actually in inventory
- the full set of currently visible shop items rather than only a partial shop snapshot
- reroll cost in the shop
- current ante and total round progression
- the selected stake or difficulty for the run, not just the deck
- whether a tag was claimed by skipping a blind
- which packs are currently present in the shop
- the distinction between blind select and the pack-opening or reward screen that appears after buying a pack

These gaps matter because they create policy mistakes even when most of the rest of the state is present. The observer must know the full actionable shop, the current progression of the run, and the correct gameplay phase in order to support reliable decision making.

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
- the full visible shop inventory rather than a first-item-only subset
- shop reroll cost
- current ante and total round progression
- selected stake or difficulty for the run
- whether a tag was earned from a blind skip and whether that state is still relevant
- pack offers visible in the shop and the separate post-purchase pack interaction phase

The system should prefer live exported state from the game whenever available and only fall back to save parsing when the live export is missing or unusable. The goal is not just to dump raw internal memory, but to provide a structured, gameplay-facing observation that policy code can use directly.

The observer should treat shop and pack state as game-state-derived structured data, not as something that depends on screenshot-only card identification. If the game state already knows which items and packs are present, the exported observation should know them too.

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
19. As the Balatro agent developer, I want the observer to expose the exact consumables currently stored in inventory, so that the policy can plan around held tarot, planet, and spectral resources instead of guessing.
20. As the Balatro agent developer, I want the observer to expose the full currently visible shop inventory, so that the policy can compare every available buy instead of only the first detected item.
21. As the Balatro agent developer, I want the observer to expose shop reroll cost, so that the policy can weigh rerolling against buying and saving.
22. As the Balatro agent developer, I want the observer to expose the current ante, so that the policy can make progression-aware decisions and know how close the run is to its next blind escalation.
23. As the Balatro agent developer, I want the observer to expose the total round count of the run, so that the policy can reason about run tempo, scaling, and long-run pacing.
24. As the Balatro agent developer, I want the observer to expose the chosen stake or difficulty for the run, so that the policy can account for rule and economy differences beyond the base deck identity.
25. As the Balatro agent developer, I want the observer to expose whether a tag was claimed by skipping a blind, so that the policy can reason about skip outcomes and tag-driven planning.
26. As the Balatro agent developer, I want the observer to expose which packs are currently available in the shop, so that the policy can compare pack value against jokers, consumables, and rerolls.
27. As the Balatro agent developer, I want the observer to distinguish pack-opening and reward-selection screens from blind-select screens, so that the agent can choose cards or skip correctly after buying a pack.
28. As the Balatro agent developer, I want the observer to expose pack interaction state in a structured way, so that the policy can understand when it is choosing rewards from a purchased pack rather than navigating the shop or blind menu.

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
- The observation model should include run progression metadata such as ante and total rounds completed or currently being played.
- The observation model should include chosen stake or difficulty as part of run identity, separate from deck identity.
- Voucher, booster pack, and tag output should represent active or currently visible run-relevant state, not every historical artifact the engine may have tracked earlier in the run.
- Shop output should include the full visible shop inventory across all relevant item types rather than a partial or first-item-only view.
- Shop output should include reroll cost as a first-class field.
- Pack offers visible in the shop should be exported separately and completely.
- The live exporter should prefer direct game-state summaries for shop and pack contents rather than depending on screenshot-only card recognition.
- The observation schema should include a phase or subphase model that distinguishes at least:
  - blind selection
  - normal shop browsing
  - pack-opening or reward-claim screens after purchasing a pack
- Skip-derived tag state should be represented in a gameplay-facing way so the policy can tell when a skip produced a tag and what that tag is.
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
  - shop inventory contains all visible actionable items rather than only a partial subset
  - reroll cost is present and accurate when in the shop
  - ante, round count, and stake are preserved
  - skip-derived tag state is preserved
  - pack offers and purchased-pack interaction state are distinguishable from blind select
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
- The observer should not treat game-state-known shop objects as unknown just because visual card recognition is incomplete. If the game knows what the item is, the export should identify it.
- This PRD sets up the next likely workflow:
  - break the observer expansion into implementation issues
  - implement the schema and exporter changes in slices
  - use TDD for exporter/parser contract coverage
