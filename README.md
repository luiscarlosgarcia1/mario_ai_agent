# balatro_ai

Build a Balatro agent that can play faster and better than a human while also serving as a sandbox for practical AI engineering workflows like delegated coding tasks, validation, and experiment logging.

## What This Repo Is For

This project has two parallel goals:

1. Build a real Balatro-playing agent.
2. Practice common AI engineering patterns in a small, concrete system.

That means the code should not only make decisions, but also make it easy for coding agents to work safely and independently:

- separate observation, decision-making, execution, and validation
- compare strategies and log why actions were chosen
- swap in rule-based logic, scripted policies, or model-based policies
- support delegated implementation, review, and validation work

## Current Architecture

The starter scaffold is organized around a simple single-policy loop:

1. `Observer` reads the current game state.
2. `Policy` proposes the next action.
3. `Validator` checks whether the action is acceptable.
4. `Executor` performs the action.
5. `Runtime` logs the result and advances the episode.

This is not meant to imply multiple in-game agents. The runtime is a normal controller with a few clean components. The coding-agent workflow goal is about how we build the project, not how the Balatro player must think.

Right now the repo ships with a tiny scripted demo so the project has a runnable backbone before integrating screen capture, OCR, or keyboard/mouse control.

## Project Shape

```text
balatro_ai/
  policy.py       # demo policy and validator
  interfaces.py   # core protocols for the agent loop
  models.py       # shared data objects
  runtime.py      # episode runner and demo wiring
main.py           # local entrypoint
WORKFLOW.md       # how coding agents can split work safely
```

## Near-Term Milestones

### 1. Observation

- capture the game window
- detect phase: blind select, hand play, shop, reward screen
- extract key state like money, hands, discards, jokers, and visible cards

### 2. Safe Actioning

- map high-level actions to mouse/keyboard inputs
- add confirmation checks after each action
- recover when the game state does not change as expected

### 3. Better Decisions

- start with strong handcrafted heuristics
- add simulation or search where the game state is clear enough
- later plug in model-based ranking or planning

### 4. AI Workflow Practice

- keep modules small enough for coding agents to own one area at a time
- define interfaces clearly so delegated work can plug in cleanly
- make validation and review easy with logs, tests, and deterministic demos
- leave room for agent-based coding workflows like implementer, reviewer, and evaluator

## Why This Structure Helps Coding Agents

The validator is still useful inside the Balatro runtime, but the bigger reason for this structure is development workflow:

- one coding agent can implement observation
- another can work on action execution
- another can review logs, tests, or decision quality
- each part has a clear contract, which makes delegation less risky

The point is not to build a multi-agent Balatro player first. The point is to make the codebase easy for coding agents to extend safely.

## Run The Demo

```bash
python main.py
```

The current demo prints a short mocked episode and shows how the policy and validator interact.

## Suggested Next Step

Implement a real `Observer` that reads Balatro screenshots and outputs structured state. Once that exists, every other layer in this scaffold becomes much more valuable.
