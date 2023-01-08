from tuindow.cursor import Cursor as LibCursor


def Cursor(initial_value, index=0, line=0):
    value = initial_value

    def read(line):
        return value

    def write(line, new_value):
        nonlocal value
        value = new_value

    return LibCursor(index, line, readline=read, writeline=write)


def MultilineCursor(lines, index, line):
    def readline(line):
        return lines[line]

    def writeline(line, value):
        lines[line] = value

    return LibCursor(index, line, readline=readline, writeline=writeline)


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

    cursor = LibCursor(index=1, line=2, readline=read, writeline=write)

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

    cursor.backspace()

    assert cursor.data == "abc"
    assert cursor.index == 3


def test_backspace_from_beginning():
    cursor = Cursor("abcd", index=0)

    cursor.backspace()

    assert cursor.data == "abcd"
    assert cursor.index == 0


def test_backspace_from_the_middle():
    cursor = Cursor("abcd", index=2)

    cursor.backspace()

    assert cursor.data == "acd"
    assert cursor.index == 1


def test_backspace_multiple():
    cursor = Cursor("abcd", index=2)

    cursor.backspace(2)

    assert cursor.data == "cd"
    assert cursor.index == 0


def test_backspace_multiple_overflows():
    cursor = Cursor("abcd", index=2)

    cursor.backspace(3)

    assert cursor.data == "cd"
    assert cursor.index == 0


def test_backspace_empty():
    cursor = Cursor("")

    cursor.backspace()

    assert cursor.data == ""
    assert cursor.index == 0


def test_delete_empty():
    cursor = Cursor("")

    cursor.delete()

    assert cursor.data == ""
    assert cursor.index == 0


def test_delete_beginning():
    cursor = Cursor("abc")

    cursor.delete()

    assert cursor.data == "bc"
    assert cursor.index == 0


def test_delete_middle():
    cursor = Cursor("abc", index=1)

    cursor.delete()

    assert cursor.data == "ac"
    assert cursor.index == 1


def test_delete_end():
    cursor = Cursor("abc", index=3)

    cursor.delete()

    assert cursor.data == "abc"
    assert cursor.index == 3


def test_delete_many():
    cursor = Cursor("abc", index=0)

    cursor.delete(2)

    assert cursor.data == "c"
    assert cursor.index == 0


def test_delete_many_overflow():
    cursor = Cursor("abc", index=1)

    cursor.delete(100)

    assert cursor.data == "a"
    assert cursor.index == 1


def test_consume():
    cursor = Cursor("abc")

    assert cursor.consume() == "abc"
    assert cursor.data == ""


def test_non_zero_index():
    cursor = Cursor("abc", index=3)

    assert cursor.consume() == "abc"
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


def test_set_index_negative_error(expect_error):
    cursor = Cursor("abc", index=0)

    with expect_error(IndexError):
        cursor.index = -5


def test_set_index_positive():
    cursor = Cursor("abc", index=0)

    cursor.index = 3

    assert cursor.index == 3


def test_set_index_positive_error(expect_error):
    cursor = Cursor("abc", index=0)

    with expect_error(IndexError):
        cursor.index = 4


def test_cursor_line_modification():
    cursor = Cursor("abc")

    assert cursor.line == 0

    cursor.line = 2
    assert cursor.line == 2

    # no upper bound on cursor line
    cursor.line = 1000
    assert cursor.line == 1000


def test_cursor_resets_index_when_line_changes():
    cursor = Cursor("abc", index=3)

    assert cursor.line == 0
    assert cursor.index == 3

    cursor.line = 1
    assert cursor.line == 1
    assert cursor.index == 0


def test_cursor_line_negative(expect_error):
    cursor = Cursor("abc")

    with expect_error(ValueError, "cannot be negative"):
        cursor.line = -1


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


def test_multiline_position_line_error(expect_error):
    cursor = MultilineCursor(["", ""], 0, 0)

    with expect_error(ValueError, "Cursor", "line"):
        cursor.position = (0, -1)


def test_multiline_position_index_error(expect_error):
    cursor = MultilineCursor(["", ""], 0, 0)

    with expect_error(IndexError, "Cursor", "index"):
        cursor.position = (1, 0)
