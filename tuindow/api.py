import contextlib
import time

from typing import Generator
from typing import Callable
from typing import Optional

from . import _curses

from .buffers import Panel
from .window import Window
from .cursor import Cursor


__all__ = (
    "TuindowError",
    "init",
    "update",
    "draw",
    "keys",
    "Panel",
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
)

BACKSPACE = _curses.SpecialKeys.BACKSPACE
DELETE = _curses.SpecialKeys.DELETE
ESCAPE = _curses.SpecialKeys.ESCAPE
F0 = _curses.SpecialKeys.F0
F1 = _curses.SpecialKeys.F1
F2 = _curses.SpecialKeys.F2
F3 = _curses.SpecialKeys.F3
F4 = _curses.SpecialKeys.F4
F5 = _curses.SpecialKeys.F5
F6 = _curses.SpecialKeys.F6
F7 = _curses.SpecialKeys.F7
F8 = _curses.SpecialKeys.F8
F9 = _curses.SpecialKeys.F9
F10 = _curses.SpecialKeys.F10
F11 = _curses.SpecialKeys.F11
F12 = _curses.SpecialKeys.F12
DOWN = _curses.SpecialKeys.DOWN
LEFT = _curses.SpecialKeys.LEFT
RIGHT = _curses.SpecialKeys.RIGHT
UP = _curses.SpecialKeys.UP


class Clock:
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


_instance: Optional[_curses.Instance] = None
_clock: Clock
_window: Window
_ResizeCallback = Callable[[int, int], None]


class TuindowError(Exception):
    pass


def requires_init(function):
    def inner(*args, **kwargs):
        if _instance is None:
            raise TuindowError(
                f"{function!r} must be called within a `with tuindow.init(...):` block"
            )
        return function(*args, **kwargs)

    return inner


@contextlib.contextmanager
def init(on_resize: _ResizeCallback, tps=144):
    global _instance
    global _clock
    global _window

    _clock = Clock(tps)
    _window = Window(0, 0, 1, 1)

    def resize_callback(width: int, height: int) -> None:
        _window.resize(0, 0, width, height)
        on_resize(width, height)

    _instance = _curses.Instance(resize_callback)
    with _instance:
        resize_callback(*_instance.size)
        yield
    _instance = None


@requires_init
def update() -> float:
    assert _instance
    global _clock
    _instance.update_display()
    return next(_clock)


@requires_init
def draw(*panels: Panel) -> None:
    assert _instance
    size = _instance.size
    try:
        _unsafe_draw(*panels)
    except _curses.CursesError:
        if _instance.size != size:
            _instance.cache_pending_keys()
            return draw(*panels)
        raise


def _unsafe_draw(*panels: Panel) -> None:
    global _window
    assert _instance

    for panel in panels:
        dirty = _window.draw(panel.rect)
        for i, line in enumerate(panel):
            if dirty or line.dirty:
                _instance.write_text(panel.left, panel.top + i, line.display)
            line.dirty = False

        if Cursor.active is panel.cursor:
            x = panel.cursor.index+panel.left + \
                panel[panel.cursor.line].display_offset
            y = panel.cursor.line+panel.top
            _instance.draw_cursor(x, y)

    if Cursor.active is None:
        _instance.disable_cursor()


@requires_init
def keys() -> Generator[str, None, None]:
    assert _instance
    return _instance.keys
