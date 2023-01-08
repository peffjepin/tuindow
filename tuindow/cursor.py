from typing import Callable
from typing import Tuple


class Cursor:
    def __init__(self, x: int, y: int, read: Callable[[int, int], str], write: Callable[[str], None]):
        self._x = x
        self._y = y
        self._read = read
        self._write = write

    @property
    def index(self) -> int:
        return self._x

    @index.setter
    def index(self, value: int) -> None:
        if value == 0:
            self._x = 0
            return

        length = len(self._read(*self.position))
        if value < 0:
            proposed = length + 1 + value
            if proposed < 0:
                raise IndexError
            self._x = proposed
        else:
            if value > length:
                raise IndexError
            self._x = value

    @property
    def position(self) -> Tuple[int, int]:
        return self._x, self._y

    @property
    def data(self) -> str:
        return self._read(*self.position)

    def insert(self, value: str) -> None:
        current = self._read(*self.position)
        self._write(current[:self._x] + value + current[self._x:])
        self._x += len(value)

    def backspace(self, n: int = 1) -> None:
        if self._x == 0:
            return
        if self._x <= n:
            self._write(self._read(*self.position)[self._x:])
            self._x = 0
            return

        current = self._read(*self.position)
        self._write(current[:self._x-n] + current[self._x:])
        self._x -= n

    def delete(self, n: int = 1) -> None:
        current = self._read(*self.position)
        if self._x >= len(current) - 1:
            return
        if n >= len(current) - self._x:
            self._write(current[:self._x])
            return
        self._write(current[:self._x] + current[self._x+n:])

    def consume(self) -> str:
        current = self._read(*self.position)
        self._write("")
        self._x = 0
        return current

    def left(self, n: int = 1) -> None:
        self._x = max(0, self._x - n)

    def right(self, n: int = 1) -> None:
        current = self._read(*self.position)
        self._x = min(len(current), self._x + n)
