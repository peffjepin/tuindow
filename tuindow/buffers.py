from typing import Iterator
from typing import Tuple
from typing import Optional
from typing import Union
from typing import List
from typing import overload

from . import structs
from . import validation
from . import cursor


class Line:
    dirty: bool = True
    style_locked: bool = False

    _display: str = ""
    _data: str = ""
    _style: structs.Style = structs.Style()
    _length: int

    def __init__(
        self,
        length: int,
        style: Optional[structs.Style] = None,
        data: str = "",
        **kwargs,
    ) -> None:
        self.length = length
        self.data = data
        if style is not None:
            self.style = style
        else:
            self.style = structs.Style.from_keywords(**kwargs)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(length={self.length!r}, data={self.data!r}, "
            f"fill={self.fill!r}, padding={self.padding!r}, padding_fills={self.padding_fills!r})"
        )

    @property
    def style(self) -> structs.Style:
        return self._style

    @style.setter
    def style(self, style: structs.Style) -> None:
        if self.style_locked:
            return

        with validation.pool(ValueError):
            validation.length_one_string("fill style", style.fill)
            validation.padding_overflow(style.padding, self.length)
            validation.padding_fills(style.padding)

        self._style = style
        self._update_display()

    @property
    def padding_fills(self) -> Tuple[str, str]:
        return self._style.padding.fills

    @padding_fills.setter
    def padding_fills(
        self, value: Optional[Union[str, Tuple[str, str]]]
    ) -> None:
        self.style = structs.Style.from_keywords(
            fill=self.fill,
            padding=self.padding,
            padding_fills=value,
        )

    @property
    def padding(self) -> Tuple[int, int]:
        return self._style.padding.values

    @padding.setter
    def padding(self, value: Union[int, Tuple[int, int]]) -> None:
        self.style = structs.Style.from_keywords(
            fill=self.fill, padding=value, padding_fills=self.padding_fills
        )

    @property
    def fill(self) -> str:
        return self._style.fill

    @fill.setter
    def fill(self, value: str) -> None:
        self.style = structs.Style.from_keywords(
            fill=value, padding=self.padding, padding_fills=self.padding_fills
        )

    @property
    def data(self) -> str:
        return self._data

    @data.setter
    def data(self, value: str) -> None:
        self._data = value
        self._update_display()

    @property
    def length(self) -> int:
        return self._length

    @length.setter
    def length(self, value: int) -> None:
        with validation.pool(ValueError):
            validation.greater_than_x("Line length", value, 0)
            validation.padding_overflow(self.style.padding, value)
        self._length = value
        self._update_display()

    @property
    def display(self) -> str:
        return self._display

    def _update_display(self) -> None:
        lpad, rpad = self.style.calculate_pads(self._data, self._length)
        display_length = self.length - len(lpad) - len(rpad)
        remaining = display_length - len(self.data)
        if remaining <= 0:
            display_data = self._data[:display_length]
        else:
            display_data = self._data + self.style.fill * remaining
        self._display = lpad + display_data + rpad
        self.dirty = True


class Panel:
    available: int = -1
    cursor: cursor.Cursor
    _lines: List[Line]
    _style: structs.Style
    _rect: structs.Rect = structs.Rect(-1, -1, -1, -1)

    def __init__(
        self,
        left: int = 0,
        top: int = 0,
        width: int = -1,
        height: int = -1,
        default_style: Optional[structs.Style] = None,
        **kwargs,
    ) -> None:
        self._lines = []
        self._style = (
            default_style
            if default_style is not None
            else structs.Style.from_keywords(**kwargs)
        )

        self.cursor = cursor.Cursor(
            index=0,
            line=0,
            maxline=0,
            readline=self.readln,
            writeline=self.writeln,
        )

        if width == -1 or height == -1:
            # user may want to create panels before initializing the screen
            # and only layout the panels later from a resize callback
            return

        self.rect = (left, top, width, height)

    def __repr__(self) -> str:
        rect = self._rect
        return f"{self.__class__.__name__}({rect=})"

    def __iter__(self) -> Iterator[Line]:
        return iter(self._lines)

    @overload
    def __getitem__(self, index: int) -> Line:
        ...

    @overload
    def __getitem__(self, index: slice) -> List[Line]:
        ...

    def __getitem__(self, index: Union[int, slice]) -> Union[Line, List[Line]]:
        return self._lines[index]

    def __len__(self) -> int:
        return self.height

    def writeln(self, index: int, value: str) -> None:
        ln = self[index]
        if ln.data and not value:
            self.available += 1
        elif not ln.data and value:
            self.available -= 1
        ln.data = value

    def readln(self, index: int) -> str:
        return self[index].data

    def clearln(self, index: int) -> None:
        self.writeln(index, "")

    def insertln(self, index: int, value: str) -> None:
        self._lines.insert(index, self._default_line(value))
        del self._lines[-1]
        for ln in self[index:]:
            ln.dirty = True

    def deleteln(self, index: int) -> None:
        del self._lines[index]
        self._lines.append(self._default_line())
        for ln in self[index:]:
            ln.dirty = True

    def styleln(self, index: int, style=None, **kwargs) -> None:
        ln = self[index]
        ln.style_locked = False
        if style is None:
            ln.style = structs.Style.from_keywords(**kwargs)
        else:
            ln.style = style
        ln.style_locked = True

    def shift_up(self, n: int = 1) -> None:
        validation.greater_than_x("Panel.shift_up param n", n, 0)
        self._shift_data(-n)

    def shift_down(self, n: int = 1) -> None:
        validation.greater_than_x("Panel.shift_down param n", n, 0)
        self._shift_data(n)

    def _shift_data(self, n: int) -> None:
        if abs(n) >= self.height:
            self._lines = [self._default_line() for _ in range(self.height)]

        fresh_lines = [self._default_line() for _ in range(abs(n))]

        if n < 0:
            existing_slice = self._lines[abs(n) : len(self._lines)]
            for ln in existing_slice:
                ln.dirty = True
            self._lines = existing_slice + fresh_lines
        elif n > 0:
            existing_slice = self._lines[0 : self.height - n]
            for ln in existing_slice:
                ln.dirty = True
            self._lines = fresh_lines + existing_slice

    @property
    def first_available(self) -> Optional[int]:
        for i, ln in enumerate(self):
            if not ln.data:
                return i
        return None

    def write_if_available(self, value: str) -> None:
        if not self.available:
            return
        index = self.first_available
        assert index is not None
        self.writeln(index, value)

    def set_default_style(
        self, style: Optional[structs.Style] = None, **kwargs
    ) -> None:
        if style is not None:
            self._style = style
        else:
            self._style = structs.Style.from_keywords(**kwargs)

        for ln in self:
            ln.style = self._style

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.width, self.height)

    @rect.setter
    def rect(self, value: Tuple[int, int, int, int]) -> None:
        rect = structs.Rect(*value)

        with validation.pool(ValueError):
            validation.not_negative("Panel.left", rect.left)
            validation.not_negative("Panel.top", rect.top)
            validation.greater_than_x("Panel.width", rect.width, 0)
            validation.greater_than_x("Panel.height", rect.height, 0)

        self._rect = rect

        if len(self._lines) < rect.height:
            grow_amount = rect.height - len(self._lines)
            self._lines.extend(
                self._default_line() for _ in range(grow_amount)
            )
        else:
            self._lines = self._lines[: rect.height]

        for ln in self._lines:
            if ln.length != rect.width:
                ln.length = rect.width

        self.cursor.maxline = rect.height - 1
        self.available = sum(1 if ln.data == "" else 0 for ln in self)

    @property
    def display_rect(self) -> structs.Rect:
        """
        Returns the internal rect object for drawing, as opposed to the
        tuple interface meant for the user.
        """
        return self._rect

    def _default_line(self, data="") -> Line:
        return Line(self.width, style=self._style, data=data)

    @property
    def left(self) -> int:
        return self._rect.left

    @left.setter
    def left(self, value: int) -> None:
        self.rect = (value, self.top, self.width, self.height)

    @property
    def top(self) -> int:
        return self._rect.top

    @top.setter
    def top(self, value: int) -> None:
        self.rect = (self.left, value, self.width, self.height)

    @property
    def width(self) -> int:
        return self._rect.width

    @width.setter
    def width(self, value: int) -> None:
        self.rect = (self.left, self.top, value, self.height)

    @property
    def height(self) -> int:
        return self._rect.height

    @height.setter
    def height(self, value: int) -> None:
        self.rect = (self.left, self.top, self.width, value)
