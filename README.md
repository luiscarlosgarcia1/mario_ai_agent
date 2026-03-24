# balatro_ai

Build a Balatro agent that can play faster and better than a human while also serving as a sandbox for practical AI engineering workflows like delegated coding tasks, agentic workflows, skills, validation, and experiment logging.

## Project Goals

This project still has the same two goals:

1. Build a real Balatro-playing agent.
2. Practice common AI engineering patterns while building it.

The second goal is about how we develop the codebase, not about turning the in-game player into a multi-agent system.

## AI Workflow Goal

This repo is also meant to be a good place to practice coding-agent workflows:

- clean module boundaries
- delegated implementation
- validation and review loops
- deterministic local harnesses for testing changes

## Current Architecture

The starter scaffold is organized around a simple single-policy loop:

1. `Observer` reads the current game state.
2. `Policy` proposes the next action.
3. `Validator` checks whether the action is acceptable.
4. `Executor` performs the action.
5. `Runtime` logs the result and advances the episode.

That structure is meant to keep the code easy to split across coding agents, review safely, and validate in small pieces.

## Run The Demo

```bash
python main.py
```

## Run Observation Testing

```bash
python obs_test.py
```

Common observation commands:

| Command | What it does |
| --- | --- |
| `python obs_test.py --once` | Parse and capture one observation, then exit. |
| `python obs_test.py --profile 2` | Explicitly read from Balatro profile `2`. |
| `python obs_test.py --window-title Balatro` | Look for a window whose title contains `Balatro`. |
| `python obs_test.py --rect 100 100 1600 900` | Capture a fixed screen rectangle instead of auto-detecting the window. |
| `python obs_test.py --show` | Open the captured full-frame image after saving it when possible. |

Clear saved observation output:

| Command | What it does |
| --- | --- |
| `.\clean_obs.ps1` | Clear the contents of `obs_test_output`. |

## Current State

The project now has the beginning of a hybrid observation stack:

- a save-first observer that reads Balatro data from `AppData/Roaming/Balatro`
- a live-export path that can prefer `AppData/Roaming/Balatro/ai/live_state.json` when a mod provides it
- parsing for core run state like money, blind, score, hands, discards, and card-area counts
- hand-card summaries with basic modifier extraction
- a local `obs_test.py` harness that watches live-export and save-file updates, writes parsed observations, and captures screenshots of the Balatro window

This is enough to start learning what the game exposes reliably from disk, where a live exporter removes latency, and where screenshots still need to fill gaps.

## Next Work

The highest-value next steps are:

1. Remove or reduce animations in the game so state changes become easier to capture and act on.
2. Increase the observation polling rate so live-state and save-driven updates are retrieved faster.
3. Screenshot more often, even between state updates, while organizing each screenshot under the most recent parsed game state.
4. Expand the live exporter so it covers more of the shop, jokers, consumables, and selection state.

## Observation

### Features

- reads structured Balatro state from disk
- prefers a live-export file when available
- parses core run state like money, blind, score, hands, discards, and card counts
- summarizes hand cards and basic modifiers
- captures screenshots alongside parsed observations through `obs_test.py`

### Limitations

- `save.jkr` is not a perfect real-time mirror of the visible game state
- the live exporter is still an initial scaffold and may need hook adjustments depending on how Balatro and Steamodded update
- screenshot capture is improving, but the observation timeline still needs tighter state-to-image linking

### To-Do

- runtime-verify the live exporter inside a real Balatro session
- expand state coverage for shop, consumables, selections, hovered cards, and other cluttered UI details
- add a smarter event-driven observe-after-action loop instead of relying only on steady polling
- improve screenshot organization so frames are tied more cleanly to the latest parsed state
- add tests around the parser and live-export contract
