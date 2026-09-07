from __future__ import annotations

from dataclasses import dataclass

from models import CommandContext
from .csf_parser import CsfFile, extract_hotkey, set_hotkey_marker


VALID_KEYS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
DEFAULT_MOUSE_KEYS = {"M3": "7", "M4": "8", "M5": "9"}
LEGACY_MOUSE_KEYS = {"M3": "8", "M4": "9", "M5": "0"}
MOUSE_BUTTONS = tuple(DEFAULT_MOUSE_KEYS)
VALID_BINDINGS = VALID_KEYS | set(MOUSE_BUTTONS)
FALLBACK_HOTKEYS = {"controlbar:sell": "L"}


@dataclass(frozen=True, slots=True)
class HotkeyChange:
    label: str
    before: str | None
    after: str | None


class HotkeyManager:
    def __init__(self, csf: CsfFile, contexts: list[CommandContext],
                 mouse_bindings: dict[str, str] | None = None,
                 mouse_keys: dict[str, str] | None = None):
        self.csf = csf
        self.contexts = contexts
        self.mouse_keys = dict(mouse_keys or DEFAULT_MOUSE_KEYS)
        if set(self.mouse_keys) != set(MOUSE_BUTTONS) or not set(self.mouse_keys.values()) <= VALID_KEYS:
            raise ValueError("Invalid mouse proxy key configuration")
        if len(set(self.mouse_keys.values())) != len(self.mouse_keys):
            raise ValueError("Mouse proxy keys must be unique")
        self.mouse_bindings = {
            str(label).casefold(): str(button).upper()
            for label, button in (mouse_bindings or {}).items()
            if str(button).upper() in MOUSE_BUTTONS
        }
        self.pending: dict[str, str | None] = {}
        self.undo_stack: list[list[HotkeyChange]] = []
        self.redo_stack: list[list[HotkeyChange]] = []

    def get_hotkey(self, command: CommandContext) -> str | None:
        label = command.button.text_label.casefold()
        if label in self.pending:
            return self.pending[label]
        text = self.csf.get(command.button.text_label)
        parsed = extract_hotkey(text) if text else None
        mouse = self.mouse_bindings.get(label)
        if mouse and parsed == self.mouse_keys[mouse]:
            return mouse
        return parsed or FALLBACK_HOTKEYS.get(label)

    def storage_key(self, binding: str | None) -> str | None:
        return self.mouse_keys.get(binding or "", binding)

    def set_mouse_proxy_keys(self, mouse_keys: dict[str, str]) -> None:
        normalized = {button: key.upper() for button, key in mouse_keys.items()}
        if set(normalized) != set(MOUSE_BUTTONS) or not set(normalized.values()) <= VALID_KEYS:
            raise ValueError("Invalid mouse proxy key configuration")
        if len(set(normalized.values())) != len(normalized):
            raise ValueError("Mouse proxy keys must be unique")
        for label, button in self.mouse_bindings.items():
            if self.mouse_keys[button] != normalized[button]:
                self.pending[label] = button
        self.mouse_keys = normalized

    def set_hotkey(self, command: CommandContext, key: str | None) -> None:
        if key:
            key = key.upper()
            if key not in VALID_BINDINGS:
                raise ValueError("Zero Hour hotkeys support A-Z, 0-9, M3, M4 and M5")
            text = self.csf.get(command.button.text_label)
            if text is None:
                raise KeyError(command.button.text_label)
            set_hotkey_marker(text, self.storage_key(key))  # Validate before queuing.
        label = command.button.text_label.casefold()
        before = self.get_hotkey(command)
        if before == key:
            return
        self.pending[label] = key
        self.undo_stack.append([HotkeyChange(label, before, key)])
        self.redo_stack.clear()

    def clear_all(self) -> int:
        """Queue removal of every command-bar hotkey as one undoable action."""
        changes: list[HotkeyChange] = []
        seen: set[str] = set()
        for command in self.contexts:
            label = command.button.text_label.casefold()
            if not label or label in seen:
                continue
            seen.add(label)
            before = self.get_hotkey(command)
            if before is None:
                continue
            self.pending[label] = None
            changes.append(HotkeyChange(label, before, None))
        if changes:
            self.undo_stack.append(changes)
            self.redo_stack.clear()
        return len(changes)

    def clear_key(self, key: str) -> int:
        """Queue removal of every CSF command using *key* as one undoable action."""
        key = key.upper()
        changes: list[HotkeyChange] = []
        seen: set[str] = set()
        for command in self.contexts:
            label = command.button.text_label.casefold()
            if not label or label in seen or self.get_hotkey(command) != key:
                continue
            seen.add(label)
            self.pending[label] = None
            changes.append(HotkeyChange(label, key, None))
        if changes:
            self.undo_stack.append(changes)
            self.redo_stack.clear()
        return len(changes)

    def get_linked_commands(self, command: CommandContext) -> list[CommandContext]:
        label = command.button.text_label.casefold()
        return [item for item in self.contexts if item.button.text_label.casefold() == label]

    def get_conflicts(self, command: CommandContext, key: str) -> list[CommandContext]:
        key = key.upper()
        return [item for item in self.contexts
                if item.identity != command.identity and item.command_set_id == command.command_set_id
                and item.button.text_label.casefold() != command.button.text_label.casefold()
                and self.storage_key(self.get_hotkey(item)) == self.storage_key(key)]

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        changes = self.undo_stack.pop()
        for change in changes:
            self.pending[change.label] = change.before
        self.redo_stack.append(changes)
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        changes = self.redo_stack.pop()
        for change in changes:
            self.pending[change.label] = change.after
        self.undo_stack.append(changes)
        return True

    def materialize(self) -> CsfFile:
        labels = self.csf.by_name()
        for folded, key in self.pending.items():
            label = labels.get(folded)
            if not label or not label.values:
                continue
            label.values[0].text = set_hotkey_marker(label.values[0].text, self.storage_key(key))
            if key in MOUSE_BUTTONS:
                self.mouse_bindings[folded] = key
            else:
                self.mouse_bindings.pop(folded, None)
        return self.csf
