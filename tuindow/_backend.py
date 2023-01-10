from typing import Deque
from typing import Callable
from typing import Generator
from typing import Optional
from typing import Dict
from typing import Tuple

import os
import enum
import curses
import string
import collections

from curses import ascii


_TUINDOW_ATTRIBUTE_BITS_START = 1 << 64
_CURSES_ATTRIBUTE_MASK = _TUINDOW_ATTRIBUTE_BITS_START - 1


class Attribute:
    BLINK = curses.A_BLINK
    BOLD = curses.A_BOLD
    DIM = curses.A_DIM
    REVERSE = curses.A_REVERSE
    STANDOUT = curses.A_STANDOUT
    UNDERLINE = curses.A_UNDERLINE

    # initialization not available until curses is initialized
    # so I'm storing color attributes in higher order bits to
    # be converted to curses color pairs at draw time
    RED = _TUINDOW_ATTRIBUTE_BITS_START
    GREEN = _TUINDOW_ATTRIBUTE_BITS_START << 1
    YELLOW = _TUINDOW_ATTRIBUTE_BITS_START << 2
    BLUE = _TUINDOW_ATTRIBUTE_BITS_START << 3
    MAGENTA = _TUINDOW_ATTRIBUTE_BITS_START << 4
    CYAN = _TUINDOW_ATTRIBUTE_BITS_START << 5


class SpecialKeys(enum.Enum):
    BACKSPACE = "BACKSPACE"
    ESCAPE = "ESCAPE"
    F0 = "F0"
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F5 = "F5"
    F6 = "F6"
    F7 = "F7"
    F8 = "F8"
    F9 = "F9"
    F10 = "F10"
    F11 = "F11"
    F12 = "F12"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UP = "UP"
    DELETE = "DELETE"

    def __eq__(self, other: object) -> bool:
        return str(other) == self.value


_curses_key_map: Dict[int, str] = {
    curses.KEY_BACKSPACE: SpecialKeys.BACKSPACE.value,
    curses.KEY_F0: SpecialKeys.F0.value,
    curses.KEY_F1: SpecialKeys.F1.value,
    curses.KEY_F2: SpecialKeys.F2.value,
    curses.KEY_F3: SpecialKeys.F3.value,
    curses.KEY_F4: SpecialKeys.F4.value,
    curses.KEY_F5: SpecialKeys.F5.value,
    curses.KEY_F6: SpecialKeys.F6.value,
    curses.KEY_F7: SpecialKeys.F7.value,
    curses.KEY_F8: SpecialKeys.F8.value,
    curses.KEY_F9: SpecialKeys.F9.value,
    curses.KEY_F10: SpecialKeys.F10.value,
    curses.KEY_F11: SpecialKeys.F11.value,
    curses.KEY_F12: SpecialKeys.F12.value,
    curses.KEY_DOWN: SpecialKeys.DOWN.value,
    curses.KEY_LEFT: SpecialKeys.LEFT.value,
    curses.KEY_RIGHT: SpecialKeys.RIGHT.value,
    curses.KEY_UP: SpecialKeys.UP.value,
    curses.KEY_DC: SpecialKeys.DELETE.value,
    ascii.ESC: SpecialKeys.ESCAPE.value,
    **{ord(c): c for c in string.printable},
}


class CursesError(Exception):
    pass


class _ColorPairIndices(enum.Enum):
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6


class Instance:
    _stdscr: curses.window
    _resize_callback: Callable[[int, int], None]
    _cached_keys: Optional[Deque[str]]
    _cursor_enabled: bool = False

    def __init__(self, resize_callback: Callable[[int, int], None]):
        self._resize_callback = resize_callback
        self._cached_keys = collections.deque()

    def __repr__(self) -> str:
        return f"<Curses instance  size={self.size!r}>"

    def __enter__(self) -> "Instance":
        os.environ.setdefault("ESCDELAY", "100")
        self._stdscr = curses.initscr()
        self._stdscr.keypad(True)
        self._stdscr.nodelay(True)

        curses.start_color()

        curses.init_pair(_ColorPairIndices.RED.value,
                         curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(_ColorPairIndices.GREEN.value,
                         curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(_ColorPairIndices.YELLOW.value,
                         curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(_ColorPairIndices.BLUE.value,
                         curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(_ColorPairIndices.MAGENTA.value,
                         curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(_ColorPairIndices.CYAN.value,
                         curses.COLOR_CYAN, curses.COLOR_BLACK)

        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self._cursor_enabled = False
        self._stdscr.clear()
        self._stdscr.refresh()
        return self

    def __exit__(self, *_) -> None:
        self._stdscr.keypad(False)
        self._stdscr.nodelay(False)
        curses.echo()
        curses.nocbreak()
        curses.curs_set(1)
        curses.endwin()

    @property
    def keys(self) -> Generator[str, None, None]:
        while self._cached_keys:
            yield self._cached_keys.popleft()
        while (keycode := self._stdscr.getch()) != -1:
            if keycode == curses.KEY_RESIZE:
                self._resize_callback(*self.size)
            else:
                yield _curses_key_map.get(keycode, chr(keycode))

    @property
    def size(self) -> Tuple[int, int]:
        height, width = self._stdscr.getmaxyx()
        return width, height

    def cache_pending_keys(self) -> None:
        cache = self._cached_keys or collections.deque()
        self._cached_keys = None
        cache.extend((k for k in self.keys))
        self._cached_keys = cache

    def write_text(self, x: int, y: int, value: str, attributes: int) -> None:
        try:
            cleaned_attributes = attributes & _CURSES_ATTRIBUTE_MASK
            if attributes & Attribute.RED:
                cleaned_attributes |= curses.color_pair(
                    _ColorPairIndices.RED.value)
            elif attributes & Attribute.GREEN:
                cleaned_attributes |= curses.color_pair(
                    _ColorPairIndices.GREEN.value)
            elif attributes & Attribute.YELLOW:
                cleaned_attributes |= curses.color_pair(
                    _ColorPairIndices.YELLOW.value)
            elif attributes & Attribute.BLUE:
                cleaned_attributes |= curses.color_pair(
                    _ColorPairIndices.BLUE.value)
            elif attributes & Attribute.MAGENTA:
                cleaned_attributes |= curses.color_pair(
                    _ColorPairIndices.MAGENTA.value)
            elif attributes & Attribute.CYAN:
                cleaned_attributes |= curses.color_pair(
                    _ColorPairIndices.CYAN.value)
            self._stdscr.addstr(y, x, value, cleaned_attributes)
        except curses.error as exc:
            # writing the last character in the window causes an error
            # because it places the cursor out of bounds and we are
            # going to simply ignore this for now.

            # TODO: revist once cursor has been implemented

            width, height = self.size
            if x + len(value) == width and y == height - 1:
                return
            else:
                raise CursesError(
                    "Curses write to screen failed:\n"
                    f"    {self!r}\n"
                    f"    write_location={x=!r}, {y=!r}\n"
                    f"    {value=!r}\n"
                    f"    {attributes=!r}\n"
                    f"    internal error: {str(exc)}"
                )

    def update_display(self) -> None:
        self._stdscr.refresh()

    def draw_cursor(self, x: int, y: int) -> None:
        if not self._cursor_enabled:
            curses.curs_set(1)
            self._cursor_enabled = True
        self._stdscr.move(y, x)

    def disable_cursor(self) -> None:
        curses.curs_set(0)
        self._cursor_enabled = False
