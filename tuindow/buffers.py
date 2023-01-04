from typing import List
from typing import Iterator
from typing import Tuple


class Line:
    dirty: bool

    _data: str
    _length: int
    _display_capacity: int
    _fill: str
    _padding: Tuple[int, int]
    _left_pad: str = ""
    _right_pad: str = ""

    def __init__(self, length: int, data="", fill=" ", padding=(0, 0)) -> None:
        self.fill = fill
        self.length = length
        self.data = data
        self.dirty = True
        self.padding = padding

    @property
    def padding(self) -> Tuple[int, int]:
        return self._padding

    @padding.setter
    def padding(self, value: Tuple[int, int]) -> None:
        if sum(x for x in value if x > 0) >= self.length:
            raise ValueError(
                f"Line padding ({value=!r}) exceeded length ({self.length!r})")

        self._display_capacity = self.length
        self._left_pad = ""
        self._right_pad = ""
        if value[0] >= 0:
            self._left_pad = self.fill*value[0]
            self._display_capacity -= value[0]
        if value[1] >= 0:
            self._right_pad = self.fill*value[1]
            self._display_capacity -= value[1]
        self._padding = value
        self.dirty = True

    @property
    def fill(self) -> str:
        return self._fill

    @fill.setter
    def fill(self, value: str) -> None:
        if len(value) != 1:
            raise ValueError(
                f"Line fill ({value=!r}) must be a string of length 1")
        self._fill = value
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
            raise ValueError(f"Line length ({value=}) must be greater than 0")
        self._length = value
        self.dirty = True

    @property
    def display(self) -> str:
        display = str(self.data)
        if len(display) < self._display_capacity:
            return (
                self._left_pad +
                display +
                self.fill*(self._display_capacity - len(display)) +
                self._right_pad
            )
        return self._left_pad + display[:self._display_capacity] + self._right_pad


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

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        if value < 0:
            raise ValueError(f"Panel x ({value=}) cannot be negative")
        self._x = value

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        if value < 0:
            raise ValueError(f"Panel y ({value=}) cannot be negative")
        self._y = value

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        if value < 1:
            raise ValueError(f"Panel width ({value=}) must be greater than 0")
        if value != self._width and self.lines:
            for line in self.lines:
                line.length = value
        self._width = value

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        if value < 1:
            raise ValueError(f"Panel height ({value=}) must be greater than 0")
        if value > self._height:
            while value > len(self.lines):
                self.lines.append(Line(self.width))
        self._height = value
