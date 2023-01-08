import contextlib
import sys

from typing import Iterator
from typing import Generator
from typing import Iterable
from typing import Tuple
from typing import Optional
from typing import Union
from typing import Dict
from typing import List
from typing import Any

from . import structs
from . import validation
from . import cursor


class Line:
    dirty: bool = True
    display_offset: int

    _display: str = ""
    _data: str = ""
    _style: structs.Style = structs.Style()
    _length: int

    def __init__(
        self,
        length: int,
        style: Optional[structs.Style] = None,
        data: str = "",
        fill: str = " ",
        padding: Union[int, Tuple[int, int]] = (0, 0),
        padding_fills: Optional[Union[str, Tuple[str, str]]] = None,
    ) -> None:
        with self._wait_update_display():
            self.data = data
            self.length = length
            if style is not None:
                self.style = style
            else:
                self.format(
                    fill=fill, padding=padding, padding_fills=padding_fills
                )

    @contextlib.contextmanager
    def _wait_update_display(self) -> Iterator[None]:
        """
        avoids recalculating display with each state change until context exits
        """

        implementation = self._update_display
        called = 0

        def patch() -> None:
            nonlocal called
            called += 1

        setattr(self, "_update_display", patch)
        yield
        setattr(self, "_update_display", implementation)

        if called:
            self._update_display()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(length={self.length!r}, data={self.data!r}, "
            f"fill={self.fill!r}, padding={self.padding!r}, padding_fills={self.padding_fills!r})"
        )

    def format(
        self,
        fill: str = " ",
        padding: Union[int, Tuple[int, int]] = (0, 0),
        padding_fills: Optional[Union[str, Tuple[str, str]]] = None,
    ) -> None:
        if padding_fills is None:
            padding_fills = fill
        self.style = structs.Style(
            fill=fill,
            padding=structs.Padding.calculate(
                fills=(
                    padding_fills
                    if isinstance(padding_fills, tuple)
                    else (padding_fills, padding_fills)
                ),
                values=(
                    padding
                    if isinstance(padding, tuple)
                    else (padding, padding)
                ),
            ),
        )
        self._update_display()

    @property
    def style(self) -> structs.Style:
        return self._style

    @style.setter
    def style(self, style: structs.Style) -> None:
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
        if value is None:
            value = (self.fill, self.fill)
        elif isinstance(value, str):
            value = (value, value)
        self.style = structs.Style(
            fill=self.fill,
            padding=structs.Padding.calculate(
                fills=value, values=self.padding
            ),
        )

    @property
    def padding(self) -> Tuple[int, int]:
        return self._style.padding.values

    @padding.setter
    def padding(self, value: Union[int, Tuple[int, int]]) -> None:
        if isinstance(value, int):
            value = (value, value)
        self.style = structs.Style(
            fill=self._style.fill,
            padding=structs.Padding.calculate(
                fills=self.padding_fills, values=value
            ),
        )

    @property
    def fill(self) -> str:
        return self._style.fill

    @fill.setter
    def fill(self, value: str) -> None:
        self.style = structs.Style(fill=value, padding=self.style.padding)

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
        self.display_offset = len(lpad)
        self._display = lpad + \
            self._data[:(self._length-len(lpad)-len(rpad))] + rpad
        self.dirty = True


class Panel:
    available: int = -1
    cursor: cursor.Cursor
    _rect: structs.Rect = structs.Rect(-1, -1, -1, -1)
    _lines: Tuple[Line, ...] = ()
    _style: Union[structs.Style, Dict[Any, Any]]
    _styled: List[bool]

    def __init__(
        self,
        left: int = 0,
        top: int = 0,
        width: int = sys.maxsize,
        height: int = sys.maxsize,
        default_style: Optional[structs.Style] = None,
        **kwargs,
    ) -> None:
        self._styled = []
        self._style = default_style if default_style is not None else kwargs

        def cursor_readline(ln: int) -> str:
            return self[ln].data

        def cursor_writeline(ln: int, value: str) -> None:
            self[ln].data = value

        self.cursor = cursor.Cursor(
            index=0, line=0, readline=cursor_readline, writeline=cursor_writeline)

        if width == sys.maxsize or height == sys.maxsize:
            return
        self.set_rect(rect=structs.Rect(left, top, width, height))

    def __repr__(self) -> str:
        rect = self._rect
        return f"{self.__class__.__name__}({rect=})"

    def __iter__(self) -> Iterator[Line]:
        return iter(self._lines)

    def __getitem__(self, index: int) -> Line:
        return self._lines[index]

    def __len__(self) -> int:
        return self.height

    def writeline(self, index: int, value: str) -> None:
        ln = self[index]
        if ln.data and not value:
            self.available += 1
        elif not ln.data and value:
            self.available -= 1
        ln.data = value

    def readline(self, index: int) -> str:
        return self[index].data

    def clearline(self, index: int) -> None:
        self.writeline(index, "")

    def styleline(self, index: int, style=None, **kwargs) -> None:
        if style is None:
            self[index].format(**kwargs)
        else:
            self[index].style = style
        self._styled[index] = True

    def write_if_available(self, value: str) -> None:
        if not self.available:
            return
        index = self.first_available
        assert index is not None
        self.writeline(index, value)

    def _linegen(
        self, current_lines: Optional[Iterable[Line]] = None
    ) -> Generator[Line, None, None]:
        if current_lines is not None:
            for ln in current_lines:
                ln.length = self.width
                yield ln
        if isinstance(self._style, structs.Style):
            while 1:
                yield Line(self.width, self._style)
        else:
            while 1:
                yield Line(self.width, **self._style)

    @property
    def first_available(self) -> Optional[int]:
        for i, ln in enumerate(self):
            if not ln.data:
                return i
        return None

    def set_default_style(
        self, style: Optional[structs.Style] = None, **kwargs
    ) -> None:
        if style is not None:
            self._style = style
            for styled, ln in zip(self._styled, self._lines):
                if styled:
                    continue
                ln.style = style
        else:
            self._style = kwargs
            for styled, ln in zip(self._styled, self._lines):
                if styled:
                    continue
                ln.format(**kwargs)

    @property
    def rect(self) -> structs.Rect:
        return self._rect

    def set_rect(
        self,
        left: int = -1,
        top: int = -1,
        width: int = 0,
        height: int = 0,
        rect: Optional[structs.Rect] = None,
    ) -> None:
        """I'd sure love to use a @rect.setter here but mypy hates Unions in setters."""

        if rect is None:
            rect = structs.Rect(left, top, width, height)
        else:
            # construct a new rect to ensure all panels have unique rects
            rect = structs.Rect(*rect)

        with validation.pool(ValueError):
            validation.not_negative("Panel.left", rect.left)
            validation.not_negative("Panel.top", rect.top)
            validation.greater_than_x("Panel.width", rect.width, 0)
            validation.greater_than_x("Panel.height", rect.height, 0)

        self._rect = rect
        lines = self._linegen(self._lines)
        self._lines = tuple(next(lines) for _ in range(rect.height))

        if len(self._styled) < rect.height:
            self._styled.extend([False] * (rect.height - len(self._styled)))
        else:
            self._styled = self._styled[: rect.height]

        self.available = sum(1 if ln.data == "" else 0 for ln in self)
        self.dirty = True

    @property
    def left(self) -> int:
        return self._rect.left

    @left.setter
    def left(self, value: int) -> None:
        self.set_rect(
            rect=structs.Rect(value, self.top, self.width, self.height)
        )

    @property
    def top(self) -> int:
        return self._rect.top

    @top.setter
    def top(self, value: int) -> None:
        self.set_rect(
            rect=structs.Rect(self.left, value, self.width, self.height)
        )

    @property
    def width(self) -> int:
        return self._rect.width

    @width.setter
    def width(self, value: int) -> None:
        self.set_rect(
            rect=structs.Rect(self.left, self.top, value, self.height)
        )

    @property
    def height(self) -> int:
        return self._rect.height

    @height.setter
    def height(self, value: int) -> None:
        self.set_rect(
            rect=structs.Rect(self.left, self.top, self.width, value)
        )
