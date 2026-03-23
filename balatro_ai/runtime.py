from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .policy import DemoPolicy, RuleBasedValidator
from .interfaces import Executor, Observer, Policy, Validator
from .models import GameAction, GameObservation, StepRecord


class ScriptedObserver:
    """Returns a fixed sequence of mock states for local development."""

    def __init__(self, observations: Iterable[GameObservation]) -> None:
        self._observations = iter(observations)

    def observe(self) -> GameObservation:
        return next(self._observations)


class LoggingExecutor:
    """Stands in for real keyboard and mouse automation."""

    def execute(self, action: GameAction) -> None:
        print(f"EXECUTE  kind={action.kind} target={action.target} reason={action.reason}")


@dataclass
class EpisodeRunner:
    """Runs one gameplay loop for a single Balatro-playing policy."""

    observer: Observer
    policy: Policy
    validator: Validator
    executor: Executor

    def run(self) -> list[StepRecord]:
        records: list[StepRecord] = []

        while True:
            try:
                observation = self.observer.observe()
            except StopIteration:
                break

            print(
                "OBSERVE  "
                f"phase={observation.phase} money={observation.money} "
                f"hands={observation.hands_left} discards={observation.discards_left} "
                f"score={observation.current_score}/{observation.score_to_beat}"
            )
            action = self.policy.choose_action(observation)
            validation = self.validator.validate(observation, action)

            print(
                f"DECIDE   kind={action.kind} accepted={validation.accepted} "
                f"notes={'; '.join(validation.notes)}"
            )

            if validation.accepted:
                self.executor.execute(action)
            else:
                print("SKIP     rejected action was not executed")

            records.append(
                StepRecord(
                    observation=observation,
                    action=action,
                    validation=validation,
                )
            )

        return records


def create_demo_runner() -> EpisodeRunner:
    observations = [
        GameObservation(
            phase="blind_select",
            money=4,
            hands_left=4,
            discards_left=3,
            score_to_beat=300,
            notes=("Small blind available.",),
        ),
        GameObservation(
            phase="play_hand",
            money=4,
            hands_left=4,
            discards_left=3,
            score_to_beat=300,
            current_score=90,
            jokers=("Greedy Joker",),
        ),
        GameObservation(
            phase="shop",
            money=6,
            hands_left=0,
            discards_left=0,
            score_to_beat=300,
            current_score=420,
            jokers=("Greedy Joker",),
        ),
    ]
    return EpisodeRunner(
        observer=ScriptedObserver(observations),
        policy=DemoPolicy(),
        validator=RuleBasedValidator(),
        executor=LoggingExecutor(),
    )


def main() -> None:
    records = create_demo_runner().run()
    accepted = sum(1 for record in records if record.validation.accepted)
    print(f"SUMMARY  steps={len(records)} accepted_actions={accepted}")
