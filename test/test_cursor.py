import pytest

from .conftest import params

from tuindow.cursor import Cursor as LibCursor
from tuindow.cursor import Overscroll


def Cursor(initial_value="", index=0, line=0):
    value = initial_value

    def read(line):
        return value

    def write(line, new_value):
        nonlocal value
        value = new_value

    return LibCursor(index, line, maxline=0, readline=read, writeline=write)


def MultilineCursor(lines, index=0, line=0):
    def readline(line):
        return lines[line]

    def writeline(line, value):
        lines[line] = value

    return LibCursor(
        index,
        line,
        maxline=len(lines) - 1,
        readline=readline,
        writeline=writeline,
    )


def test_read_write_functions():
    value = "abc"
    line_read = -1
    line_written = -1

    def read(line) -> str:
        nonlocal line_read
        line_read = line
        return value

    def write(line, value) -> str:
        nonlocal line_written
        line_written = line
        return value

    cursor = LibCursor(
        index=1, line=2, maxline=2, readline=read, writeline=write
    )

    assert cursor.data == "abc"
    assert line_read == 2
    cursor.insert("123")
    assert line_written == 2


def test_data():
    cursor = Cursor("abc")
    assert cursor.data == "abc"
    assert cursor.index == 0


def test_insert_into_empty_data():
    cursor = Cursor("")

    cursor.insert("a")

    assert cursor.data == "a"
    assert cursor.index == 1


def test_inserting_empty_string():
    cursor = Cursor("")

    cursor.insert("")

    assert cursor.data == ""
    assert cursor.index == 0


def test_insert_before_data():
    cursor = Cursor("b")

    cursor.insert("a")

    assert cursor.data == "ab"
    assert cursor.index == 1


def test_insert_after_data():
    cursor = Cursor("b", index=1)

    cursor.insert("a")

    assert cursor.data == "ba"
    assert cursor.index == 2


def test_insert_between_data():
    cursor = Cursor("abc", index=1)

    cursor.insert("d")

    assert cursor.data == "adbc"
    assert cursor.index == 2


def test_insert_string():
    cursor = Cursor("b")

    cursor.insert("aaa")

    assert cursor.data == "aaab"
    assert cursor.index == 3


def test_backspace_from_end():
    cursor = Cursor("abcd", index=4)

    assert cursor.backspace() == "d"
    assert cursor.data == "abc"
    assert cursor.index == 3


def test_backspace_from_beginning():
    cursor = Cursor("abcd", index=0)

    assert cursor.backspace() == ""
    assert cursor.data == "abcd"
    assert cursor.index == 0


def test_backspace_from_the_middle():
    cursor = Cursor("abcd", index=2)

    assert cursor.backspace() == "b"
    assert cursor.data == "acd"
    assert cursor.index == 1


def test_backspace_multiple():
    cursor = Cursor("abcd", index=2)

    assert cursor.backspace(2) == "ab"
    assert cursor.data == "cd"
    assert cursor.index == 0


def test_backspace_multiple_overflows():
    cursor = Cursor("abcd", index=2)

    assert cursor.backspace(3) == "ab"
    assert cursor.data == "cd"
    assert cursor.index == 0


def test_backspace_negative():
    cursor = Cursor("abcd", index=4)

    assert cursor.backspace(-1) == "abcd"
    assert cursor.data == ""
    assert cursor.index == 0


def test_backspace_empty():
    cursor = Cursor("")

    assert cursor.backspace() == ""
    assert cursor.data == ""
    assert cursor.index == 0


def test_delete_empty():
    cursor = Cursor("")

    assert cursor.delete() == ""
    assert cursor.data == ""
    assert cursor.index == 0


def test_delete_beginning():
    cursor = Cursor("abc")

    assert cursor.delete() == "a"
    assert cursor.data == "bc"
    assert cursor.index == 0


def test_delete_middle():
    cursor = Cursor("abc", index=1)

    assert cursor.delete() == "b"
    assert cursor.data == "ac"
    assert cursor.index == 1


def test_delete_end():
    cursor = Cursor("abc", index=3)

    assert cursor.delete() == ""
    assert cursor.data == "abc"
    assert cursor.index == 3


def test_delete_many():
    cursor = Cursor("abc", index=0)

    assert cursor.delete(2) == "ab"
    assert cursor.data == "c"
    assert cursor.index == 0


def test_delete_many_overflow():
    cursor = Cursor("abc", index=1)

    assert cursor.delete(100) == "bc"
    assert cursor.data == "a"
    assert cursor.index == 1


def test_delete_negative():
    cursor = Cursor("abc", index=0)

    assert cursor.delete(-1) == "abc"
    assert cursor.data == ""
    assert cursor.index == 0


def test_consume_line():
    cursor = Cursor("abc")

    assert cursor.consume_line() == "abc"
    assert cursor.data == ""


def test_non_zero_index():
    cursor = Cursor("abc", index=3)

    assert cursor.consume_line() == "abc"
    assert cursor.data == ""
    assert cursor.index == 0


def test_left():
    cursor = Cursor("abc", index=3)

    cursor.left()

    assert cursor.index == 2


def test_left_n():
    cursor = Cursor("abc", index=3)

    cursor.left(2)

    assert cursor.index == 1


def test_left_at_index_zero():
    cursor = Cursor("abc", index=0)

    cursor.left()

    assert cursor.index == 0


def test_right():
    cursor = Cursor("abc", index=0)

    cursor.right()

    assert cursor.index == 1


def test_right_n():
    cursor = Cursor("abc", index=0)

    cursor.right(2)

    assert cursor.index == 2


def test_right_past_end():
    cursor = Cursor("abc", index=0)

    cursor.right(10)

    assert cursor.index == 3


def test_set_index_negative():
    cursor = Cursor("abc", index=0)

    cursor.index = -1
    assert cursor.index == 3

    cursor.index = -4
    assert cursor.index == 0


def test_set_index_negative_overflow():
    cursor = Cursor("abc", index=0)

    cursor.index = -5
    assert cursor.index == 0


def test_set_index_positive():
    cursor = Cursor("abc", index=0)

    cursor.index = 3

    assert cursor.index == 3


def test_set_index_positive_overflow():
    cursor = Cursor("abc", index=0)

    cursor.index = 4
    assert cursor.index == 3


@params(
    "new_line_value,expected_line_value",
    (0, 0),
    (1, 1),
    (2, 2),
    (-1, 4),
    (-100, 0),
    (100, 4),
)
def test_cursor_line_modification(new_line_value, expected_line_value):
    cursor = MultilineCursor(list(map(str, range(5))), index=0, line=0)
    assert cursor.line == 0

    cursor.line = new_line_value
    assert cursor.line == expected_line_value


def test_cursor_preserves_and_clamps_index_when_line_changes():
    lines = [
        "abcdef",
        "abcde",
        "abcd",
        "abcd",
        "abcde",
        "a",
        "",
    ]
    cursor = MultilineCursor(lines, index=6, line=0)
    cursor.down()
    assert cursor.index == 5
    cursor.down()
    assert cursor.index == 4
    cursor.down()
    assert cursor.index == 4
    cursor.down()
    assert cursor.index == 4
    cursor.down()
    assert cursor.index == 1
    cursor.down()
    assert cursor.index == 0
    cursor.up()
    assert cursor.index == 0
    cursor.up()
    assert cursor.index == 0


def test_writing_multiple_lines():
    lines = ["", ""]
    cursor = MultilineCursor(lines, 0, 0)

    cursor.insert("abc")
    cursor.line = 1
    cursor.insert("def")

    assert lines == ["abc", "def"]


def test_set_multiline_position_sets_line_then_index():
    cursor = MultilineCursor(["abc", "defghi"], 0, 0)

    cursor.position = (-1, 1)
    assert cursor.data == "defghi"
    assert cursor.index == 6
    assert cursor.line == 1


@params(
    "length,index,expected",
    (2, 0, "01"),
    (3, 0, "012"),
    (3, 1, "012"),
    (3, 2, "012"),
    (3, 3, "123"),
    (3, 4, "234"),
    (3, 5, "34"),
    (5, 5, "1234"),
)
def test_pan(length, index, expected):
    cursor = Cursor("01234", index=index)

    assert cursor.pan(length) == expected


def test_up():
    cursor = MultilineCursor(["" for _ in range(5)], line=3)

    cursor.up()

    assert cursor.line == 2


def test_up_many():
    cursor = MultilineCursor(["" for _ in range(5)], line=3)

    cursor.up(3)

    assert cursor.line == 0


def test_up_negative(expect_error):
    cursor = MultilineCursor(["" for _ in range(5)], line=3)

    with expect_error(ValueError):
        cursor.up(-2)


def test_up_overflow(expect_error):
    cursor = MultilineCursor(["" for _ in range(5)], line=3)

    with pytest.raises(Overscroll) as excinfo:
        cursor.up(7)

    assert excinfo.value.amount == 4
    assert cursor.line == 0


def test_down():
    cursor = MultilineCursor(["" for _ in range(5)], line=3)

    cursor.down()

    assert cursor.line == 4


def test_down_many():
    cursor = MultilineCursor(["" for _ in range(5)], line=1)

    cursor.down(3)

    assert cursor.line == 4


def test_down_negative():
    cursor = MultilineCursor(["" for _ in range(5)], line=3)

    with pytest.raises(ValueError):
        cursor.down(-3)


def test_down_overflow():
    cursor = MultilineCursor(["" for _ in range(5)], line=3)

    with pytest.raises(Overscroll) as excinfo:
        cursor.down(3)

    assert excinfo.value.amount == 2
    assert cursor.line == cursor.maxline


def test_setting_maxline_clamps_line():
    cursor = MultilineCursor(["" for _ in range(5)], line=3)
    cursor.maxline = 2
    assert cursor.line == 2
