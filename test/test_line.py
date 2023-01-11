from .conftest import params

from tuindow._backend import AttributeBit
from tuindow.buffers import Line
from tuindow.structs import Style


@params(
    "kwargs,expected",
    ({"length": 3, "data": "abc"}, "abc"),
    ({"length": 2, "data": "abc"}, "ab"),
    ({"length": 2}, "  "),
    ({"length": 3, "data": "ab"}, "ab "),
    ({"length": 3, "data": "ab", "fill": "."}, "ab."),
    ({"length": 5, "data": "abcde", "padding": (1, 0)}, " abcd"),
    ({"length": 5, "data": "abcde", "padding": (0, 1)}, "abcd "),
    ({"length": 5, "data": "abcde", "padding": (2, 1)}, "  ab "),
    ({"length": 5, "data": "ab", "padding": (1, 1)}, " ab  "),
    (
        {"length": 5, "data": "abc", "padding": (1, 1), "padding_fills": "."},
        ".abc.",
    ),
    (
        {
            "length": 5,
            "data": "ab",
            "padding": (1, 1),
            "padding_fills": "!",
            "fill": "?",
        },
        "!ab?!",
    ),
    (
        {
            "length": 5,
            "data": "ab",
            "padding": (1, 1),
            "padding_fills": ("!", "."),
        },
        "!ab .",
    ),
    ({"length": 5, "data": "abc", "padding": 1}, " abc "),
    ({"length": 5, "data": "a", "padding": (-1, 1)}, "   a "),
    ({"length": 5, "data": "a", "padding": -1}, "  a  "),
    ({"length": 5, "data": "a", "padding": (-1, -3)}, " a   "),
    ({"length": 5, "data": "ab", "padding": (-1, -1)}, "  ab "),
    (
        {
            "length": 5,
            "data": "a",
            "padding": -1,
            "padding_fills": "!",
            "fill": ".",
        },
        "!!a!!",
    ),
)
def test_display(kwargs, expected):
    line = Line(**kwargs)
    print(repr(line))
    assert line.display == expected


@params(
    "attr,value",
    ("fill", "!"),
    ("data", "abc"),
    ("length", 2),
    ("padding", (1, 2)),
    ("padding_fills", "."),
    ("attributes", AttributeBit.BOLD),
)
def test_dirty_on_state_change(attr, value):
    ln = Line(10)
    ln.dirty = False

    setattr(ln, attr, value)
    assert ln.dirty


@params(
    "attr,value",
    ("fill", "!"),
    ("data", "abc"),
    ("length", 2),
    ("padding", (1, 2)),
    ("padding_fills", "."),
    ("attributes", AttributeBit.BOLD),
)
def test_not_dirty_when_state_doesnt_actually_change(attr, value):
    ln = Line(10)
    setattr(ln, attr, value)
    ln.dirty = False

    setattr(ln, attr, value)
    assert not ln.dirty


@params("length", 0, -1)
def test_length_less_than_1(expect_error, length):
    with expect_error(ValueError, "length", "greater than 0"):
        Line(length)


@params("length", 0, -1)
def test_modifying_length_less_than_1(expect_error, length):
    ln = Line(1)
    with expect_error(ValueError, "length", "greater than 0"):
        ln.length = length


def test_fill():
    assert Line(10, fill="!").display == "!" * 10


def test_default_fill_is_space():
    assert Line(10).display == " " * 10


@params("fill", "", "--")
def test_fill_must_be_length_1(expect_error, fill):
    with expect_error(ValueError, "fill", "length 1", fill):
        Line(10, fill=fill)


@params("fill", "", "--", ("", " "), (" ", ""))
def test_padding_fill_must_be_length_1(expect_error, fill):
    with expect_error(ValueError, "fill", "length 1", repr(fill)):
        Line(10, padding_fills=fill)


def test_dirty_on_init():
    assert Line(1).dirty


@params(
    "padding,length",
    ((1, 1), 1),
    ((2, 0), 1),
    ((0, 2), 1),
    ((1, 1), 2),
)
def test_padding_exceeds_length(expect_error, padding, length):
    with expect_error(
        ValueError, "padding", "length", repr(length), repr(padding)
    ):
        Line(length, padding=padding)


def test_pads_updated_when_padding_fill_updated():
    ln = Line(4, padding=(1, 2))
    assert ln.display == "    "

    ln.padding_fills = "."
    assert ln.display == ". .."


def test_scalar_padding_on_init():
    assert Line(4, padding=1, data="ab").display == " ab "


def test_scalar_padding_modification():
    line = Line(4, data="ab")
    assert line.display == "ab  "

    line.padding = 1
    assert line.display == " ab "


def test_insufficient_padding_space_error_when_line_length_changed(
    expect_error,
):
    ln = Line(4, padding=(1, 2))

    with expect_error(ValueError, "padding", "length", repr(2), repr((1, 2))):
        ln.length = 2
