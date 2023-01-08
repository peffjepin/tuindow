from typing import Callable


class Cursor:
    def __init__(self, x: int, y: int, read: Callable[[], str], write: Callable[[str], None]):
        self._x = x
        self._y = y
        self._read = read
        self._write = write

    @property
    def index(self) -> int:
        return self._x

    @property
    def data(self) -> str:
        return self._read()

    def insert(self, value: str) -> None:
        current = self._read()
        self._write(current[:self._x] + value + current[self._x:])
        self._x += len(value)

    def backspace(self, n: int = 1) -> None:
        if self._x == 0:
            return
        if self._x <= n:
            self._write(self._read()[self._x:])
            self._x = 0
            return

        current = self._read()
        self._write(current[:self._x-n] + current[self._x:])
        self._x -= n

    def delete(self, n: int = 1) -> None:
        current = self._read()
        if self._x >= len(current) - 1:
            return
        if n >= len(current) - self._x:
            self._write(current[:self._x])
            return
        self._write(current[:self._x] + current[self._x+n:])
