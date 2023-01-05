from typing import List
from typing import Iterator
from typing import Tuple
from typing import Optional
from typing import Union
from typing import Any


class _Validation:
    @classmethod
    def _error(
        cls, value_description: str, value: Any, error_reason: str
    ) -> None:
        raise ValueError(f"{value_description} ({value=!r}) {error_reason}")

    @classmethod
    def not_negative(cls, desc: str, value: Union[int, float]) -> None:
        if value < 0:
            cls._error(desc, value, "cannot be negative")

    @classmethod
    def greater_than_x(
        cls, desc: str, value: Union[int, float], x: Union[int, float]
    ) -> None:
        if not value > x:
            cls._error(desc, value, f"must be greater than {x!r}")

    @classmethod
    def padding_overflow(cls, value: Tuple[int, int], length: int) -> None:
        if sum(v for v in value if v > 0) >= length:
            cls._error("padding", value, f"cannot consume entire {length=}")

    @classmethod
    def padding_fill(cls, value: Tuple[str, str]) -> None:
        if any(len(v) != 1 for v in value):
            cls._error(
                "padding_fill values", value, "must be strings of length 1"
            )

    @classmethod
    def length_one_string(cls, desc: str, value: str) -> None:
        if len(value) != 1:
            cls._error(desc, value, "must be a string of length 1")


class _Padding:
    _pads: Tuple[str, str] = ("", "")
    _value: Tuple[int, int] = (0, 0)
    _fill: Tuple[str, str] = (" ", " ")

    def __init__(
        self,
        value: Tuple[int, int],
        fill: Tuple[str, str],
        max_length: int,
    ) -> None:
        self.set_value(value, max_length)
        self.fill = fill

    def validate_max_length(self, max_length: int) -> None:
        _Validation.padding_overflow(self.value, max_length)

    def pad_string(
        self, string: str, max_length: int, regular_fill: str
    ) -> str:
        final_display_length = max_length - self._required_length

        left_pad, right_pad = self._pads
        left_val, right_val = self.value

        display = string[:final_display_length]
        remaining = final_display_length - len(string)

        if remaining == 0:
            return left_pad + display + right_pad

        # there is extra space that needs filling
        # if there is variable length padding (values less than 0) fill appropriate space with padding fill
        # otherwise fill remainder with regular fill

        if left_val >= 0:
            if right_val < 0:
                # right pad variable/left pad constant -- extend right with padding fill
                f = self.fill[1]
            else:
                # both pads constant, extend right with default fill
                f = regular_fill
            right_pad = remaining * f + right_pad

        elif right_val >= 0:
            # left pad is variable/right pad is constant -- extend left with padding fill
            left_pad += remaining * self.fill[0]

        else:
            # both pads are variable, treat values like weights and fill with padding fill
            total = left_val + right_val
            left_extra = int(round(left_val / total * remaining))
            right_extra = int(round(right_val / total * remaining))

            # fix off by one errors from rounding, leaving higher weight with the extra padding
            off = remaining - (left_extra + right_extra)
            assert off in (-1, 0, 1)
            if off == 1:
                if left_extra >= right_extra:
                    left_extra += off
                else:
                    right_extra += off
            elif off == -1:
                if left_extra >= right_extra:
                    right_extra += off
                else:
                    left_extra += off
            left_pad += self.fill[0] * left_extra
            right_pad += self.fill[1] * right_extra

        return left_pad + display + right_pad

    @property
    def value(self) -> Tuple[int, int]:
        return self._value

    def set_value(self, value: Tuple[int, int], max_length: int) -> None:
        _Validation.padding_overflow(value, max_length)
        self._value = value
        self._pads = (
            self.value[0] * self.fill[0] if self.value[0] >= 0 else "",
            self.value[1] * self.fill[1] if self.value[1] >= 0 else "",
        )

    @property
    def fill(self) -> Tuple[str, str]:
        return self._fill

    @fill.setter
    def fill(self, value: Tuple[str, str]) -> None:
        _Validation.padding_fill(value)
        self._fill = value
        self._pads = (
            self.value[0] * self.fill[0] if self.value[0] >= 0 else "",
            self.value[1] * self.fill[1] if self.value[1] >= 0 else "",
        )

    @property
    def _required_length(self) -> int:
        return sum(map(len, self._pads))


class Line:
    dirty: bool

    _data: str
    _length: int
    _fill: str
    _padding: _Padding

    def __init__(
        self,
        length: int,
        data="",
        fill=" ",
        padding: Union[int, Tuple[int, int]] = (0, 0),
        padding_fill: Optional[Union[str, Tuple[str, str]]] = None,
    ) -> None:

        # self.value property catches this, but requires self.padding
        # to be initialized. Without this check here, the error message
        # for initializing with an invalid length would indicate a padding
        # overflow which would be a slightly inaccurate error message
        _Validation.greater_than_x("Line length", length, 0)

        self.fill = fill

        if padding_fill is None:
            padding_fill = (fill, fill)
        elif isinstance(padding_fill, str):
            padding_fill = (padding_fill, padding_fill)
        if isinstance(padding, int):
            padding = (padding, padding)
        self._padding = _Padding(padding, padding_fill, length)

        self.length = length
        self.data = data
        self.dirty = True
        self.padding = padding

    @property
    def padding_fill(self) -> Tuple[str, str]:
        return self._padding.fill

    @padding_fill.setter
    def padding_fill(
        self, value: Optional[Union[str, Tuple[str, str]]]
    ) -> None:
        if value is None:
            self._padding.fill = (self.fill, self.fill)
        elif isinstance(value, str):
            self._padding.fill = (value, value)
        else:
            self._padding.fill = value
        self.dirty = True

    @property
    def padding(self) -> Tuple[int, int]:
        return self._padding.value

    @padding.setter
    def padding(self, value: Tuple[int, int]) -> None:
        self._padding.set_value(value, self.length)
        self.dirty = True

    @property
    def fill(self) -> str:
        return self._fill

    @fill.setter
    def fill(self, value: str) -> None:
        _Validation.length_one_string("Line fill", value)
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
        _Validation.greater_than_x("Line length", value, 0)
        self._padding.validate_max_length(value)
        self._length = value
        self.dirty = True

    @property
    def display(self) -> str:
        return self._padding.pad_string(str(self.data), self.length, self.fill)


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
        return iter(self.lines[: self.height])

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        _Validation.not_negative("Panel x", value)
        self._x = value

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        _Validation.not_negative("Panel y", value)
        self._y = value

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        _Validation.greater_than_x("Panel width", value, 0)
        if value != self._width and self.lines:
            for line in self.lines:
                line.length = value
        self._width = value

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        _Validation.greater_than_x("Panel height", value, 0)
        if value > self._height:
            while value > len(self.lines):
                self.lines.append(Line(self.width))
        self._height = value
