import time
import curses
import collections
import typing
import enum
import string

from curses import ascii

from typing import Deque
from typing import Optional
from typing import List
from typing import NamedTuple
from typing import Tuple

from . import buffers


class WindowError(Exception):
    pass


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


class SpecialKey(enum.Enum):
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

    def __eq__(self, other: object) -> bool:
        return str(other) == self.value


_curses_key_map = {
    curses.KEY_BACKSPACE: SpecialKey.BACKSPACE.value,
    curses.KEY_F0: SpecialKey.F0.value,
    curses.KEY_F1: SpecialKey.F1.value,
    curses.KEY_F2: SpecialKey.F2.value,
    curses.KEY_F3: SpecialKey.F3.value,
    curses.KEY_F4: SpecialKey.F4.value,
    curses.KEY_F5: SpecialKey.F5.value,
    curses.KEY_F6: SpecialKey.F6.value,
    curses.KEY_F7: SpecialKey.F7.value,
    curses.KEY_F8: SpecialKey.F8.value,
    curses.KEY_F9: SpecialKey.F9.value,
    curses.KEY_F10: SpecialKey.F10.value,
    curses.KEY_F11: SpecialKey.F11.value,
    curses.KEY_F12: SpecialKey.F12.value,
    curses.KEY_DOWN: SpecialKey.DOWN.value,
    curses.KEY_LEFT: SpecialKey.LEFT.value,
    curses.KEY_RIGHT: SpecialKey.RIGHT.value,
    curses.KEY_UP: SpecialKey.UP.value,
    ascii.ESC: SpecialKey.ESCAPE.value,
    **{ord(c): c for c in string.printable},
}


class CursesInput:
    _cache: Deque[str]
    _dummy_cache: Deque[str]
    _stdscr: curses.window
    _resize_callback: typing.Callable[[], None]

    def __init__(
        self, stdscr: curses.window, resize_callback: typing.Callable[[], None]
    ) -> None:
        self._stdscr = stdscr
        self._resize_callback = resize_callback
        self._cache = collections.deque()
        self._dummy_cache = collections.deque()

    def cache_pending_keys(self) -> None:
        # patch cache member so iteration doesn't consume cache
        # resulting in an infinite loop
        cache = self._cache
        self._cache = self._dummy_cache

        cache.extend((key for key in self))
        self._cache = cache

    def __iter__(self) -> typing.Iterator[str]:
        return self

    def __next__(self):
        if self._cache:
            return self._cache.popleft()
        curses_ch = self._stdscr.getch()
        if curses_ch == -1:
            raise StopIteration
        elif curses_ch == curses.KEY_RESIZE:
            self._resize_callback()
            return self._get_key()
        return _curses_key_map.get(curses_ch, chr(curses_ch))


class AABB(NamedTuple):
    left: int
    top: int
    width: int
    height: int


def _aabb_collides(b1: AABB, b2: AABB):
    """
    None of the following can be True during a collision:
        b1 left   >= b2 right
        b1 top    >= b2 bottom
        b1 right  <= b2 left
        b1 bottom <= b2 top
    """
    return (
        b1.left < b2.left + b2.width and
        b1.top < b2.top + b2.height and
        b1.left + b1.width > b2.left and
        b1.top + b1.height > b2.top
    )


class Window:
    clock: Clock

    _stdscr: curses.window
    _input: CursesInput
    _default_panel: Optional[buffers.Panel] = None
    _user_panels: List[buffers.Panel]

    def __init__(self, tps: int = 144):
        self.clock = Clock(tps)
        self._user_panels = []
        self._init_curses()

    def _init_curses(self) -> None:
        self._stdscr = curses.initscr()
        self._input = CursesInput(self._stdscr, self._do_layout)
        self._stdscr.keypad(True)
        self._stdscr.nodelay(True)
        curses.noecho()
        curses.cbreak()
        self._stdscr.clear()
        self._stdscr.refresh()

    def _cleanup_curses(self) -> None:
        self._stdscr.keypad(False)
        self._stdscr.nodelay(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    def __enter__(self) -> "Window":
        return self

    def __exit__(self, *args) -> None:
        self._cleanup_curses()

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}(width={self.width}, "
            f"height={self.height}, tps={self.clock.tps})>"
        )

    def _do_layout(self) -> None:
        if self._default_panel:
            self._default_panel.width = self.width
            self._default_panel.height = self.height
        self.layout()

    def layout(self) -> None:
        """stub for subclass to implement a resize event handler"""

    def _check_panel_collisions(self, panel: buffers.Panel) -> None:
        box = AABB(panel.x, panel.y, panel.width, panel.height)
        if any(_aabb_collides(box, edge_box) for edge_box in self._aabb_boundaries):
            raise WindowError(
                "Trying to create out of bounds panel: "
                f"{panel=!r}, window={self!r}"
            )

        collisions_with_existing = [_aabb_collides(
            box, AABB(p.x, p.y, p.width, p.height)) for p in self._user_panels]
        if any(collisions_with_existing):
            error = f"Panel collision detected: {panel=!r} collides with"
            for i, collides in enumerate(collisions_with_existing):
                error += f" {self._user_panels[i]!r}"
            raise WindowError(error)

    def panel(self, x: int, y: int, width: int, height: int) -> buffers.Panel:
        if self._default_panel:
            self._raise_mutually_exclusive_panels()
        new_panel = buffers.Panel(x, y, width, height)
        self._check_panel_collisions(new_panel)
        self._user_panels.append(new_panel)
        return new_panel

    @property
    def _aabb_boundaries(self) -> Tuple[AABB, AABB, AABB, AABB]:
        return (
            AABB(-1,  0, 1, self.height),         # left
            AABB(0, -1, self.width, 1),           # top
            AABB(self.width, 0, 1, self.height),  # right
            AABB(0, self.height, self.width, 1),  # bottom
        )

    @property
    def default_panel(self) -> buffers.Panel:
        if self._user_panels:
            self._raise_mutually_exclusive_panels()
        if not self._default_panel:
            self._default_panel = buffers.Panel(0, 0, self.width, self.height)
        return self._default_panel

    @property
    def width(self) -> int:
        return self._stdscr.getmaxyx()[1]

    @property
    def height(self) -> int:
        return self._stdscr.getmaxyx()[0]

    @property
    def keys(self) -> typing.Iterable[str]:
        return self._input

    def tick(self) -> float:
        return next(self.clock)

    def draw(self) -> None:
        if self._default_panel:
            panels = [self._default_panel]
        else:
            panels = self._user_panels

        for panel in panels:
            for i, line in enumerate(panel):
                self._draw_line(panel.x, panel.y + i, line)

        self._stdscr.refresh()

    def _draw_line(self, x: int, y: int, line: buffers.Line):
        if line.dirty:
            try:
                # clear user input before drawing in case
                # we need to react to a resize key event
                self._input.cache_pending_keys()
                self._stdscr.insstr(y, x, line.display)
            except curses.error:
                raise WindowError(
                    f"failed to draw line (length={line.length}): "
                    f"{line.display!r} at {x=}, {y=} on {self!r}"
                )
        line.dirty = False

    def _raise_mutually_exclusive_panels(self) -> None:
        raise WindowError(
            "Window objects can be used with the Window.default_panel or "
            "you can create your own panels with Window.panel calls. "
            "These panel options are mutually exclusive."
        )
