"""
The public api to be exposed by the package.
"""

import contextlib
import time
import string

from typing import Generator
from typing import Callable
from typing import Optional

from . import _backend
from . import structs

from .buffers import Panel
from .window import Window
from .cursor import Cursor
from .cursor import Overscroll

__all__ = (
    "TuindowError",
    "init",
    "update",
    "draw",
    "keys",
    "structs",
    "set_active_cursor",
    "clear_active_cursor",
    "Panel",
    "SpecialKeys",
    "BACKSPACE",
    "DELETE",
    "ESCAPE",
    "F0",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "DOWN",
    "LEFT",
    "RIGHT",
    "UP",
    "AttributeBit",
    "BLINK",
    "BOLD",
    "DIM",
    "REVERSE",
    "STANDOUT",
    "UNDERLINE",
    "PRINTABLE",
    "Overscroll",
    "RED",
    "GREEN",
    "YELLOW",
    "BLUE",
    "MAGENTA",
    "CYAN",
)

PRINTABLE = set(c for c in string.printable)

SpecialKeys = _backend.SpecialKeys
BACKSPACE = _backend.SpecialKeys.BACKSPACE
DELETE = _backend.SpecialKeys.DELETE
ESCAPE = _backend.SpecialKeys.ESCAPE
F0 = _backend.SpecialKeys.F0
F1 = _backend.SpecialKeys.F1
F2 = _backend.SpecialKeys.F2
F3 = _backend.SpecialKeys.F3
F4 = _backend.SpecialKeys.F4
F5 = _backend.SpecialKeys.F5
F6 = _backend.SpecialKeys.F6
F7 = _backend.SpecialKeys.F7
F8 = _backend.SpecialKeys.F8
F9 = _backend.SpecialKeys.F9
F10 = _backend.SpecialKeys.F10
F11 = _backend.SpecialKeys.F11
F12 = _backend.SpecialKeys.F12
DOWN = _backend.SpecialKeys.DOWN
LEFT = _backend.SpecialKeys.LEFT
RIGHT = _backend.SpecialKeys.RIGHT
UP = _backend.SpecialKeys.UP

AttributeBit = _backend.AttributeBit
BLINK = AttributeBit.BLINK
BOLD = AttributeBit.BOLD
DIM = AttributeBit.DIM
REVERSE = AttributeBit.REVERSE
STANDOUT = AttributeBit.STANDOUT
UNDERLINE = AttributeBit.UNDERLINE
RED = AttributeBit.RED
GREEN = AttributeBit.GREEN
YELLOW = AttributeBit.YELLOW
BLUE = AttributeBit.BLUE
MAGENTA = AttributeBit.MAGENTA
CYAN = AttributeBit.CYAN


class _Clock:
    _interval: float
    _tps: int
    _previous: float
    _ticks: int

    def __init__(self, tps: int) -> None:
        self._interval = 1 / tps
        self._tps = tps
        self._previous = time.time()
        self._ticks = 0

    def __next__(self) -> float:
        remaining = self._interval - (time.time() - self._previous)
        if remaining > 0:
            time.sleep(remaining)
        now = time.time()
        dt = now - self._previous
        self._previous = now
        self._ticks += 1
        return dt

    @property
    def ticks(self) -> int:
        return self._ticks

    @property
    def tps(self) -> int:
        return self._tps

    @tps.setter
    def tps(self, value: int) -> None:
        self._tps = value
        self._interval = 1 / value


_instance: Optional[_backend.Instance] = None
_clock: _Clock
_window: Window
_active_cursor: Optional[Cursor] = None


class TuindowError(Exception):
    pass


def _requires_init(function):
    """
    Decorate a function such that it raises an apprioriate error message when
    not called from within a `with tuindow.init(...)` block.
    """

    def inner(*args, **kwargs):
        if _instance is None:
            raise TuindowError(
                f"{function!r} must be called within a `with tuindow.init(...):` block"
            )
        return function(*args, **kwargs)

    return inner


def set_active_cursor(cursor: Cursor) -> None:
    """
    Sets the cursor as active -- only one cursor will be active at once
    and only the active cursor will be drawn"
    """

    global _active_cursor
    _active_cursor = cursor


def clear_active_cursor() -> None:
    """
    Clears the active cursor -- no cursor will be drawn.
    """

    global _active_cursor
    _active_cursor = None


@contextlib.contextmanager
def init(on_resize: Callable[[int, int], None], tps: int = 144):
    """
    Initializes the curses window on entering the context and
    tears down curses on exit ensuring terminal remains in a usable state.

    on_resize:
        the given function should accept (width, height) in characters as parameters
        will be called immediately after initialization
        will also be called whenever text size changes

    tps (ticks per second):
        this will be kept by calling tuindow.update() in a loop

    Example:
        import tuindow

        panel = tuindow.Panel()

        def layout(width, height):
            panel.rect = (0, 0, width, height)

        with tuindow.init(layout):
            while 1:
                for key in tuindow.keys():
                    ...
                tuindow.draw(panel)
                tuindow.update()
    """

    global _instance
    global _clock
    global _window

    _clock = _Clock(tps)
    _window = Window(0, 0, 1, 1)

    def resize_callback(width: int, height: int) -> None:
        _window.resize(0, 0, width, height)
        on_resize(width, height)

    _instance = _backend.Instance(resize_callback)
    with _instance:
        resize_callback(*_instance.size)
        yield
    _instance = None


@_requires_init
def update() -> float:
    """
    Called in a loop to update the display and keep to a reasonable tickrate.

    Returns time (in seconds) since the previous tuindow.update() call.

    Example:
        import tuindow

        ...

        with tuindow.init(...):
            while 1:
                for k in tuindow.keys():
                    ...
                tuindow.draw(...)
                tuindow.update()

        ...
    """

    assert _instance
    global _clock
    _instance.update_display()
    return next(_clock)


@_requires_init
def draw(*panels: Panel) -> None:
    """
    Draws each panel ignoring regions that haven't changed.
    """

    assert _instance
    size = _instance.size
    try:
        _unsafe_draw(*panels)
    except _backend.CursesError:
        if _instance.size != size:
            _instance.cache_pending_keys()
            return draw(*panels)
        raise


@_requires_init
def keys() -> Generator[str, None, None]:
    """
    Yields keys pressed by the user since the last call to this function.

    Example:
            ...

            for key in tuindow.keys():
                if key == "a":
                    ...
                elif key == "A":
                    ...
                elif key == "\n":
                    ...
                elif key == tuindow.SpecialKey.BACKSPACE:
                    ...
                elif key == tuindow.BACKSPACE:
                    # alias to tuindow.SpecialKey.BACKSPACE
                    ...
                elif key in tuindow.PRINTABLE:
                    # set of printable single character keys
                    ...
            ...
    """

    assert _instance
    return _instance.keys


def _unsafe_draw(*panels: Panel) -> None:
    global _window
    assert _instance

    active_cursor_drawn = False

    for panel in panels:
        dirty = _window.draw(panel.display_rect)
        for i, line in enumerate(panel):
            if dirty or line.dirty:
                _instance.write_text(
                    panel.left,
                    panel.top + i,
                    line.display,
                    line.style.attributes,
                )
            line.dirty = False

        if _active_cursor is panel.cursor:
            _handle_active_cursor(panel, panel.cursor)
            active_cursor_drawn = True

    if not active_cursor_drawn:
        _instance.disable_cursor()


def _handle_active_cursor(panel: Panel, cursor: Cursor) -> None:
    """
    Enable and draw the cursor aswell as panning the line underneath the cursor
    if the lines data extends beyond the display window
    """
    assert _instance

    ln = panel[cursor.line]
    pads = ln.style.calculate_pads(ln.data, ln.length)

    # pan display to cursor if it is overflowing on an active cursor line
    if ln.style.padding.values[1] < 0 and pads[1]:
        # if right padding is variable length it is going
        # to fill the space where our cursor should go
        # so we will reclaim one of those characters for the cursor
        pads = (pads[0], pads[1][1:])

    remaining = ln.length - sum(map(len, pads))
    panned_display = cursor.pan(remaining)
    if len(panned_display) < remaining:
        panned_display += " " * (remaining - len(panned_display))

    # if cursor extends beyond the end of the display region we will clamp it
    cursor_x = min(
        panel.left + len(pads[0]) + cursor.index,
        panel.left + panel.width - 1 - len(pads[1]),
    )
    cursor_y = cursor.line + panel.top

    _instance.write_text(
        panel.left,
        cursor_y,
        pads[0] + panned_display + pads[1],
        ln.style.attributes,
    )
    _instance.draw_cursor(cursor_x, cursor_y)
