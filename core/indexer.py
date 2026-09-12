from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path

from models import CommandContext, GameDatabase
from .archive_index import ArchiveIndex
from .asset_manager import AssetManager
from .command_parser import parse_command_buttons, parse_command_sets, parse_objects
from .csf_parser import CsfFile, CsfFormatError
from .ini_parser import decode_ini
from .mapped_image_parser import parse_mapped_images


GENERAL_PREFIXES = {
    "AirF_": ("USA", "Air Force"), "Lazr_": ("USA", "Laser"), "SupW_": ("USA", "Superweapon"),
    "Tank_": ("China", "Tank"), "Infa_": ("China", "Infantry"), "Nuke_": ("China", "Nuclear"),
    "Chem_": ("GLA", "Toxin"), "Slth_": ("GLA", "Stealth"), "Demo_": ("GLA", "Demolition"),
}

GLA_FAKE_WORKER_SETS = {
    ("GLA", "Vanilla"): ("GLAWorkerCommandSet", "GLAWorkerFakeBuildingsCommandSet"),
    ("GLA", "Toxin"): ("Chem_GLAWorkerCommandSet", "Chem_GLAWorkerFakeBuildingsCommandSet"),
    ("GLA", "Stealth"): ("Slth_GLAWorkerCommandSet", "Slth_GLAWorkerFakeBuildingsCommandSet"),
    ("GLA", "Demolition"): ("Demo_GLAWorkerCommandSet", "Demo_GLAWorkerFakeBuildingsCommandSet"),
}

GENERAL_POWER_COMMAND_SETS = {
    ("USA", "Vanilla"): "AmericaCommandCenterCommandSet",
    ("USA", "Air Force"): "AirF_AmericaCommandCenterCommandSet",
    ("USA", "Laser"): "Lazr_AmericaCommandCenterCommandSet",
    ("USA", "Superweapon"): "SupW_AmericaCommandCenterCommandSet",
    ("China", "Vanilla"): "ChinaCommandCenterCommandSet",
    ("China", "Tank"): "Tank_ChinaCommandCenterCommandSet",
    ("China", "Infantry"): "Infa_ChinaCommandCenterCommandSet",
    ("China", "Nuclear"): "Nuke_ChinaCommandCenterCommandSet",
    ("GLA", "Vanilla"): "GLACommandCenterCommandSet",
    ("GLA", "Toxin"): "Chem_GLACommandCenterCommandSet",
    ("GLA", "Stealth"): "Slth_GLACommandCenterCommandSet",
    ("GLA", "Demolition"): "Demo_GLACommandCenterCommandSet",
}

GENERAL_POWER_EXCLUSIONS = {
    ("China", "Vanilla"): {"Command_NapalmStrike"},
    ("China", "Nuclear"): {"Command_NapalmStrike"},
}

# These are grouped by what the player is controlling instead of by each
# individual Object/CommandSet. Every card still uses a real CommandButton,
# its CSF label and its original in-game MappedImage.
ACTIVE_ACTION_GROUPS = {
    "USA": {
        "Unit Actions": (
            "CONTROLBAR:AttackMove", "CONTROLBAR:Guard", "CONTROLBAR:GuardFlyingUnitsOnly",
            "CONTROLBAR:Stop", "CONTROLBAR:DisarmMinesAtPosition", "CONTROLBAR:AmbulanceCleanupArea",
            "CONTROLBAR:FireRocketPods", "CONTROLBAR:LaserMissileAttack",
            "CONTROLBAR:ConstructAmericaVehicleBattleDrone",
            "CONTROLBAR:ConstructAmericaVehicleHellfireDrone",
            "CONTROLBAR:ConstructAmericaVehicleScoutDrone", "CONTROLBAR:Evacuate",
        ),
        "Building Actions": (
            "CONTROLBAR:Sell", "CONTROLBAR:SetRallyPoint", "CONTROLBAR:Evacuate",
        ),
        "Infantry Actions": (
            "CONTROLBAR:KnifeAttack", "CONTROLBAR:TimedDemoCharge", "CONTROLBAR:RemoteDemoCharge",
            "CONTROLBAR:DetonateCharges", "CONTROLBAR:FlashBangGrenadeMode",
            "CONTROLBAR:RangerMachineGun", "CONTROLBAR:CaptureBuilding",
        ),
    },
    "China": {
        "Unit Actions": (
            "CONTROLBAR:AttackMove", "CONTROLBAR:Guard", "CONTROLBAR:GuardFlyingUnitsOnly",
            "CONTROLBAR:Stop", "CONTROLBAR:DisarmMinesAtPosition", "CONTROLBAR:FireWall",
            "CONTROLBAR:ECMDisableVehicle", "CONTROLBAR:DropNapalmBomb", "CONTROLBAR:DropNukeBomb",
            "CONTROLBAR:NeutronWarhead", "CONTROLBAR:NukeWarhead", "CONTROLBAR:Evacuate",
            "CONTROLBAR:TransportExit",
        ),
        "Building Actions": (
            "CONTROLBAR:Sell", "CONTROLBAR:SetRallyPoint", "CONTROLBAR:Evacuate",
            "CONTROLBAR:BunkerExit", "CONTROLBAR:StructureExit", "CONTROLBAR:Stop",
            "CONTROLBAR:Overcharge",
        ),
        "Infantry Actions": (
            "CONTROLBAR:CaptureBuilding", "CONTROLBAR:TNTAttack", "CONTROLBAR:InternetHack",
            "CONTROLBAR:DisableBuildingHack", "CONTROLBAR:DisableVehicleHack",
            "CONTROLBAR:StealCashHack",
        ),
    },
    "GLA": {
        "Unit Actions": (
            "CONTROLBAR:AttackMove", "CONTROLBAR:Guard", "CONTROLBAR:Stop",
            "CONTROLBAR:DisarmMinesAtPosition", "CONTROLBAR:Contaminate",
            "CONTROLBAR:DetonateBombTruck", "CONTROLBAR:DisguiseAsVehicle",
            "CONTROLBAR:RadarVanScan", "CONTROLBAR:AnthraxWarhead",
            "CONTROLBAR:ExplosiveWarhead", "CONTROLBAR:Evacuate", "CONTROLBAR:TransportExit",
        ),
        "Building Actions": (
            "CONTROLBAR:Sell", "CONTROLBAR:SetRallyPoint", "CONTROLBAR:Evacuate",
            "CONTROLBAR:StructureExit", "CONTROLBAR:Stop", "CONTROLBAR:DetonateFakeBuilding",
            "CONTROLBAR:ProximityFuse", "CONTROLBAR:ManualControl", "CONTROLBAR:Detonate",
        ),
        "Infantry Actions": (
            "CONTROLBAR:CaptureBuilding", "CONTROLBAR:BoobyTrapAttack", "CONTROLBAR:CarBomb",
            "CONTROLBAR:Hijack", "CONTROLBAR:SabotageBuilding", "CONTROLBAR:SniperAttack",
            "CONTROLBAR:TimedDemoCharge", "CONTROLBAR:RemoteDemoCharge",
            "CONTROLBAR:DetonateCharges", "CONTROLBAR:SuicideAttack",
        ),
    },
}

FACTION_GENERALS = {
    "USA": ("Vanilla", "Air Force", "Laser", "Superweapon"),
    "China": ("Vanilla", "Tank", "Infantry", "Nuclear"),
    "GLA": ("Vanilla", "Toxin", "Stealth", "Demolition"),
}

NON_ACTION_COMMANDS = {
    "UNIT_BUILD", "PLAYER_UPGRADE", "DOZER_CONSTRUCT",
    "DOZER_CONSTRUCT_CANCEL", "PURCHASE_SCIENCE", "SPECIAL_POWER_FROM_SHORTCUT",
}


def _is_active_button(button) -> bool:
    return bool(
        button and button.text_label and button.button_image
        and button.command not in NON_ACTION_COMMANDS
        and "NEED_SPECIAL_POWER_SCIENCE" not in button.fields.get("Options", "").split()
    )


def append_active_action_groups(
        db: GameDatabase, csf: CsfFile, allowed_producers: dict[str, set[str]] | None = None,
        visible_layouts: dict[str, dict[str, list[int]]] | None = None) -> None:
    """Expose active commands once per faction general in three virtual pages."""
    allowed_producers = allowed_producers or {}
    visible_layouts = visible_layouts or {}
    objects = sorted(db.objects.values(), key=lambda item: item.id)
    buildable_objects = {
        button.object_id for button in db.buttons.values()
        if button.command == "UNIT_BUILD" and button.object_id
    }
    for faction, groups in ACTIVE_ACTION_GROUPS.items():
        for general in FACTION_GENERALS[faction]:
            for group_name, labels in groups.items():
                page_id = f"ActiveActions/{faction}/{general}/{group_name}"
                allowed = allowed_producers.get(f"{faction}/{general}")
                if allowed is not None and page_id not in allowed:
                    continue
                layout = visible_layouts.get(page_id)
                layout_keys = {key.casefold() for key in layout} if layout is not None else set()
                wanted = {label.casefold() for label in labels}
                unit_labels = {
                    label.casefold() for label in groups["Unit Actions"]
                }
                found = {}
                for obj in objects:
                    if classify(obj.id, obj.command_set) != (faction, general):
                        continue
                    if "SELECTABLE" not in obj.kind_of:
                        continue
                    if group_name == "Building Actions" and "STRUCTURE" not in obj.kind_of:
                        continue
                    if group_name != "Building Actions" and "STRUCTURE" in obj.kind_of:
                        continue
                    if group_name == "Infantry Actions" and "INFANTRY" not in obj.kind_of:
                        continue
                    command_set = db.command_sets.get(obj.command_set)
                    if not command_set:
                        continue
                    for game_slot, button_id in sorted(command_set.slots.items()):
                        button = db.buttons.get(button_id)
                        folded = button.text_label.casefold() if button else ""
                        configured = bool(button and (
                            button.id.casefold() in layout_keys or folded in layout_keys
                        ))
                        discovered = (group_name != "Building Actions" and obj.id in buildable_objects
                                      and _is_active_button(button))
                        if group_name == "Unit Actions" and "INFANTRY" in obj.kind_of and folded not in wanted:
                            discovered = False
                        if group_name == "Infantry Actions" and folded in unit_labels:
                            discovered = False
                        if (folded in wanted or discovered or configured) and folded not in found:
                            found[folded] = (command_set, game_slot, button)

                # Some stock objects contain a malformed CommandSet reference,
                # so correctly classified command sets are a safe fallback.
                for command_set in sorted(db.command_sets.values(), key=lambda item: item.id):
                    fallback_faction = classify(command_set.id, command_set.id)
                    vanilla_gla_fake = (faction, general) == ("GLA", "Vanilla") \
                        and command_set.id.startswith("FakeGLA")
                    if fallback_faction != (faction, general) and not vanilla_gla_fake:
                        continue
                    for game_slot, button_id in sorted(command_set.slots.items()):
                        button = db.buttons.get(button_id)
                        folded = button.text_label.casefold() if button else ""
                        configured = bool(button and (
                            button.id.casefold() in layout_keys or folded in layout_keys
                        ))
                        if (folded in wanted or configured) and folded not in found:
                            found[folded] = (command_set, game_slot, button)

                discovered_labels = sorted(
                    (button.text_label for folded, (_command_set, _slot, button) in found.items()
                     if folded not in wanted),
                    key=lambda label: (csf.get(label) or label).replace("&", "").casefold(),
                )
                ordered_labels = (*labels, *discovered_labels)
                for visual_slot, label in enumerate(ordered_labels, 1):
                    match = found.get(label.casefold())
                    if not match:
                        continue
                    command_set, _game_slot, button = match
                    if layout is not None and (button.id.casefold() not in layout_keys
                                               and button.text_label.casefold() not in layout_keys):
                        continue
                    localized = csf.get(button.text_label)
                    display = localized.replace("&", "") if localized else friendly_identifier(button.id)
                    db.contexts.append(CommandContext(
                        faction, general, page_id,
                        group_name, command_set.id, visual_slot, button, None, display,
                    ))


class CsfLoadError(ValueError):
    def __init__(self, path: Path, loose_override: bool, reason: Exception):
        super().__init__(str(reason))
        self.path = path
        self.loose_override = loose_override
        self.reason = reason


def producer_overrides() -> dict[str, set[str]]:
    path = Path(__file__).resolve().parents[1] / "data/overrides/producers.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {key: set(values) for key, values in raw.items()}
    except (OSError, ValueError, TypeError):
        logging.getLogger(__name__).warning("Could not read producer overrides from %s", path)
        return {}


def layout_overrides() -> dict[str, dict[str, list[int]]]:
    path = Path(__file__).resolve().parents[1] / "data/overrides/layouts.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def classify(object_id: str, command_set_id: str = "") -> tuple[str, str]:
    # General prefixes are authoritative. Challenge (GC_), cinematic (CINE_)
    # and boss/debug objects must never leak into stock faction databases.
    for prefix, result in GENERAL_PREFIXES.items():
        if object_id.startswith(prefix) or command_set_id.startswith(prefix):
            return result
    if object_id.startswith("America"):
        return "USA", "Vanilla"
    if object_id.startswith("China"):
        return "China", "Vanilla"
    if object_id.startswith("GLA"):
        return "GLA", "Vanilla"
    return "", ""


def friendly_identifier(value: str) -> str:
    for prefix in ("AirF_", "Lazr_", "SupW_", "Tank_", "Infa_", "Nuke_", "Chem_", "Slth_", "Demo_", "America", "China", "GLA"):
        value = value.removeprefix(prefix)
    value = value.replace("CommandSet", "")
    value = re_sub_camel(value)
    return value.strip() or "Commands"


def re_sub_camel(value: str) -> str:
    import re
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value).replace("_", " ")


class GameIndexer:
    def __init__(self, game_dir: str | Path, app_root: str | Path):
        self.game_dir = Path(game_dir)
        self.app_root = Path(app_root)
        self.resources = ArchiveIndex(self.game_dir)
        # Keep the archive copy separate from a loose, user-modified override.
        # It is the authoritative source for the built-in Game Default profile
        # and for restoring the installation default.
        self.csf_source = self.resources.read_archive(r"Data\English\generals.csf")
        try:
            archive_csf = CsfFile.from_bytes(self.csf_source)
        except (CsfFormatError, UnicodeError) as exc:
            raise CsfLoadError(self.game_dir / "EnglishZH.big", False, exc) from exc
        loose = self.game_dir / "Data/English/generals.csf"
        if loose.is_file():
            try:
                self.csf = CsfFile.from_bytes(loose.read_bytes())
            except (CsfFormatError, UnicodeError) as exc:
                raise CsfLoadError(loose, True, exc) from exc
        else:
            self.csf = archive_csf

    def build(self, progress: Callable[[int, str], None] | None = None) -> tuple[GameDatabase, CsfFile, AssetManager]:
        report = progress or (lambda _percent, _message: None)
        db = GameDatabase(self.game_dir, self.game_dir / "EnglishZH.big", r"Data\English\generals.csf")
        ini_archive = next(a for a in self.resources.archives if a.path.name.casefold() == "inizh.big")
        report(10, "Reading MappedImages")
        for entry in ini_archive.entries:
            lower = entry.name.casefold()
            if "\\mappedimages\\" in lower and lower.endswith(".ini"):
                db.mapped_images.update(parse_mapped_images(decode_ini(ini_archive.read(entry)), entry.name))
        report(28, "Reading CommandButtons")
        for entry in ini_archive.entries:
            lower = entry.name.casefold()
            if lower.endswith("commandbutton.ini"):
                db.buttons.update(parse_command_buttons(decode_ini(ini_archive.read(entry)), entry.name))
        report(42, "Reading CommandSets")
        for entry in ini_archive.entries:
            if entry.name.casefold().endswith("commandset.ini"):
                db.command_sets.update(parse_command_sets(decode_ini(ini_archive.read(entry)), entry.name))
        report(56, "Reading Object INI")
        for entry in ini_archive.entries:
            lower = entry.name.casefold()
            if "\\object\\" in lower and lower.endswith(".ini") or lower.endswith("\\default\\object.ini"):
                db.objects.update(parse_objects(decode_ini(ini_archive.read(entry)), entry.name))
        report(68, "Building command database")
        csf_labels = self.csf.by_name()
        assets = AssetManager(self.resources, db.mapped_images, self.app_root / "cache/icons")
        allowed_producers = producer_overrides()
        visible_layouts = layout_overrides()
        used_contexts: set[tuple[str, str]] = set()
        for obj in db.objects.values():
            command_set = db.command_sets.get(obj.command_set)
            faction, general = classify(obj.id, obj.command_set)
            # The visual editor focuses on the same producer/category command
            # bars the user sees while building: structures and builders only.
            if (not command_set or not faction or not ({"STRUCTURE", "DOZER"} & obj.kind_of)
                    or "Fake" in obj.id):
                continue
            allowed = allowed_producers.get(f"{faction}/{general}")
            if allowed is not None and obj.command_set not in allowed:
                continue
            producer_label = self.csf.get(obj.display_name) if obj.display_name else None
            producer_name = (producer_label or friendly_identifier(obj.id)).replace("&", "")
            for slot, button_id in sorted(command_set.slots.items()):
                button = db.buttons.get(button_id)
                if not button or not button.text_label or not button.button_image:
                    continue
                # General powers are conditionally injected into Command Center
                # command sets, but are not part of the normal producer bar shown
                # in the user's reference layout.
                if "NEED_SPECIAL_POWER_SCIENCE" in button.fields.get("Options", "").split():
                    continue
                # Once a CommandSet is explicitly listed in layouts.json, that
                # file is also the visibility whitelist for its cards.
                if obj.command_set in visible_layouts and button_id not in visible_layouts[obj.command_set]:
                    continue
                unique = (faction, general, obj.command_set, button_id)
                if unique in used_contexts:
                    continue
                used_contexts.add(unique)
                localized = self.csf.get(button.text_label)
                display = localized.replace("&", "") if localized else friendly_identifier(button.object_id or button.id)
                context = CommandContext(faction, general, obj.id, producer_name, obj.command_set, slot, button, None, display)
                db.contexts.append(context)
                if button.text_label.casefold() not in csf_labels:
                    db.warnings.append(f"Missing CSF label: {button.text_label}")

        # General powers are injected into the Command Center command bar only
        # after their corresponding sciences are purchased. Keep them in their
        # real CommandSet conflict context, but expose them as a dedicated page
        # so users can edit their actual CSF shortcuts without UI clutter.
        for (faction, general), command_set_id in GENERAL_POWER_COMMAND_SETS.items():
            command_set = db.command_sets.get(command_set_id)
            if not command_set:
                continue
            excluded = GENERAL_POWER_EXCLUSIONS.get((faction, general), set())
            powers = []
            for _game_slot, button_id in sorted(command_set.slots.items()):
                button = db.buttons.get(button_id)
                if (button_id not in excluded and button and button.text_label and button.button_image
                        and "NEED_SPECIAL_POWER_SCIENCE" in button.fields.get("Options", "").split()):
                    powers.append((button_id, button))
            for visual_slot, (button_id, button) in enumerate(powers, 1):
                unique = (faction, general, command_set_id, button_id)
                if unique in used_contexts:
                    continue
                used_contexts.add(unique)
                localized = self.csf.get(button.text_label)
                display = localized.replace("&", "") if localized else friendly_identifier(button.id)
                db.contexts.append(CommandContext(
                    faction, general, "__general_powers__", "General Powers",
                    command_set_id, visual_slot, button, None, display,
                ))
                if button.text_label.casefold() not in csf_labels:
                    db.warnings.append(f"Missing CSF label: {button.text_label}")

        # Workers switch to these command sets dynamically through an upgrade,
        # so no Object definition points at them directly. Add a virtual
        # producer page to expose both the fake construction commands and the
        # button that switches the worker back to its real structures.
        for (faction, general), (worker_set_id, fake_set_id) in GLA_FAKE_WORKER_SETS.items():
            fake_set = db.command_sets.get(fake_set_id)
            worker = next((obj for obj in db.objects.values() if obj.command_set == worker_set_id
                           and "DOZER" in obj.kind_of and not obj.id.startswith(("GC_", "CINE_"))), None)
            allowed = allowed_producers.get(f"{faction}/{general}")
            if not fake_set or not worker or (allowed is not None and fake_set_id not in allowed):
                continue
            worker_label = self.csf.get(worker.display_name) if worker.display_name else None
            producer_name = f"{(worker_label or 'Worker').replace('&', '')} — Fake Structures"
            for slot, button_id in sorted(fake_set.slots.items()):
                button = db.buttons.get(button_id)
                if not button or not button.text_label or not button.button_image:
                    continue
                if fake_set_id in visible_layouts and button_id not in visible_layouts[fake_set_id]:
                    continue
                unique = (faction, general, fake_set_id, button_id)
                if unique in used_contexts:
                    continue
                used_contexts.add(unique)
                localized = self.csf.get(button.text_label)
                display = localized.replace("&", "") if localized else friendly_identifier(button.object_id or button.id)
                db.contexts.append(CommandContext(
                    faction, general, worker.id, producer_name, fake_set_id, slot, button, None, display
                ))
                if button.text_label.casefold() not in csf_labels:
                    db.warnings.append(f"Missing CSF label: {button.text_label}")
        append_active_action_groups(db, self.csf, allowed_producers, visible_layouts)
        report(78, "Extracting referenced icons")
        required = {item.button.button_image for item in db.contexts}
        for number, image_id in enumerate(sorted(required), 1):
            path = assets.get_icon(image_id)
            if path:
                for context in db.contexts:
                    if context.button.button_image == image_id:
                        context.icon_path = path
            if number % 20 == 0:
                report(78 + int(21 * number / max(1, len(required))), f"Building icon cache ({number}/{len(required)})")
        report(100, "Ready")
        logging.getLogger(__name__).info("Indexed %d contexts, %d images, %d objects", len(db.contexts), len(db.mapped_images), len(db.objects))
        return db, self.csf, assets
