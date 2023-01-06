import contextlib

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


class Line:
    dirty: bool = True

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
        self._display = _pad_string(self._data, self._style, self._length)
        self.dirty = True


class Panel:
    dirty: bool = True
    available: int = -1
    _rect: structs.Rect = structs.Rect(-1, -1, -1, -1)
    _lines: Tuple[Line, ...] = ()
    _style: Union[structs.Style, Dict[Any, Any]]
    _styled: List[bool]

    def __init__(
        self,
        left: int,
        top: int,
        width: int,
        height: int,
        default_style: Optional[structs.Style] = None,
        **kwargs
    ) -> None:
        self._styled = []
        self._style = default_style if default_style is not None else kwargs
        self.rect = structs.Rect(left, top, width, height)

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

    def set_default_style(self, style: Optional[structs.Style] = None, **kwargs) -> None:
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

    @rect.setter
    def rect(self, rect: Union[structs.Rect, Tuple[int, int, int, int]]) -> None:
        if isinstance(rect, tuple):
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
            self._styled.extend([False] * (rect.height-len(self._styled)))
        else:
            self._styled = self._styled[:rect.height]

        self.available = sum(1 if ln.data == "" else 0 for ln in self)
        self.dirty = True

    @property
    def left(self) -> int:
        return self._rect.left

    @left.setter
    def left(self, value: int) -> None:
        self.rect = structs.Rect(value, self.top, self.width, self.height)

    @property
    def top(self) -> int:
        return self._rect.top

    @top.setter
    def top(self, value: int) -> None:
        self.rect = structs.Rect(self.left, value, self.width, self.height)

    @property
    def width(self) -> int:
        return self._rect.width

    @width.setter
    def width(self, value: int) -> None:
        self.rect = structs.Rect(self.left, self.top, value, self.height)

    @property
    def height(self) -> int:
        return self._rect.height

    @height.setter
    def height(self, value: int) -> None:
        self.rect = structs.Rect(self.left, self.top, self.width, value)


def _pad_string(string: str, style: structs.Style, max_length: int) -> str:
    """Assumes validation is handled by the caller"""

    final_display_length = max_length - sum(map(len, style.padding.pads))
    remaining = final_display_length - len(string)
    if remaining == 0:
        return style.padding.pads[0] + string + style.padding.pads[1]

    left_pad, right_pad = style.padding.pads
    display = string[:final_display_length]

    if remaining == 0:
        return left_pad + display + right_pad

    if style.padding.values[0] >= 0:
        if style.padding.values[1] < 0:
            # right pad variable/left pad constant -- extend right with padding fill
            right_pad = remaining * style.padding.fills[1] + right_pad
        else:
            # both pads constant, extend display with default fill
            display += remaining * style.fill

    elif style.padding.values[1] >= 0:
        # left pad is variable/right pad is constant -- extend left with padding fill
        left_pad += remaining * style.padding.fills[0]

    else:
        # both pads are variable, treat values like weights and fill with padding fill
        total = sum(style.padding.values)
        left_extra = int(round(style.padding.values[0] / total * remaining))
        right_extra = int(round(style.padding.values[1] / total * remaining))

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
        left_pad += style.padding.fills[0] * left_extra
        right_pad += style.padding.fills[1] * right_extra

    return left_pad + display + right_pad
