# balatro_ai

Build a Balatro agent that can play faster and better than a human while also serving as a sandbox for practical AI engineering workflows like delegated coding tasks, validation, and experiment logging.

## Project Goals

This project still has the same two goals:

1. Build a real Balatro-playing agent.
2. Practice common AI engineering patterns while building it.

The second goal is about how we develop the codebase, not about turning the in-game player into a multi-agent system.

## Current State

The project now has the beginning of an observation stack:

- a save-first observer that reads Balatro data from `AppData/Roaming/Balatro`
- parsing for core run state like money, blind, score, hands, discards, and card-area counts
- hand-card summaries with basic modifier extraction
- a local `obs_test.py` harness that watches the save, writes parsed observations, and captures screenshots of the Balatro window

This is enough to start learning what the game exposes reliably from disk and where screenshots still need to fill gaps.

## Current Architecture

The starter scaffold is organized around a simple single-policy loop:

1. `Observer` reads the current game state.
2. `Policy` proposes the next action.
3. `Validator` checks whether the action is acceptable.
4. `Executor` performs the action.
5. `Runtime` logs the result and advances the episode.

That structure is meant to keep the code easy to split across coding agents, review safely, and validate in small pieces.

## Project Shape

```text
balatro_ai/
  observer.py     # save-first observation and parsing
  policy.py       # demo policy and validator
  interfaces.py   # core protocols for the agent loop
  models.py       # shared data objects
  runtime.py      # episode runner and demo wiring
obs_test.py       # local observation/screenshot harness
clean_obs.ps1     # clear obs_test_output on Windows
main.py           # local entrypoint
WORKFLOW.md       # how coding agents can split work safely
```

## Observation Strategy

The intended observation stack is:

1. Read the live save file for structured state.
2. Capture screenshots often enough to cover state transitions that the save file misses.
3. Tie those screenshots back to the most recent parsed game state.
4. Fall back to heavier vision only when save data and lightweight capture are not enough.

This should stay lighter and more reliable than trying to understand Balatro purely from screenshots.

## Current Limitations

- `save.jkr` is not a perfect real-time mirror of the visible game state
- some fast transitions can be missed if the game does not flush the save quickly enough
- screenshot capture is improving, but the observation timeline still needs tighter state-to-image linking

## Next Work

The highest-value next steps are:

1. Remove or reduce animations in the game so state changes become easier to capture and act on.
2. Increase the observation polling rate so save-driven state updates are retrieved faster.
3. Screenshot more often, even between save updates, while organizing each screenshot under the most recent parsed game state.

## AI Workflow Goal

This repo is also meant to be a good place to practice coding-agent workflows:

- clean module boundaries
- delegated implementation
- validation and review loops
- deterministic local harnesses for testing changes

## Run The Demo

```bash
python main.py
```

## Run Observation Testing

```bash
python obs_test.py
```
