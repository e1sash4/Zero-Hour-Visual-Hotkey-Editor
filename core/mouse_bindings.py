from __future__ import annotations

import json
from pathlib import Path

from .hotkey_manager import MOUSE_BUTTONS, VALID_KEYS


class MouseBindingStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict[str, str]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            bindings = payload.get("bindings", {})
            if not isinstance(bindings, dict):
                return {}
            return {
                str(label).casefold(): str(button).upper()
                for label, button in bindings.items()
                if str(button).upper() in MOUSE_BUTTONS
            }
        except (OSError, ValueError, TypeError):
            return {}

    def load_proxies(self) -> dict[str, str]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            proxies = payload.get("proxies", {})
            if (not isinstance(proxies, dict) or set(proxies) != set(MOUSE_BUTTONS)
                    or not {str(value).upper() for value in proxies.values()} <= VALID_KEYS):
                return {}
            normalized = {str(button): str(key).upper() for button, key in proxies.items()}
            return normalized if len(set(normalized.values())) == len(normalized) else {}
        except (OSError, ValueError, TypeError):
            return {}

    def save(self, bindings: dict[str, str], proxies: dict[str, str] | None = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "bindings": dict(sorted(bindings.items()))}
        if proxies:
            payload["proxies"] = dict(proxies)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)
