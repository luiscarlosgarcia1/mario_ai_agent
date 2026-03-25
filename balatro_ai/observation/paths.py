from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_BALATRO_ROOT = Path.home() / "AppData" / "Roaming" / "Balatro"


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
