"""
A helper object for navigating the lines of the user interface
"""

from typing import Callable
from typing import Tuple

from . import validation


class Overscroll(Exception):
    """
    Raised when a Cursor object tries to scroll outside it's allowed
    line range.
    """

    def __init__(self, amount: int):
        self.amount = amount
        super().__init__(amount)


class Cursor:
    def __init__(
        self,
        index: int,
        line: int,
        maxline: int,
        readline: Callable[[int], str],
        writeline: Callable[[int, str], None],
    ):
        self._index = index
        self._line = line
        self._readline = lambda: readline(self.line)
        self._writeline = lambda v: writeline(self.line, v)
        self._maxline = maxline

    def __repr__(self) -> str:
        return f"<Cursor line={self.line} index={self.index}>"

    @property
    def maxline(self) -> int:
        """
        Gets the maximum line index this cursor is allowed to visit.
        """

        return self._maxline

    @maxline.setter
    def maxline(self, value: int) -> None:
        """
        Sets maximum line index this cursor is allowed to visit and clamps
        the cursor's line index to be within the new range.
        """

        validation.not_negative("Cursor.maxline", value)
        self._maxline = value
        self.line = min(self.line, self._maxline)

    @property
    def index(self) -> int:
        """
        Gets the cursor's index into the current line.
        """

        return self._index

    @index.setter
    def index(self, value: int) -> None:
        """
        Sets the cursor's index into the current line.

        Negative values wrap from the end like any sequence.

        This function never errors, instead it clamps the given
        value to this cursor's acceptable range of values.
        """

        if value == 0:
            self._index = 0
            return

        length = len(self._readline())
        if value < 0:
            self._index = max(0, length + 1 + value)
        else:
            self._index = min(value, len(self._readline()))

    @property
    def line(self) -> int:
        """
        Gets the cursor's current line index.
        """

        return self._line

    @line.setter
    def line(self, value: int) -> None:
        """
        Sets the cursor's current line index.

        Negative values wrap from the end like any sequence.

        This function never errors, instead it clamps the given
        value to this cursor's acceptable range of values.
        """

        current = self._line

        if value < 0:
            value = max(0, self._maxline + 1 + value)
        else:
            value = min(value, self._maxline)

        self._line = value
        if value != current:
            self.index = self.index

    @property
    def position(self) -> Tuple[int, int]:
        """
        Gets (self.index, self.line).
        """

        return self._index, self._line

    @position.setter
    def position(self, value: Tuple[int, int]) -> None:
        """
        Given `value` as (index, line), equivalent to:
            self.line = line
            self.index = index
        """

        self.line = value[1]
        self.index = value[0]

    @property
    def data(self) -> str:
        """
        Reads the entire line currently under the cursor.
        """

        return self._readline()

    def insert(self, value: str) -> None:
        """
        Inserts the given string at the cursor's position and increments
        the cursor's `index` attribute accordingly.
        """

        current = self._readline()
        self._writeline(
            current[: self._index] + value + current[self._index :]
        )
        self._index += len(value)

    def backspace(self, n: int = 1) -> str:
        """
        Deletes `n` characters behind the cursor and decrements the index accordingly.

        This does not wrap lines, and does not error if self.index == 0.

        Returns the data that was removed or ""
        """

        if self._index == 0:
            return ""

        current = self._readline()

        if self._index <= n or n < 0:
            self._writeline(current[self._index :])
            removed = current[: self._index]
            self._index = 0
        else:
            self._writeline(
                current[: self._index - n] + current[self._index :]
            )
            removed = current[self._index - n : self._index]
            self._index -= n
        return removed

    def delete(self, n: int = 1) -> str:
        """
        Deletes `n` characters starting under the cursor and moving forward.

        This does not wrap lines, and does not error if
        deleting beyond the end of a line.

        Returns the data that was removed or ""
        """

        current = self._readline()

        if self._index >= len(current):
            return ""

        if n >= len(current) - self._index or n < 0:
            self._writeline(current[: self._index])
            return current[self._index :]

        self._writeline(current[: self._index] + current[self._index + n :])
        return current[self._index : self._index + n]

    def left(self, n: int = 1) -> None:
        """
        Moves the index left `n` spaces. Does not wrap and clamps index to valid values.
        """

        validation.not_negative("Cursor.left n", n)
        self._index = max(0, self._index - n)

    def right(self, n: int = 1) -> None:
        """
        Moves the index right `n` spaces. Does not wrap and clamps index to valid values.
        """

        validation.not_negative("Cursor.right n", n)
        current = self._readline()
        self._index = min(len(current), self._index + n)

    def up(self, n: int = 1) -> None:
        """
        Moves the line index up `n` spaces.

        raises Overscroll:
            when trying to go past cursor boundaries
            NOTE: check Overscroll.amount for the extent of the overscroll
        """

        validation.not_negative("Cursor.up n", n)
        new_line_index = self.line - n
        if new_line_index < 0:
            over = 0 - new_line_index
            self.line = 0
            raise Overscroll(over)
        else:
            self.line = new_line_index

    def down(self, n: int = 1) -> None:
        """
        Moves the line index down `n` spaces.

        raises Overscroll:
            when trying to go past cursor boundaries
            NOTE: check Overscroll.amount for the extent of the overscroll
        """

        validation.not_negative("Cursor.down n", n)

        if self.maxline is None:
            self.line += n
            return

        new_line_index = self.line + n
        over = new_line_index - self.maxline
        if over > 0:
            self.line = self.maxline
            raise Overscroll(over)
        else:
            self.line = new_line_index

    def consume_line(self) -> str:
        """
        Returns the current line data.

        In the process:
            sets index to 0
            sets line data to ""
        """

        self.index = 0
        return self.delete(-1)

    def pan(self, display_length: int) -> str:
        """
        Returns a slice of the data such that if there is insufficient space
        to display the entire string the cursor should be positioned at the very
        end of the display.
        """

        data = self._readline()
        # if there is enough space to display the data no panning is necessary
        if len(data) < display_length:
            return data
        # otherwise we aim to have the cursor positioned
        # at the end of the displayable length
        start = max(0, self.index - (display_length - 1))
        return data[start : start + display_length]
