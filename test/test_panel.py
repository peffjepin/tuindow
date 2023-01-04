from .conftest import params

import pytest

from tuindow import Panel
from tuindow import Line


@pytest.fixture
def panel():
    return Panel(1, 2, 3, 4)


def test_initial_lines(panel):
    assert len(panel.lines) == panel.height
    for ln in panel.lines:
        assert ln.length == panel.width
        assert ln.data == ""


def test_iteration_without_modifications(panel):
    for i, ln in enumerate(panel):
        assert panel.lines[i] is ln


def test_iteration_with_modifications(panel):
    newline = Line(panel.width)
    panel.lines[1] = newline
    panel.lines.append(Line(panel.width))

    assert len(list(panel)) == panel.height

    for i, ln in enumerate(panel):
        assert ln is panel.lines[i]
        if i == 1:
            assert ln is newline


def test_x_less_than_0(expect_error):
    with expect_error(ValueError, "x", "negative", "-1"):
        Panel(-1, 0, 1, 1)


def test_y_less_than_0(expect_error):
    with expect_error(ValueError, "y", "negative", "-1"):
        Panel(0, -1, 1, 1)


def test_modify_x_less_than_0(expect_error):
    with expect_error(ValueError, "x", "negative", "-1"):
        p = Panel(0, 0, 1, 1)
        p.x = -1


def test_modify_y_less_than_0(expect_error):
    with expect_error(ValueError, "y", "negative", "-1"):
        p = Panel(0, 0, 1, 1)
        p.y = -1


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
    lines = panel.lines.copy()
    panel.width = end_width

    for ln0, ln1 in zip(lines, panel.lines):
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
    nlines = len(panel.lines)

    panel.height = end_height

    if start_height >= end_height:
        # no changes to line count
        assert len(panel.lines) == nlines
    else:
        # extra lines added
        assert len(panel.lines) == end_height
        for ln in panel.lines:
            assert ln.length == panel.width


@params("new_height", 0, -1)
def test_bad_height_reconfiguration(new_height, panel, expect_error):
    with expect_error(ValueError, "greater than 0", "height", str(new_height)):
        panel.height = new_height
