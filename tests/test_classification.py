from core.csf_parser import CsfFile, CsfLabel, CsfValue
from core.indexer import append_active_action_groups, classify, layout_overrides, producer_overrides
from models import CommandButton, CommandSet, GameDatabase, ObjectDefinition
from pathlib import Path


def test_stock_and_general_classification_excludes_challenge_cine_and_boss():
    assert classify("GLAArmsDealer", "GLAArmsDealerCommandSet") == ("GLA", "Vanilla")
    assert classify("Chem_GLAArmsDealer", "Chem_GLAArmsDealerCommandSet") == ("GLA", "Toxin")
    assert classify("GC_Chem_GLAArmsDealer", "GC_Chem_GLAArmsDealerCommandSet") == ("", "")
    assert classify("Boss_TunnelNetwork", "Boss_GLATunnelNetworkCommandSet") == ("", "")
    assert classify("CINE_GLAInfantryWorker", "GLAWorkerCommandSet") == ("", "")


def test_vanilla_gla_uses_only_reference_producer_panels():
    assert {
        "GLAWorkerCommandSet",
        "GLACommandCenterCommandSet",
        "GLABarracksCommandSet",
        "GLAArmsDealerCommandSet",
    } <= producer_overrides()["GLA/Vanilla"]


def test_usa_active_actions_are_grouped_and_keep_real_command_buttons():
    db = GameDatabase(Path("game"))
    db.buttons = {
        "Attack": CommandButton("Attack", button_image="SSAttackMove2", text_label="CONTROLBAR:AttackMove"),
        "Sell": CommandButton("Sell", button_image="SSSell2", text_label="CONTROLBAR:Sell"),
        "Knife": CommandButton("Knife", button_image="SSKnifeAttack", text_label="CONTROLBAR:KnifeAttack"),
    }
    db.command_sets = {
        "VehicleSet": CommandSet("VehicleSet", {1: "Attack"}),
        "BuildingSet": CommandSet("BuildingSet", {1: "Sell"}),
        "InfantrySet": CommandSet("InfantrySet", {1: "Knife"}),
    }
    db.objects = {
        "AmericaTank": ObjectDefinition("AmericaTank", "VehicleSet", kind_of={"SELECTABLE", "VEHICLE"}),
        "AmericaBase": ObjectDefinition("AmericaBase", "BuildingSet", kind_of={"SELECTABLE", "STRUCTURE"}),
        "AmericaSoldier": ObjectDefinition("AmericaSoldier", "InfantrySet", kind_of={"SELECTABLE", "INFANTRY"}),
    }
    csf = CsfFile(labels=[
        CsfLabel("CONTROLBAR:AttackMove", [CsfValue("&Attack Move")]),
        CsfLabel("CONTROLBAR:Sell", [CsfValue("Se&ll")]),
        CsfLabel("CONTROLBAR:KnifeAttack", [CsfValue("&Knife Attack")]),
    ])

    append_active_action_groups(db, csf)

    assert [(item.producer_name, item.display_name, item.button.button_image) for item in db.contexts] == [
        ("Unit Actions", "Attack Move", "SSAttackMove2"),
        ("Building Actions", "Sell", "SSSell2"),
        ("Infantry Actions", "Knife Attack", "SSKnifeAttack"),
    ]


def test_china_and_gla_specific_active_abilities_are_exposed():
    db = GameDatabase(Path("game"))
    db.buttons = {
        "FireWall": CommandButton(
            "FireWall", command="FIRE_WEAPON", button_image="SSFireStorm",
            text_label="CONTROLBAR:FireWall",
        ),
        "Hijack": CommandButton(
            "Hijack", command="HIJACK_VEHICLE", button_image="SSCarjack",
            text_label="CONTROLBAR:Hijack",
        ),
        "Detonate": CommandButton(
            "Detonate", command="SWITCH_WEAPON", button_image="SSDetonateDemo",
            text_label="CONTROLBAR:Detonate",
        ),
    }
    db.command_sets = {
        "ChinaDragonSet": CommandSet("ChinaDragonSet", {1: "FireWall"}),
        "GLAHijackerSet": CommandSet("GLAHijackerSet", {1: "Hijack"}),
        "DemoTrapSet": CommandSet("DemoTrapSet", {1: "Detonate"}),
    }
    db.objects = {
        "ChinaTankDragon": ObjectDefinition(
            "ChinaTankDragon", "ChinaDragonSet", kind_of={"SELECTABLE", "VEHICLE"},
        ),
        "GLAInfantryHijacker": ObjectDefinition(
            "GLAInfantryHijacker", "GLAHijackerSet", kind_of={"SELECTABLE", "INFANTRY"},
        ),
        "Demo_GLADemoTrap": ObjectDefinition(
            "Demo_GLADemoTrap", "DemoTrapSet", kind_of={"SELECTABLE", "STRUCTURE"},
        ),
    }
    csf = CsfFile(labels=[
        CsfLabel("CONTROLBAR:FireWall", [CsfValue("&Fire Wall")]),
        CsfLabel("CONTROLBAR:Hijack", [CsfValue("Hi&jack")]),
        CsfLabel("CONTROLBAR:Detonate", [CsfValue("&Detonate!")]),
    ])

    append_active_action_groups(db, csf)

    assert {(item.faction, item.general, item.producer_name, item.display_name) for item in db.contexts} == {
        ("China", "Vanilla", "Unit Actions", "Fire Wall"),
        ("GLA", "Vanilla", "Infantry Actions", "Hijack"),
        ("GLA", "Demolition", "Building Actions", "Detonate!"),
    }


def test_active_pages_are_configurable_through_producer_and_layout_overrides():
    producers = producer_overrides()
    layouts = layout_overrides()

    for faction, generals in {
        "USA": ("Vanilla", "Air Force", "Laser", "Superweapon"),
        "China": ("Vanilla", "Tank", "Infantry", "Nuclear"),
        "GLA": ("Vanilla", "Toxin", "Stealth", "Demolition"),
    }.items():
        for general in generals:
            page_ids = {
                f"ActiveActions/{faction}/{general}/Unit Actions",
                f"ActiveActions/{faction}/{general}/Building Actions",
                f"ActiveActions/{faction}/{general}/Infantry Actions",
            }
            assert page_ids <= producers[f"{faction}/{general}"]
            assert page_ids <= layouts.keys()
            for page_id in page_ids:
                positions = [tuple(position) for position in layouts[page_id].values()]
                assert len(positions) == len(set(positions))
                assert all(row >= 0 and column >= 0 for row, column in positions)

    assert layouts["ActiveActions/USA/Air Force/Unit Actions"]["CONTROLBAR:Evacuate"] == [2, 3]


def test_active_layout_can_add_an_action_by_button_id():
    db = GameDatabase(Path("game"))
    db.buttons = {
        "CustomBuildingAction": CommandButton(
            "CustomBuildingAction", command="OBJECT_UPGRADE", button_image="CustomImage",
            text_label="CONTROLBAR:CustomBuildingAction",
        ),
    }
    db.command_sets = {
        "GLABuildingSet": CommandSet("GLABuildingSet", {1: "CustomBuildingAction"}),
    }
    db.objects = {
        "GLABuilding": ObjectDefinition(
            "GLABuilding", "GLABuildingSet", kind_of={"SELECTABLE", "STRUCTURE"},
        ),
    }
    layouts = {
        "ActiveActions/GLA/Vanilla/Building Actions": {
            "CustomBuildingAction": [0, 0],
        },
    }

    append_active_action_groups(db, CsfFile(), visible_layouts=layouts)

    assert [(item.producer_name, item.button.id) for item in db.contexts] == [
        ("Building Actions", "CustomBuildingAction"),
    ]
