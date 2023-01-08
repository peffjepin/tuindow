from tuindow.cursor import Cursor as LibCursor


def Cursor(initial_value, index=0):
    value = initial_value

    def read(x, y):
        return value

    def write(new_value):
        nonlocal value
        value = new_value

    return LibCursor(index, 0, read=read, write=write)


def test_read_write_functions():
    value = "abc"
    read_x = -1
    read_y = -1

    def read(x: int, y: int) -> str:
        nonlocal read_x
        nonlocal read_y
        read_x = x
        read_y = y
        return value

    def write() -> str:
        return value

    cursor = LibCursor(x=1, y=2, read=read, write=write)

    assert cursor.data == "abc"
    assert read_x == 1
    assert read_y == 2


def test_data():
    cursor = Cursor("abc")
    assert cursor.data == "abc"
    assert cursor.index == 0


def test_insert_into_empty_data():
    cursor = Cursor("")

    cursor.insert("a")

    assert cursor.data == "a"
    assert cursor.index == 1


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
