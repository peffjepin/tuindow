from .conftest import params

from tuindow import Line


@params(
    "line,expected",
    (Line(3, data="abc"), "abc"),
    (Line(2, data="abc"), "ab"),
    (Line(2), "  "),
    (Line(3, data="ab"), "ab "),
    (Line(3, data="ab", fill="."), "ab."),
    (Line(5, data="abcde", padding=(1, 0)), " abcd"),
    (Line(5, data="abcde", padding=(0, 1)), "abcd "),
    (Line(5, data="abcde", padding=(2, 1)), "  ab "),
    (Line(5, data="ab", padding=(1, 1)), " ab  "),
    (Line(5, data="abc", padding=(1, 1), padding_fill="."), ".abc."),
    (Line(5, data="ab", padding=(1, 1), padding_fill="!", fill="?"), "!ab?!"),
    (Line(5, data="ab", padding=(1, 1), padding_fill=("!", ".")), "!ab ."),
    (Line(5, data="abc", padding=1), " abc "),
    (Line(5, data="a", padding=(-1, 1)), "   a "),
    (Line(5, data="a", padding=-1), "  a  "),
    (Line(5, data="a", padding=(-1, -3)), " a   "),
    (Line(5, data="ab", padding=(-1, -1)), "  ab "),
    (Line(5, data="a", padding=-1, padding_fill="!", fill="."), "!!a!!"),
)
def test_display(line, expected):
    assert line.display == expected


@params(
    "attr,value",
    ("fill", "!"),
    ("data", "abc"),
    ("length", 2),
    ("padding", (1, 2)),
    ("padding_fill", "."),
)
def test_dirty_on_state_change(attr, value):
    ln = Line(10)
    ln.dirty = False

    setattr(ln, attr, value)
    assert ln.dirty


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
    assert Line(10, fill="!").display == "!"*10


def test_default_fill_is_space():
    assert Line(10).display == " "*10


@params("fill", "", "--")
def test_fill_must_be_length_1(expect_error, fill):
    with expect_error(ValueError, "fill", "length 1", fill):
        Line(10, fill=fill)


@params("fill", "", "--", ("", " "), (" ", ""))
def test_padding_fill_must_be_length_1(expect_error, fill):
    with expect_error(ValueError, "fill", "length 1", repr(fill)):
        Line(10, padding_fill=fill)


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
    with expect_error(ValueError, "padding", "length", repr(length), repr(padding)):
        Line(length, padding=padding)


def test_pads_updated_when_padding_fill_updated():
    ln = Line(4, padding=(1, 2))
    assert ln.display == "    "

    ln.padding_fill = "."
    assert ln.display == ". .."


def test_scalar_padding_on_init():
    assert Line(4, padding=1, data="ab").display == " ab "


def test_scalar_padding_modification():
    line = Line(4, data="ab")
    assert line.display == "ab  "

    line.padding = 1
    assert line.display == " ab "


def test_insufficient_padding_space_error_when_line_length_changed(expect_error):
    ln = Line(4, padding=(1, 2))

    with expect_error(ValueError, "padding", "length", repr(2), repr((1, 2))):
        ln.length = 2


def test_data_is_anything_that_implements_str():
    class Data:
        def __str__(self):
            return "txt"
    assert Line(3, data=Data()).display == "txt"


@params(
    "data1,data2",
    (1, 2),
    ("", " "),
    (True, False),
    (1.0, 2.0),
)
def test_line_data_primitives(data1, data2):
    ln = Line(10, data=data1)
    assert ln.dirty
    assert str(data1) in ln.display
    ln.dirty = False

    ln.data = data2
    assert ln.dirty
    assert str(data2) in ln.display


def test_line_data_protocol():
    class MyData:
        dirty = False

        def __str__(self):
            return "hello"

    data = MyData()
    assert not data.dirty

    # The window has yet to draw this line, and so it should still
    # be flagged dirty despite the implementation dirty flag currently being False
    ln = Line(10, data=data)
    assert ln.dirty
    ln.dirty = False
    assert not ln.dirty
    assert "hello" in ln.display

    # without touching the line we should be able to enable the dirty flag
    # with our data implementation
    data.dirty = True
    assert ln.dirty
    assert "hello" in ln.display
