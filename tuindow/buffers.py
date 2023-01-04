from typing import List
from typing import Iterator


class Line:
    dirty: bool

    _data: str
    _length: int

    def __init__(self, length: int, data="") -> None:
        if length < 1:
            raise ValueError(f"Line {length=} must be greater than 0")
        self.length = length
        self.data = data
        self.dirty = True

    @property
    def data(self) -> str:
        return self._data

    @data.setter
    def data(self, value: str) -> None:
        self._data = value
        self.dirty = True

    @property
    def length(self) -> int:
        return self._length

    @length.setter
    def length(self, value: int) -> None:
        if value < 1:
            raise ValueError(f"Line length {value=} must be greater than 0")
        self._length = value
        self.dirty = True

    @property
    def display(self) -> str:
        return self.data[: self.length]


class Panel:
    lines: List[Line]

    _x: int = -1
    _y: int = -1
    _width: int = -1
    _height: int = -1

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.lines = []
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.lines = [Line(width) for _ in range(height)]

    def __repr__(self) -> str:
        x = self.x
        y = self.y
        width = self.width
        height = self.height
        return f"{self.__class__.__name__}({x=}, {y=}, {width=}, {height=})"

    def __iter__(self) -> Iterator[Line]:
        return iter(self.lines[:self.height])

    @ property
    def x(self) -> int:
        return self._x

    @ x.setter
    def x(self, value: int) -> None:
        if value < 0:
            raise ValueError(f"Panel x {value=} cannot be negative")
        self._x = value

    @ property
    def y(self) -> int:
        return self._y

    @ y.setter
    def y(self, value: int) -> None:
        if value < 0:
            raise ValueError(f"Panel y {value=} cannot be negative")
        self._y = value

    @ property
    def width(self) -> int:
        return self._width

    @ width.setter
    def width(self, value: int) -> None:
        if value < 1:
            raise ValueError(f"Panel width {value=} must be greater than 0")
        if value != self._width and self.lines:
            for line in self.lines:
                line.length = value
        self._width = value

    @ property
    def height(self) -> int:
        return self._height

    @ height.setter
    def height(self, value: int) -> None:
        if value < 1:
            raise ValueError(f"Panel height {value=} must be greater than 0")
        if value > self._height:
            while value > len(self.lines):
                self.lines.append(Line(self.width))
        self._height = value
