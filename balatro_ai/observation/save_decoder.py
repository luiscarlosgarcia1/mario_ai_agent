from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import zlib


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
