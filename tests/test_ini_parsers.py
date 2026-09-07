from core.command_parser import parse_command_buttons, parse_command_sets
from core.ini_parser import parse_blocks
from core.mapped_image_parser import parse_mapped_images


def test_generic_blocks_tolerate_unknown_fields_and_comments():
    blocks = parse_blocks("""CommandButton Test ; comment
      Command = UNIT_BUILD
      Unknown = retained
    End
    """, {"CommandButton"})
    assert blocks[0].fields == {"Command": "UNIT_BUILD", "Unknown": "retained"}


def test_command_and_set_parsers():
    button = parse_command_buttons("""CommandButton Build_Test
    Command = UNIT_BUILD
    Object = TestTank
    TextLabel = CONTROLBAR:Test
    ButtonImage = SATest
    End""")["Build_Test"]
    command_set = parse_command_sets("""CommandSet FactorySet
    3 = Build_Test
    End""")["FactorySet"]
    assert button.object_id == "TestTank"
    assert command_set.slots == {3: "Build_Test"}


def test_mapped_image_coordinates():
    parsed = parse_mapped_images("""MappedImage SAHummer
    Texture = SAUserInterface512_005.tga
    TextureWidth = 512
    TextureHeight = 512
    Coords = Left:435 Top:101 Right:495 Bottom:149
    Status = NONE
    End""")
    assert parsed["SAHummer"].box == (435, 101, 495, 149)

