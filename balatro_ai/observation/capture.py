from __future__ import annotations

from dataclasses import dataclass


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
