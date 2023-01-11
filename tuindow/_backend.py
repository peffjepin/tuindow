"""
All curses related code
"""

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


# Store custom attributes for this library in higher order bits.
# These will be processed before issuing draw commands
#
# Using this method we can specify attributes like color before the
# display has been initialized and handle passing in the correct value
# at draw time.

_ATTRIBUTE_BITS_START = 1 << 64
_CURSES_ATTRIBUTE_BITMASK = _ATTRIBUTE_BITS_START - 1

_attribute_bits_current = 1 << 64


def _new_attribute_bit():
    global _attribute_bits_current

    new_bit = _attribute_bits_current
    _attribute_bits_current <<= 1
    return new_bit


class AttributeBit:
    BLINK = curses.A_BLINK
    BOLD = curses.A_BOLD
    DIM = curses.A_DIM
    REVERSE = curses.A_REVERSE
    STANDOUT = curses.A_STANDOUT
    UNDERLINE = curses.A_UNDERLINE

    RED = _new_attribute_bit()
    GREEN = _new_attribute_bit()
    YELLOW = _new_attribute_bit()
    BLUE = _new_attribute_bit()
    MAGENTA = _new_attribute_bit()
    CYAN = _new_attribute_bit()


_COLOR_ATTRIBUTES_BITMASK = (
    (AttributeBit.CYAN << 1) - 1
) ^ _CURSES_ATTRIBUTE_BITMASK

_COLOR_BITS = set(
    (
        AttributeBit.RED,
        AttributeBit.GREEN,
        AttributeBit.BLUE,
        AttributeBit.MAGENTA,
        AttributeBit.CYAN,
    )
)


def set_color_bit(attributes: int, color_bit: int) -> int:
    if color_bit not in _COLOR_BITS:
        raise ValueError(
            "`color_bit` must be a color from the AttributeBit namespace"
        )
    cleaned = attributes & ~_COLOR_ATTRIBUTES_BITMASK
    cleaned |= color_bit
    return cleaned


class SpecialKeys(enum.Enum):
    """
    Keys that aren't represented by their corresponding single character.

    TODO: This could be expanded, but suits my purposes currently
    """

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


class _ColorPairIndex(enum.Enum):
    """
    curses.color_pair( ... ) indices for color pairs
    that the library sets up by default.

    All of these pairs are against a black background.

    White on black is the default so it's not listed.
    """

    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6


class _CursorVisualState:
    def __init__(self):
        self._current_curses_value = -1
        self._curses_value = 0
        self._x = 0
        self._y = 0

    def enable(self) -> None:
        self._curses_value = 1

    def disable(self) -> None:
        self._curses_value = 0

    def move(self, x: int, y: int):
        self._x = x
        self._y = y

    def draw(self, stdscr: curses.window):
        if self._curses_value != self._current_curses_value:
            curses.curs_set(self._curses_value)
            self._current_curses_value = self._curses_value
        stdscr.move(self._y, self._x)


class Instance:
    """
    An object that encapsules curses funtionality.
    """

    _stdscr: curses.window
    _cursor_display: _CursorVisualState
    _resize_callback: Callable[[int, int], None]
    _cached_keys: Optional[Deque[str]]

    def __init__(self, resize_callback: Callable[[int, int], None]):
        self._cursor_display = _CursorVisualState()
        self._resize_callback = resize_callback
        self._cached_keys = collections.deque()

    def __repr__(self) -> str:
        return f"<Curses instance  size={self.size!r}>"

    def __enter__(self) -> "Instance":
        """
        Initializes curses and sets up some default color pairs.
        """

        os.environ.setdefault("ESCDELAY", "100")
        self._stdscr = curses.initscr()
        self._stdscr.keypad(True)
        self._stdscr.nodelay(True)

        curses.start_color()

        curses.init_pair(
            _ColorPairIndex.RED.value, curses.COLOR_RED, curses.COLOR_BLACK
        )
        curses.init_pair(
            _ColorPairIndex.GREEN.value, curses.COLOR_GREEN, curses.COLOR_BLACK
        )
        curses.init_pair(
            _ColorPairIndex.YELLOW.value,
            curses.COLOR_YELLOW,
            curses.COLOR_BLACK,
        )
        curses.init_pair(
            _ColorPairIndex.BLUE.value, curses.COLOR_BLUE, curses.COLOR_BLACK
        )
        curses.init_pair(
            _ColorPairIndex.MAGENTA.value,
            curses.COLOR_MAGENTA,
            curses.COLOR_BLACK,
        )
        curses.init_pair(
            _ColorPairIndex.CYAN.value, curses.COLOR_CYAN, curses.COLOR_BLACK
        )

        curses.noecho()
        curses.cbreak()
        self._cursor_display.disable()
        self._stdscr.clear()
        self.update_display()
        return self

    def __exit__(self, *_) -> None:
        """
        Tears down curses and restores terminal to usable state
        """

        self._stdscr.keypad(False)
        self._stdscr.nodelay(False)
        curses.echo()
        curses.nocbreak()
        curses.curs_set(1)
        curses.endwin()

    @property
    def keys(self) -> Generator[str, None, None]:
        """
        Polls for keys non-blocking and yields them when present.
        """

        while self._cached_keys:
            yield self._cached_keys.popleft()
        while (keycode := self._stdscr.getch()) != -1:
            if keycode == curses.KEY_RESIZE:
                self._resize_callback(*self.size)
            else:
                yield _curses_key_map.get(keycode, chr(keycode))

    @property
    def size(self) -> Tuple[int, int]:
        """
        Returns the size of the window measured in characters
        """

        height, width = self._stdscr.getmaxyx()
        return width, height

    def cache_pending_keys(self) -> None:
        """
        Caches all pending key presses until next self.keys access.

        NOTE: triggers resize callback if resize encountered in keys
        """

        cache = self._cached_keys or collections.deque()
        self._cached_keys = None
        cache.extend((k for k in self.keys))
        self._cached_keys = cache

    def update_display(self) -> None:
        self._cursor_display.draw(self._stdscr)
        self._stdscr.refresh()

    def draw_cursor(self, x: int, y: int) -> None:
        self._cursor_display.enable()
        self._cursor_display.move(x, y)

    def disable_cursor(self) -> None:
        self._cursor_display.disable()

    def write_text(self, x: int, y: int, value: str, attributes: int) -> None:
        """
        Writes the given string to the screen at (x, y) where (0, 0) is the top left.
        Not displayed until display is updated.

        Raises CursesError when write fails.
        """
        try:
            self._stdscr.addstr(
                y, x, value, self._process_attributes(attributes)
            )
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

    def _process_attributes(self, attributes: int) -> int:
        cleaned_attributes = attributes & _CURSES_ATTRIBUTE_BITMASK
        if attributes & AttributeBit.RED:
            cleaned_attributes |= curses.color_pair(_ColorPairIndex.RED.value)
        elif attributes & AttributeBit.GREEN:
            cleaned_attributes |= curses.color_pair(
                _ColorPairIndex.GREEN.value
            )
        elif attributes & AttributeBit.YELLOW:
            cleaned_attributes |= curses.color_pair(
                _ColorPairIndex.YELLOW.value
            )
        elif attributes & AttributeBit.BLUE:
            cleaned_attributes |= curses.color_pair(_ColorPairIndex.BLUE.value)
        elif attributes & AttributeBit.MAGENTA:
            cleaned_attributes |= curses.color_pair(
                _ColorPairIndex.MAGENTA.value
            )
        elif attributes & AttributeBit.CYAN:
            cleaned_attributes |= curses.color_pair(_ColorPairIndex.CYAN.value)
        return cleaned_attributes
