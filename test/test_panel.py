from .conftest import params

import pytest

from tuindow import Panel
from tuindow import structs


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
    with expect_error(ValueError, "greater than 0", "width", str(width)):
        Panel(1, 1, width, 1)


@params("height", 0, -1)
def test_panel_height_less_than_1(height, expect_error):
    with expect_error(ValueError, "greater than 0", "height", str(height)):
        Panel(1, 1, 1, height)


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


def test_writeline():
    panel = Panel(0, 0, 10, 2)

    panel.writeline(0, "testing1")
    panel.writeline(1, "testing2")

    assert panel[0].data == "testing1"
    assert panel[1].data == "testing2"


def test_readline():
    panel = Panel(0, 0, 10, 2)

    panel[0].data = "testing1"
    panel[1].data = "testing2"

    assert panel.readline(0) == "testing1"
    assert panel.readline(1) == "testing2"


def test_styleline():
    panel = Panel(0, 0, 10, 2)
    style1 = structs.Style(fill="1")
    style2 = structs.Style(fill="2")

    panel.styleline(0, style1)
    panel.styleline(1, style2)

    assert panel[0].style == style1
    assert panel[1].style == style2


def test_available():
    panel = Panel(0, 0, 10, 3)
    assert panel.available == 3

    panel.writeline(1, "abc")

    assert panel.available == 2


def test_availability_determined_by_empty_string():
    panel = Panel(0, 0, 10, 3)
    assert panel.available == 3

    panel.writeline(0, "abc")
    assert panel.available == 2

    panel.writeline(1, "")
    assert panel.available == 2


def test_first_available_returns_index():
    panel = Panel(0, 0, 10, 3)
    assert panel.first_available == 0

    panel.writeline(0, "abc")
    panel.writeline(1, "abc")
    assert panel.first_available == 2


def test_first_available_returns_none():
    panel = Panel(0, 0, 10, 2)
    assert panel.first_available == 0

    panel.writeline(0, "abc")
    panel.writeline(1, "abc")

    assert panel.first_available is None


def test_available_again_after_clear():
    panel = Panel(0, 0, 10, 3)

    panel.writeline(0, "abc")
    assert panel.first_available == 1

    panel.writeline(0, "")
    assert panel.first_available == 0


def test_clearline():
    panel = Panel(0, 0, 10, 3)

    panel.writeline(0, "abc")
    assert panel.readline(0) == "abc"

    panel.clearline(0)
    assert panel.readline(0) == ""


def test_first_available_after_clear():
    panel = Panel(0, 0, 10, 5)

    for i in range(5):
        panel.writeline(i, "abc")

    panel.clearline(4)
    panel.clearline(1)
    panel.clearline(3)

    assert panel.first_available == 1
    panel.writeline(1, "a")
    assert panel.first_available == 3
    panel.writeline(3, "a")
    assert panel.first_available == 4


def test_write_if_available_when_available():
    panel = Panel(0, 0, 10, 2)

    panel.write_if_available("abc")
    panel.write_if_available("bcd")

    assert panel.readline(0) == "abc"
    assert panel.readline(1) == "bcd"


def test_write_if_available_when_not_available():
    panel = Panel(0, 0, 10, 2)

    panel.write_if_available("abc")
    panel.write_if_available("bcd")
    # does nothing
    panel.write_if_available("cde")

    assert panel.readline(0) == "abc"
    assert panel.readline(1) == "bcd"


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


def test_updating_default_style_doesnt_update_existing_lines():
    style1 = structs.Style(fill="!")
    style2 = structs.Style(fill="@")
    style3 = structs.Style(fill="#")
    panel = Panel(0, 0, 10, 2, default_style=style1)

    panel.styleline(0, style3)
    panel.set_default_style(style2)

    assert panel[0].style == style3
    assert panel[1].style == style2
