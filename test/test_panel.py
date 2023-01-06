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
