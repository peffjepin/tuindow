import contextlib
import time

from typing import Generator
from typing import Callable
from typing import Optional

from . import _curses

from .buffers import Panel


__all__ = (
    "TuindowError",
    "init",
    "update",
    "draw",
    "keys",
    "Panel",
    "BACKSPACE",
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
def init(onresize: _ResizeCallback, tps=144):
    global _instance
    global _clock

    _clock = Clock(tps)
    _instance = _curses.Instance(onresize)
    with _instance:
        onresize(*_instance.size)
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
        for panel in panels:
            for i, line in enumerate(panel):
                if panel.dirty or line.dirty:
                    _instance.write_text(
                        panel.left, panel.top + i, line.display
                    )
    except _curses.CursesError:
        if _instance.size != size:
            _instance.cache_pending_keys()
            return draw(panel)
        raise


@requires_init
def keys() -> Generator[str, None, None]:
    assert _instance
    return _instance.keys
