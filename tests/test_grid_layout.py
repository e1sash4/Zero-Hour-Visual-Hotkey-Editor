from models import CommandButton, CommandContext
from ui.command_grid import command_grid_positions


def make(slot: int) -> CommandContext:
    return CommandContext("GLA", "Vanilla", "Producer", "Producer", "Set", slot,
                          CommandButton(f"Button{slot}"), display_name=str(slot))


def test_reference_two_row_layout_for_worker_barracks_and_arms_dealer():
    worker = [make(slot) for slot in list(range(1, 11)) + [13, 14]]
    positions = command_grid_positions(worker)
    assert positions[worker[0].identity] == (0, 0)
    assert positions[worker[4].identity] == (0, 4)
    assert positions[worker[5].identity] == (1, 0)
    assert positions[worker[9].identity] == (1, 4)
    assert positions[worker[10].identity] == (0, 6)
    assert positions[worker[11].identity] == (1, 6)

    barracks = [make(slot) for slot in list(range(1, 9)) + [11, 13, 14]]
    positions = command_grid_positions(barracks)
    assert positions[barracks[3].identity] == (0, 3)
    assert positions[barracks[4].identity] == (1, 0)
    assert positions[barracks[8].identity] == (0, 5)

    arms = [make(slot) for slot in range(1, 15)]
    positions = command_grid_positions(arms)
    assert positions[arms[10].identity] == (0, 5)
    assert positions[arms[11].identity] == (1, 5)


def test_vanilla_gla_override_matches_reference_order():
    def gla(button_id: str, slot: int) -> CommandContext:
        return CommandContext("GLA", "Vanilla", "GLAInfantryWorker", "Worker", "GLAWorkerCommandSet", slot,
                              CommandButton(button_id), display_name=button_id)
    stash = gla("Command_ConstructGLASupplyStash", 1)
    demo = gla("Command_ConstructGLADemoTrap", 2)
    arms = gla("Command_ConstructGLAArmsDealer", 9)
    tunnel = gla("Command_ConstructGLATunnelNetwork", 7)
    positions = command_grid_positions([stash, demo, arms, tunnel])
    assert positions[stash.identity] == (0, 0)
    assert positions[arms.identity] == (0, 4)
    assert positions[demo.identity] == (1, 0)
    assert positions[tunnel.identity] == (0, 3)


def test_active_action_layout_supports_a_third_row():
    button = CommandButton(
        "Command_ConstructAmericaVehicleScoutDrone",
        text_label="CONTROLBAR:ConstructAmericaVehicleScoutDrone",
    )
    context = CommandContext(
        "USA", "Vanilla", "ActiveActions/USA/Vanilla/Unit Actions", "Unit Actions",
        "AmericaVehicleHumveeCommandSet", 11, button, display_name="Scout Drone",
    )

    assert command_grid_positions([context])[context.identity] == (2, 2)
