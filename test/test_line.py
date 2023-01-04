from .conftest import params

from tuindow import Line


@params(
    "line, expected",
    (Line(10), ""),
    (Line(10, data="abc"), "abc"),
    (Line(2, data="abc"), "ab"),
)
def test_display(line, expected):
    assert line.display == expected


@params("length", 0, -1)
def test_length_less_than_1(expect_error, length):
    with expect_error(ValueError, "length", "greater than 0"):
        Line(length)


@params("length", 0, -1)
def test_modifying_length_less_than_1(expect_error, length):
    ln = Line(1)
    with expect_error(ValueError, "length", "greater than 0"):
        ln.length = length


def test_dirty_on_init():
    assert Line(1).dirty


def test_dirty_on_length_change():
    ln = Line(1)
    ln.dirty = False

    ln.length = 2
    assert ln.dirty


def test_dirty_on_data_change():
    ln = Line(1)
    ln.dirty = False

    ln.data = "abc"
    assert ln.dirty
