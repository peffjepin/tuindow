from typing import Callable
from typing import Tuple
from typing import Optional

from . import validation


class Cursor:
    active: Optional["Cursor"]

    def __init__(
        self,
        index: int,
        line: int,
        readline: Callable[[int], str],
        writeline: Callable[[int, str], None],
    ):
        self._index = index
        self._line = line
        self._readline = lambda: readline(self.line)
        self._writeline = lambda v: writeline(self.line, v)

    def __repr__(self) -> str:
        return f"<Cursor line={self.line} index={self.index}>"

    @classmethod
    def clear_active(cls):
        cls.active = None

    def set_active(self) -> None:
        Cursor.active = self

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, value: int) -> None:
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
        return self._line

    @line.setter
    def line(self, value: int) -> None:
        validation.not_negative("Cursor.line", value)
        if value != self._line:
            self.index = 0
        self._line = value

    @property
    def position(self) -> Tuple[int, int]:
        return self._index, self._line

    @position.setter
    def position(self, value: Tuple[int, int]) -> None:
        self.line = value[1]
        self.index = value[0]

    @property
    def data(self) -> str:
        return self._readline()

    def insert(self, value: str) -> None:
        current = self._readline()
        self._writeline(
            current[: self._index] + value + current[self._index:]
        )
        self._index += len(value)

    def backspace(self, n: int = 1) -> None:
        if self._index == 0:
            return
        if self._index <= n:
            self._writeline(self._readline()[self._index:])
            self._index = 0
            return

        current = self._readline()
        self._writeline(current[: self._index - n] + current[self._index:])
        self._index -= n

    def delete(self, n: int = 1) -> None:
        current = self._readline()
        if self._index >= len(current):
            return
        if n >= len(current) - self._index:
            self._writeline(current[: self._index])
            return
        self._writeline(current[: self._index] + current[self._index + n:])

    def consume(self) -> str:
        current = self._readline()
        self._writeline("")
        self._index = 0
        return current

    def pan(self, display_length: int) -> str:
        data = self._readline()
        # if there is enough space to display the data no panning is necessary
        if len(data) < display_length:
            return data
        # otherwise we aim to have the cursor positioned
        # at the end of the displayable length
        start = max(0, self.index - (display_length - 1))
        return data[start: start + display_length]

    def left(self, n: int = 1) -> None:
        self._index = max(0, self._index - n)

    def right(self, n: int = 1) -> None:
        current = self._readline()
        self._index = min(len(current), self._index + n)
