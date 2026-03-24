from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import zlib

from .models import GameObservation, ObservedCard


DEFAULT_BALATRO_ROOT = Path.home() / "AppData" / "Roaming" / "Balatro"


@dataclass(frozen=True)
class PixelRect:
    left: int
    top: int
    width: int
    height: int


@dataclass(frozen=True)
class CaptureBand:
    label: str
    top_ratio: float
    height_ratio: float

    def to_rect(self, window_width: int, window_height: int) -> PixelRect:
        top = int(window_height * self.top_ratio)
        height = max(1, int(window_height * self.height_ratio))
        return PixelRect(left=0, top=top, width=window_width, height=height)


@dataclass(frozen=True)
class LightweightCapturePlan:
    """Small horizontal bands for click targeting without full-frame screenshots."""

    bands: tuple[CaptureBand, ...]

    @classmethod
    def default(cls) -> "LightweightCapturePlan":
        return cls(
            bands=(
                CaptureBand(label="joker_row", top_ratio=0.10, height_ratio=0.16),
                CaptureBand(label="shop_row", top_ratio=0.28, height_ratio=0.18),
                CaptureBand(label="consumable_row", top_ratio=0.48, height_ratio=0.14),
                CaptureBand(label="hand_row", top_ratio=0.70, height_ratio=0.20),
            )
        )

    def to_rects(self, window_width: int, window_height: int) -> dict[str, PixelRect]:
        return {
            band.label: band.to_rect(window_width=window_width, window_height=window_height)
            for band in self.bands
        }


@dataclass(frozen=True)
class BalatroPaths:
    root: Path = DEFAULT_BALATRO_ROOT
    profile: int = 2

    @property
    def settings_path(self) -> Path:
        return self.root / "settings.jkr"

    @property
    def ai_dir(self) -> Path:
        return self.root / "ai"

    @property
    def profile_dir(self) -> Path:
        return self.root / str(self.profile)

    @property
    def save_path(self) -> Path:
        return self.profile_dir / "save.jkr"

    @property
    def profile_path(self) -> Path:
        return self.profile_dir / "profile.jkr"

    @property
    def meta_path(self) -> Path:
        return self.profile_dir / "meta.jkr"

    @property
    def live_state_path(self) -> Path:
        return self.ai_dir / "live_state.json"

    def available_profiles(self) -> tuple[int, ...]:
        profiles: list[int] = []
        if not self.root.exists():
            return ()

        for child in self.root.iterdir():
            if child.is_dir() and child.name.isdigit() and (child / "save.jkr").exists():
                profiles.append(int(child.name))
        return tuple(sorted(profiles))


@dataclass(frozen=True)
class SaveSnapshot:
    profile: int
    save_path: Path
    modified_at: datetime
    raw_payload: str
    active_payload: str


class SavePayloadDecoder:
    """Decode Balatro's deflated save files into Lua source text."""

    _window_sizes = (
        zlib.MAX_WBITS,
        -zlib.MAX_WBITS,
        zlib.MAX_WBITS | 32,
    )

    def decode_bytes(self, compressed_bytes: bytes) -> str:
        last_error: Exception | None = None
        for window_size in self._window_sizes:
            try:
                return zlib.decompress(compressed_bytes, window_size).decode("utf-8")
            except (zlib.error, UnicodeDecodeError) as exc:
                last_error = exc

        raise ValueError("Could not decode Balatro save payload.") from last_error

    def decode_file(self, path: Path) -> str:
        return self.decode_bytes(path.read_bytes())

    def extract_active_payload(self, payload: str) -> str:
        marker = " end return "
        if marker not in payload:
            return payload

        active_payload = payload.split(marker, 1)[1].strip()
        if active_payload.startswith("return "):
            return active_payload
        return f"return {active_payload}"


class BalatroSaveObserver:
    """Observation layer that prefers live save files over OCR-heavy screenshots."""

    def __init__(
        self,
        paths: BalatroPaths | None = None,
        decoder: SavePayloadDecoder | None = None,
        capture_plan: LightweightCapturePlan | None = None,
    ) -> None:
        self.paths = paths or BalatroPaths()
        self.decoder = decoder or SavePayloadDecoder()
        self.capture_plan = capture_plan or LightweightCapturePlan.default()

    def observe(self) -> GameObservation:
        live_observation = self.read_live_observation()
        if live_observation is not None:
            return live_observation

        snapshot = self.read_snapshot()
        return self._build_observation(snapshot)

    def read_live_observation(self) -> GameObservation | None:
        path = self.paths.live_state_path
        if not path.exists():
            return None

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        if not isinstance(payload, dict):
            return None

        state = payload.get("state")
        if not isinstance(state, dict):
            state = payload
        if not isinstance(state, dict):
            return None

        hand_cards_payload = state.get("hand_cards")
        hand_cards: list[ObservedCard] = []
        if isinstance(hand_cards_payload, list):
            for item in hand_cards_payload:
                if not isinstance(item, dict):
                    continue
                modifiers = item.get("modifiers")
                hand_cards.append(
                    ObservedCard(
                        area=str(item.get("area", "hand")),
                        code=self._string_or_none(item.get("code")),
                        name=self._string_or_none(item.get("name")),
                        facing=self._string_or_none(item.get("facing")),
                        enhancement=self._string_or_none(item.get("enhancement")),
                        edition=self._string_or_none(item.get("edition")),
                        seal=self._string_or_none(item.get("seal")),
                        debuffed=bool(item.get("debuffed", False)),
                        modifiers=tuple(
                            str(value) for value in modifiers
                        ) if isinstance(modifiers, list) else (),
                    )
                )

        notes = state.get("notes")
        if not isinstance(notes, list):
            notes = []

        jokers_payload = state.get("jokers")
        jokers: list[str] = []
        if isinstance(jokers_payload, list):
            for item in jokers_payload:
                if item is None:
                    continue
                if isinstance(item, dict):
                    label = self._string_or_none(item.get("name")) or self._string_or_none(item.get("label"))
                    if label:
                        jokers.append(label)
                    continue
                jokers.append(str(item))

        seen_at_raw = state.get("seen_at")
        seen_at = None
        if isinstance(seen_at_raw, str):
            try:
                seen_at = datetime.fromisoformat(seen_at_raw)
            except ValueError:
                seen_at = None
        if seen_at is None:
            seen_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

        return GameObservation(
            phase=str(state.get("phase", state.get("state", "unknown"))),
            money=self._int_or_zero(state.get("money")),
            hands_left=self._int_or_zero(state.get("hands_left")),
            discards_left=self._int_or_zero(state.get("discards_left")),
            score_to_beat=self._int_or_zero(
                state.get("score_to_beat", state.get("target"))
            ),
            current_score=self._int_or_zero(
                state.get("current_score", state.get("score"))
            ),
            jokers=tuple(jokers),
            hand_cards=tuple(hand_cards),
            source=str(state.get("source", "live_export")),
            state_id=self._int_or_none(state.get("state_id")),
            blind_name=self._string_or_none(
                state.get("blind_name", state.get("blind"))
            ),
            blind_key=self._string_or_none(state.get("blind_key")),
            cards_in_hand=self._int_or_none(state.get("cards_in_hand")),
            jokers_count=self._int_or_none(state.get("jokers_count")),
            notes=tuple(str(value) for value in notes if value is not None),
            seen_at=seen_at,
        )

    def read_snapshot(self) -> SaveSnapshot:
        raw_payload = self.decoder.decode_file(self.paths.save_path)
        modified_at = datetime.fromtimestamp(
            self.paths.save_path.stat().st_mtime,
            tz=timezone.utc,
        )
        return SaveSnapshot(
            profile=self.paths.profile,
            save_path=self.paths.save_path,
            modified_at=modified_at,
            raw_payload=raw_payload,
            active_payload=self.decoder.extract_active_payload(raw_payload),
        )

    def _build_observation(self, snapshot: SaveSnapshot) -> GameObservation:
        payload = snapshot.active_payload
        blind_block = self._extract_block(payload, "BLIND") or ""
        game_block = self._extract_block(payload, "GAME") or ""
        current_round_block = self._extract_block(game_block, "current_round") or ""
        round_resets_block = self._extract_block(game_block, "round_resets") or ""
        card_areas_block = self._extract_block(payload, "cardAreas") or ""
        pseudorandom_block = self._extract_block(game_block, "pseudorandom") or ""

        state_id = self._extract_int(payload, "STATE")
        blind_name = self._extract_top_level_string(blind_block, "name") or self._extract_string(blind_block, "name")
        blind_key = self._extract_top_level_string(blind_block, "config_blind") or self._extract_string(blind_block, "config_blind")
        money = self._extract_top_level_big_number(game_block, "dollars")
        if money is None:
            money = self._extract_big_number(game_block, "dollars") or 0
        hands_left = self._extract_int(current_round_block, "hands_left")
        discards_left = self._extract_int(current_round_block, "discards_left")
        score_to_beat = self._extract_top_level_big_number(blind_block, "chips")
        if score_to_beat is None:
            score_to_beat = self._extract_big_number(blind_block, "chips") or 0
        current_score = self._extract_top_level_big_number(game_block, "chips")
        if current_score is None:
            current_score = self._extract_big_number(game_block, "chips") or 0
        cards_in_hand = self._extract_area_card_count(card_areas_block, "hand")
        jokers_count = self._extract_area_card_count(card_areas_block, "jokers")
        seed = self._extract_string(pseudorandom_block, "seed")
        blind_in_progress = self._extract_top_level_bool(blind_block, "in_blind")
        if blind_in_progress is None:
            blind_in_progress = self._extract_bool(blind_block, "in_blind")
        blind_on_deck = self._extract_top_level_string(game_block, "blind_on_deck") or self._extract_string(game_block, "blind_on_deck")
        joker_names = self._extract_area_labels(card_areas_block, "jokers")
        hand_cards = self._extract_area_cards(card_areas_block, "hand")

        phase = self._infer_phase(
            state_id=state_id,
            blind_in_progress=blind_in_progress,
            blind_on_deck=blind_on_deck,
            current_round_block=current_round_block,
            round_resets_block=round_resets_block,
        )

        notes: list[str] = [f"profile={snapshot.profile}", f"save={snapshot.save_path.name}"]
        if blind_name:
            notes.append(f"blind={blind_name}")
        if seed:
            notes.append(f"seed={seed}")
        if cards_in_hand is not None:
            notes.append(f"cards_in_hand={cards_in_hand}")
        if jokers_count is not None:
            notes.append(f"jokers_count={jokers_count}")

        return GameObservation(
            phase=phase,
            money=money,
            hands_left=hands_left or self._extract_int(round_resets_block, "hands") or 0,
            discards_left=discards_left or self._extract_int(round_resets_block, "discards") or 0,
            score_to_beat=score_to_beat,
            current_score=current_score,
            jokers=joker_names,
            hand_cards=hand_cards,
            source="save_file",
            state_id=state_id,
            blind_name=blind_name,
            blind_key=blind_key,
            cards_in_hand=cards_in_hand,
            jokers_count=jokers_count,
            notes=tuple(notes),
            seen_at=snapshot.modified_at,
        )

    def _infer_phase(
        self,
        *,
        state_id: int | None,
        blind_in_progress: bool | None,
        blind_on_deck: str | None,
        current_round_block: str,
        round_resets_block: str,
    ) -> str:
        if blind_in_progress:
            return "play_hand"

        hands_left = self._extract_int(current_round_block, "hands_left")
        discards_left = self._extract_int(current_round_block, "discards_left")
        round_blind_name = self._extract_string(self._extract_block(round_resets_block, "blind") or "", "name")
        if blind_on_deck and round_blind_name and hands_left is not None and discards_left is not None:
            return "blind_select"

        if state_id is None:
            return "unknown"
        return f"state_{state_id}"

    def _extract_area_card_count(self, card_areas_block: str, area_name: str) -> int | None:
        area_block = self._extract_block(card_areas_block, area_name)
        if not area_block:
            return None

        cards_block = self._extract_block(area_block, "cards") or ""
        search_start = 0
        if cards_block:
            search_start = area_block.find(cards_block) + len(cards_block)
        config_block = self._extract_block(area_block, "config", start=search_start) or area_block
        return self._extract_int(config_block, "card_count")

    def _extract_area_labels(self, card_areas_block: str, area_name: str) -> tuple[str, ...]:
        area_block = self._extract_block(card_areas_block, area_name)
        if not area_block:
            return ()

        cards_block = self._extract_block(area_block, "cards") or ""
        labels = re.findall(r'\["label"\]="((?:[^"\\]|\\.)*)"', cards_block)
        cleaned: list[str] = []
        for label in labels:
            decoded = self._unescape(label)
            if decoded and decoded != "Base Card":
                cleaned.append(decoded)
        return tuple(cleaned)

    def _extract_area_cards(self, card_areas_block: str, area_name: str) -> tuple[ObservedCard, ...]:
        area_block = self._extract_block(card_areas_block, area_name)
        if not area_block:
            return ()

        cards_block = self._extract_block(area_block, "cards") or ""
        cards: list[ObservedCard] = []
        for _, card_block in self._iter_child_blocks(cards_block):
            cards.append(self._build_card_summary(area_name, card_block))
        return tuple(cards)

    def _build_card_summary(self, area_name: str, card_block: str) -> ObservedCard:
        save_fields_block = self._extract_block(card_block, "save_fields") or ""
        base_block = self._extract_block(card_block, "base") or ""
        ability_block = self._extract_block(card_block, "ability") or ""
        edition_block = self._extract_block(card_block, "edition") or ""

        enhancement = self._extract_top_level_string(ability_block, "effect")
        if enhancement == "Base":
            enhancement = None

        modifiers: list[str] = []
        for key, label, default in (
            ("bonus", "bonus", 0),
            ("mult", "mult", 0),
            ("x_mult", "x_mult", 1),
            ("x_chips", "x_chips", 1),
            ("perma_bonus", "perma_bonus", 0),
            ("perma_mult", "perma_mult", 0),
            ("perma_x_mult", "perma_x_mult", 0),
            ("perma_x_chips", "perma_x_chips", 0),
            ("h_mult", "h_mult", 0),
            ("h_chips", "h_chips", 0),
            ("h_x_mult", "h_x_mult", 0),
            ("h_x_chips", "h_x_chips", 1),
            ("h_dollars", "h_dollars", 0),
            ("p_dollars", "p_dollars", 0),
            ("t_mult", "t_mult", 0),
            ("t_chips", "t_chips", 0),
            ("d_size", "d_size", 0),
            ("h_size", "h_size", 0),
        ):
            value = self._extract_top_level_number(ability_block, key)
            if value is not None and value != default:
                modifiers.append(f"{label}={self._format_number(value)}")

        if self._extract_top_level_bool(card_block, "debuff"):
            modifiers.append("debuffed")

        if self._extract_top_level_bool(ability_block, "played_this_ante"):
            modifiers.append("played_this_ante")

        return ObservedCard(
            area=area_name,
            code=self._extract_string(save_fields_block, "card"),
            name=self._extract_string(base_block, "name"),
            facing=self._extract_top_level_string(card_block, "facing"),
            enhancement=enhancement,
            edition=self._extract_top_level_string(edition_block, "type")
            or self._extract_top_level_string(edition_block, "key")
            or self._extract_top_level_string(edition_block, "name"),
            seal=self._extract_top_level_string(card_block, "seal"),
            debuffed=bool(self._extract_top_level_bool(card_block, "debuff")),
            modifiers=tuple(modifiers),
        )

    def _extract_string(self, text: str, key: str) -> str | None:
        match = re.search(rf'\["{re.escape(key)}"\]="((?:[^"\\]|\\.)*)"', text)
        if not match:
            return None
        return self._unescape(match.group(1))

    def _extract_top_level_string(self, text: str, key: str) -> str | None:
        raw = self._extract_top_level_raw_value(text, key)
        if raw is None:
            return None
        match = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', raw)
        if not match:
            return None
        return self._unescape(match.group(1))

    def _extract_int(self, text: str, key: str) -> int | None:
        match = re.search(rf'\["{re.escape(key)}"\]=(-?\d+)', text)
        if not match:
            return None
        return int(match.group(1))

    def _extract_top_level_int(self, text: str, key: str) -> int | None:
        raw = self._extract_top_level_raw_value(text, key)
        if raw is None:
            return None
        match = re.fullmatch(r"-?\d+", raw)
        if not match:
            return None
        return int(raw)

    def _extract_bool(self, text: str, key: str) -> bool | None:
        match = re.search(rf'\["{re.escape(key)}"\]=(true|false)', text)
        if not match:
            return None
        return match.group(1) == "true"

    def _extract_top_level_bool(self, text: str, key: str) -> bool | None:
        raw = self._extract_top_level_raw_value(text, key)
        if raw is None:
            return None
        if raw == "true":
            return True
        if raw == "false":
            return False
        return None

    def _extract_big_number(self, text: str, key: str) -> int | None:
        match = re.search(rf'\["{re.escape(key)}"\]=to_big\(\{{(-?\d+)', text)
        if match:
            return int(match.group(1))
        return self._extract_int(text, key)

    def _extract_top_level_big_number(self, text: str, key: str) -> int | None:
        raw = self._extract_top_level_raw_value(text, key)
        if raw is None:
            return None
        match = re.fullmatch(r"to_big\(\{(-?\d+)(?:,\s*)?\},\s*1\)", raw)
        if match:
            return int(match.group(1))
        match = re.fullmatch(r"-?\d+", raw)
        if match:
            return int(raw)
        return None

    def _extract_top_level_number(self, text: str, key: str) -> float | int | None:
        raw = self._extract_top_level_raw_value(text, key)
        if raw is None:
            return None
        if re.fullmatch(r"-?\d+", raw):
            return int(raw)
        if re.fullmatch(r"-?\d+\.\d+", raw):
            return float(raw)
        return None

    def _extract_top_level_raw_value(self, text: str, key: str) -> str | None:
        marker = f'["{key}"]='
        depth = 0
        in_string = False
        escaped = False
        index = 0

        while index < len(text):
            char = text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                index += 1
                continue

            if char == '"':
                in_string = True
                index += 1
                continue
            if char == "{":
                depth += 1
                index += 1
                continue
            if char == "}":
                depth -= 1
                index += 1
                continue

            if depth == 1 and text.startswith(marker, index):
                value_start = index + len(marker)
                value_end = self._find_value_end(text, value_start)
                return text[value_start:value_end].strip()

            index += 1

        return None

    def _extract_block(self, text: str, key: str, start: int = 0) -> str | None:
        marker = f'["{key}"]={{'
        marker_start = text.find(marker, start)
        if marker_start == -1:
            return None

        brace_index = marker_start + len(marker) - 1
        return self._read_balanced_braces(text, brace_index)

    def _read_balanced_braces(self, text: str, start_index: int) -> str | None:
        end_index = self._find_balanced_brace_end(text, start_index)
        if end_index is None:
            return None
        return text[start_index : end_index + 1]

    def _find_balanced_brace_end(self, text: str, start_index: int) -> int | None:
        depth = 0
        in_string = False
        escaped = False

        for index in range(start_index, len(text)):
            char = text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return index

        return None

    def _find_value_end(self, text: str, start_index: int) -> int:
        depth = 1
        in_string = False
        escaped = False

        for index in range(start_index, len(text)):
            char = text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue
            if char == "{":
                depth += 1
                continue
            if char == "}":
                if depth == 1:
                    return index
                depth -= 1
                continue
            if char == "," and depth == 1:
                return index

        return len(text)

    def _iter_child_blocks(self, text: str) -> list[tuple[str, str]]:
        blocks: list[tuple[str, str]] = []
        depth = 0
        in_string = False
        escaped = False
        index = 0

        while index < len(text):
            char = text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                index += 1
                continue

            if char == '"':
                in_string = True
                index += 1
                continue
            if char == "{":
                depth += 1
                index += 1
                continue
            if char == "}":
                depth -= 1
                index += 1
                continue

            if char == "[" and depth == 1:
                end_bracket = text.find("]", index)
                if end_bracket != -1 and end_bracket + 2 < len(text) and text[end_bracket + 1 : end_bracket + 3] == "={":
                    key = text[index + 1 : end_bracket]
                    brace_index = end_bracket + 2
                    end_index = self._find_balanced_brace_end(text, brace_index)
                    if end_index is not None:
                        blocks.append((key, text[brace_index : end_index + 1]))
                        index = end_index + 1
                        continue

            index += 1

        return blocks

    def _format_number(self, value: float | int) -> str:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    def _int_or_zero(self, value: object) -> int:
        return self._int_or_none(value) or 0

    def _int_or_none(self, value: object) -> int | None:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
            return int(value)
        return None

    def _string_or_none(self, value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    def _unescape(self, value: str) -> str:
        return bytes(value, "utf-8").decode("unicode_escape")
