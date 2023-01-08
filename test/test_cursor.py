from tuindow.cursor import Cursor as LibCursor


def Cursor(initial_value, index=0):
    value = initial_value

    def read():
        return value

    def write(new_value):
        nonlocal value
        value = new_value

    return LibCursor(index, 0, read=read, write=write)


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
