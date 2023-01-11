from .conftest import params

import pytest

from tuindow import Panel
from tuindow import structs
from tuindow import AttributeBit
from tuindow import cursor


@pytest.fixture
def panel():
    return Panel(1, 2, 3, 4)


def test_initial_lines(panel):
    assert len(panel) == panel.height
    for ln in panel:
        assert ln.length == panel.width
        assert ln.data == ""


def test_left_less_than_0(expect_error):
    with expect_error(ValueError, "left", "negative", "-1"):
        Panel(-1, 0, 1, 1)


def test_top_less_than_0(expect_error):
    with expect_error(ValueError, "top", "negative", "-1"):
        Panel(0, -1, 1, 1)


def test_modify_left_less_than_0(expect_error):
    with expect_error(ValueError, "left", "negative", "-1"):
        p = Panel(0, 0, 1, 1)
        p.left = -1


def test_modify_top_less_than_0(expect_error):
    with expect_error(ValueError, "top", "negative", "-1"):
        p = Panel(0, 0, 1, 1)
        p.top = -1


@params("width", 0, -1)
def test_panel_width_less_than_1(width, expect_error):
    p = Panel(1, 1, 1, 1)
    with expect_error(ValueError, "greater than 0", "width", str(width)):
        p.width = width


@params("height", 0, -1)
def test_panel_height_less_than_1(height, expect_error):
    p = Panel(1, 1, 1, 1)
    with expect_error(ValueError, "greater than 0", "height", str(height)):
        p.height = height


def test_special_width_height_initial_values_negative_1_means_dont_initialize_yet(
    expect_error,
):
    p = Panel(0, 0, -1, -1)

    # the panel is currently invalid so if we initialize it by updaing it's rect
    # we must set width in height or be met with an error
    with expect_error(ValueError, "width", "height", "greater than 0"):
        p.left = 0

    # if we set the entire rect using valid width and height everything should be ok
    p.rect = (0, 0, 1, 1)


@params(
    "start_width,end_width",
    (3, 6),
    (6, 3),
    (3, 3),
)
def test_good_width_reconfiguration(start_width, end_width):
    panel = Panel(0, 0, start_width, 2)
    initial_lines = panel[:]
    panel.width = end_width

    for ln0, ln1 in zip(initial_lines, panel):
        # lines remain as the same objects with updated length values
        assert ln0 is ln1
        assert ln1.length == end_width


@params("new_width", 0, -1)
def test_bad_width_reconfiguration(new_width, panel, expect_error):
    with expect_error(ValueError, "greater than 0", "width", str(new_width)):
        panel.width = new_width


@params(
    "start_height,end_height",
    (3, 6),
    (6, 3),
    (3, 3),
)
def test_good_height_reconfiguration(start_height, end_height):
    panel = Panel(0, 0, 1, start_height)
    initial_lines = panel[:]

    panel.height = end_height

    assert len(panel) == end_height
    for ln in panel:
        assert ln.length == panel.width
    for ln0, ln1 in zip(initial_lines, panel):
        assert ln0 is ln1


@params("new_height", 0, -1)
def test_bad_height_reconfiguration(new_height, panel, expect_error):
    with expect_error(ValueError, "greater than 0", "height", str(new_height)):
        panel.height = new_height


def test_writeln():
    panel = Panel(0, 0, 10, 2)

    panel.writeln(0, "testing1")
    panel.writeln(1, "testing2")

    assert panel[0].data == "testing1"
    assert panel[1].data == "testing2"


def test_readln():
    panel = Panel(0, 0, 10, 2)

    panel[0].data = "testing1"
    panel[1].data = "testing2"

    assert panel.readln(0) == "testing1"
    assert panel.readln(1) == "testing2"


def test_styleln():
    panel = Panel(0, 0, 10, 2)
    style1 = structs.Style(fill="1")
    style2 = structs.Style(fill="2")

    panel.styleln(0, style1)
    panel.styleln(1, style2)

    assert panel[0].style == style1
    assert panel[1].style == style2


def test_available():
    panel = Panel(0, 0, 10, 3)
    assert panel.available == 3

    panel.writeln(1, "abc")

    assert panel.available == 2


def test_availability_determined_by_empty_string():
    panel = Panel(0, 0, 10, 3)
    assert panel.available == 3

    panel.writeln(0, "abc")
    assert panel.available == 2

    panel.writeln(1, "")
    assert panel.available == 2


def test_first_available_returns_index():
    panel = Panel(0, 0, 10, 3)
    assert panel.first_available == 0

    panel.writeln(0, "abc")
    panel.writeln(1, "abc")
    assert panel.first_available == 2


def test_first_available_returns_none():
    panel = Panel(0, 0, 10, 2)
    assert panel.first_available == 0

    panel.writeln(0, "abc")
    panel.writeln(1, "abc")

    assert panel.first_available is None


def test_available_again_after_clear():
    panel = Panel(0, 0, 10, 3)

    panel.writeln(0, "abc")
    assert panel.first_available == 1

    panel.writeln(0, "")
    assert panel.first_available == 0


def test_clearln():
    panel = Panel(0, 0, 10, 3)

    panel.writeln(0, "abc")
    assert panel.readln(0) == "abc"

    panel.clearln(0)
    assert panel.readln(0) == ""


def test_first_available_after_clear():
    panel = Panel(0, 0, 10, 5)

    for i in range(5):
        panel.writeln(i, "abc")

    panel.clearln(4)
    panel.clearln(1)
    panel.clearln(3)

    assert panel.first_available == 1
    panel.writeln(1, "a")
    assert panel.first_available == 3
    panel.writeln(3, "a")
    assert panel.first_available == 4


def test_write_if_available_when_available():
    panel = Panel(0, 0, 10, 2)

    panel.write_if_available("abc")
    panel.write_if_available("bcd")

    assert panel.readln(0) == "abc"
    assert panel.readln(1) == "bcd"


def test_write_if_available_when_not_available():
    panel = Panel(0, 0, 10, 2)

    panel.write_if_available("abc")
    panel.write_if_available("bcd")
    # does nothing
    panel.write_if_available("cde")

    assert panel.readln(0) == "abc"
    assert panel.readln(1) == "bcd"


def test_default_default_style():
    style = structs.Style(fill="!")
    panel = Panel(0, 0, 10, 2, default_style=style)

    assert panel[0].style == style
    assert panel[1].style == style


def test_updating_default_style_updates_existing_lines():
    style1 = structs.Style(fill="!")
    style2 = structs.Style(fill="@")
    panel = Panel(0, 0, 10, 2, default_style=style1)

    panel.set_default_style(style2)

    assert panel[0].style == style2
    assert panel[1].style == style2


def test_cursor():
    panel = Panel(0, 0, 10, 2)

    panel.cursor.insert("abc")
    panel.cursor.line = 1
    panel.cursor.insert("def")

    assert panel.readln(0) == "abc"
    assert panel.readln(1) == "def"


def test_cursor_raises_overscroll_errors_by_default():
    panel = Panel(0, 0, 10, 2)

    with pytest.raises(cursor.Overscroll) as excinfo:
        panel.cursor.down(4)

    assert excinfo.value.amount == 3


def test_cursor_raises_overscroll_errors_by_default_across_size_change():
    panel = Panel(0, 0, 10, 2)
    panel.rect = (0, 0, 10, 3)

    with pytest.raises(cursor.Overscroll) as excinfo:
        panel.cursor.down(4)

    assert excinfo.value.amount == 2


def test_shift_up():
    panel = Panel(0, 0, 10, 3)
    panel.writeln(0, "0")
    panel.writeln(1, "1")
    panel.writeln(2, "2")

    panel.shift_up()

    assert panel.readln(0) == "1"
    assert panel.readln(1) == "2"
    assert panel.readln(2) == ""


def test_shift_up_multiple():
    panel = Panel(0, 0, 10, 3)
    panel.writeln(0, "0")
    panel.writeln(1, "1")
    panel.writeln(2, "2")

    panel.shift_up(2)

    assert panel.readln(0) == "2"
    assert panel.readln(1) == ""
    assert panel.readln(2) == ""


def test_shift_up_overflow():
    panel = Panel(0, 0, 10, 3)
    panel.writeln(0, "0")
    panel.writeln(1, "1")
    panel.writeln(2, "2")

    panel.shift_up(1000)

    assert panel.readln(0) == ""
    assert panel.readln(1) == ""
    assert panel.readln(2) == ""


def test_shift_down():
    panel = Panel(0, 0, 10, 3)
    panel.writeln(0, "0")
    panel.writeln(1, "1")
    panel.writeln(2, "2")

    panel.shift_down()

    assert panel.readln(0) == ""
    assert panel.readln(1) == "0"
    assert panel.readln(2) == "1"


def test_shift_down_multiple():
    panel = Panel(0, 0, 10, 3)
    panel.writeln(0, "0")
    panel.writeln(1, "1")
    panel.writeln(2, "2")

    panel.shift_down(2)

    assert panel.readln(0) == ""
    assert panel.readln(1) == ""
    assert panel.readln(2) == "0"


def test_shift_down_overflow():
    panel = Panel(0, 0, 10, 3)
    panel.writeln(0, "0")
    panel.writeln(1, "1")
    panel.writeln(2, "2")

    panel.shift_down(1000)

    assert panel.readln(0) == ""
    assert panel.readln(1) == ""
    assert panel.readln(2) == ""


@params(
    "index,value,expected",
    (0, "abc", ["abc", "0", "1"]),
    (1, "abc", ["0", "abc", "1"]),
    (3, "abc", ["0", "1", "2"]),
    (-1, "abc", ["0", "1", "abc"]),
)
def test_insert_line(index, value, expected):
    panel = Panel(0, 0, 5, 3)
    for i in range(3):
        panel.writeln(i, str(i))

    panel.insertln(index, value)

    for i, ln in enumerate(panel):
        assert ln.data == expected[i]


@params(
    "index,expected",
    (0, ["1", "2", ""]),
    (1, ["0", "2", ""]),
    (-1, ["0", "1", ""]),
)
def test_delete_line(index, expected):
    panel = Panel(0, 0, 5, 3)
    for i in range(3):
        panel.writeln(i, str(i))

    panel.deleteln(index)

    for i, ln in enumerate(panel):
        assert ln.data == expected[i]


def test_color_line():
    panel = Panel(0, 0, 5, 1)
    panel.colorln(0, AttributeBit.RED)

    assert panel[0].attributes & AttributeBit.RED


def test_color_line_keeps_other_attributes_intact():
    panel = Panel(0, 0, 5, 1, attributes=AttributeBit.BOLD)
    panel.colorln(0, AttributeBit.RED)

    assert panel[0].attributes & AttributeBit.RED
    assert panel[0].attributes & AttributeBit.BOLD


def test_color_line_removes_existing_color_bit():
    panel = Panel(0, 0, 5, 1)
    panel.colorln(0, AttributeBit.RED)
    panel.colorln(0, AttributeBit.GREEN)

    assert not panel[0].attributes & AttributeBit.RED
    assert panel[0].attributes & AttributeBit.GREEN


def test_color_line_not_a_color(expect_error):
    panel = Panel(0, 0, 5, 1)

    with expect_error(ValueError, "AttributeBit"):
        panel.colorln(0, 999)
