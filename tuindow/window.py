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
from typing import Tuple

from . import buffers
from . import structs
from . import validation


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

    def __eq__(self, other: object) -> bool:
        return str(other) == self.value


_curses_key_map = {
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
    ascii.ESC: SpecialKeys.ESCAPE.value,
    **{ord(c): c for c in string.printable},
}


class _CursesInput:
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
            return next(self)
        return _curses_key_map.get(curses_ch, chr(curses_ch))


class Window:
    clock: Clock

    _stdscr: curses.window
    _input: _CursesInput
    _default_panel: Optional[buffers.Panel] = None
    _user_panels: List[buffers.Panel]

    def __init__(self, tps: int = 144):
        self.clock = Clock(tps)
        self._user_panels = []
        self._init_curses()

    def _init_curses(self) -> None:
        self._stdscr = curses.initscr()
        self._input = _CursesInput(self._stdscr, self._do_layout)
        self._stdscr.keypad(True)
        self._stdscr.nodelay(True)
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
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
            self._default_panel.rect = self.rect
        self.layout()
        if self._user_panels:
            with validation.pool(WindowError):
                for i, p in enumerate(self._user_panels):
                    p.dirty = True
                    validation.rect_in_bounds("panel", p.rect, self.rect)

                    if i == len(self._user_panels) - 1:
                        break

                    for j in range(i+1, len(self._user_panels)):
                        validation.rects_dont_collide(
                            "panel", p.rect, self._user_panels[j].rect)

    def layout(self) -> None:
        """stub for subclass to implement a resize event handler"""

    def _check_panel_collisions(self, panel: buffers.Panel) -> None:
        with validation.pool(WindowError):
            validation.rect_in_bounds(
                "panel", rect=panel.rect, bounds=self.rect
            )
            for other in self._user_panels:
                validation.rects_dont_collide("panel", panel.rect, other.rect)

    def panel(
        self, left: int, top: int, width: int, height: int
    ) -> buffers.Panel:
        new_panel = buffers.Panel(left, top, width, height)
        self._check_panel_collisions(new_panel)
        self._user_panels.append(new_panel)
        self._mutually_exclusive_panels()
        return new_panel

    @property
    def _boundary_rects(
        self,
    ) -> Tuple[structs.Rect, structs.Rect, structs.Rect, structs.Rect]:
        return (
            structs.Rect(-1, 0, 1, self.height),  # left
            structs.Rect(0, -1, self.width, 1),  # top
            structs.Rect(self.width, 0, 1, self.height),  # right
            structs.Rect(0, self.height, self.width, 1),  # bottom
        )

    @property
    def default_panel(self) -> buffers.Panel:
        if self._default_panel is None:
            self._default_panel = buffers.Panel(*self.rect)
        self._mutually_exclusive_panels()
        return self._default_panel

    @property
    def width(self) -> int:
        return self._stdscr.getmaxyx()[1]

    @property
    def height(self) -> int:
        return self._stdscr.getmaxyx()[0]

    @property
    def rect(self) -> structs.Rect:
        return structs.Rect(0, 0, self.width, self.height)

    @property
    def keys(self) -> typing.Iterable[str]:
        return self._input

    def tick(self) -> float:
        return next(self.clock)

    def draw(self) -> None:
        w, h = self.width, self.height
        try:
            self._draw_unsafe()
        except WindowError:
            if w != self.width or h != self.height:
                # resize occurred, clean the pending user input
                # so we can consume the resize event and trigger
                # a window re-layout then try again
                self._input.cache_pending_keys()
                self.draw()
            else:
                raise

    def _draw_unsafe(self):
        """
        We have no control over the window resizing so all draw calls
        are inheirently unsafe.

        It is up to the caller of this method to recognize the resize
        and make another draw attempt
        """

        if self._default_panel:
            panels = [self._default_panel]
        else:
            panels = self._user_panels

        for panel in panels:
            for i, line in enumerate(panel):
                if panel.dirty or line.dirty:
                    self._draw_line(panel.left, panel.top + i, line)
                line.dirty = False
            panel.dirty = False

        self._stdscr.refresh()

    def _draw_line(self, x: int, y: int, line: buffers.Line):
        try:
            self._stdscr.addstr(y, x, line.display)
        except curses.error:
            # writing the last character in the window causes an error
            # because it places the cursor out of bounds
            if x + line.length == self.width and y == self.height - 1:
                line.dirty = False
                return
            raise WindowError(
                f"failed to draw line (length={line.length}): "
                f"at {x=}, {y=} on {self!r}"
            )

    def _mutually_exclusive_panels(self) -> None:
        if self._user_panels and self._default_panel is not None:
            raise WindowError(
                "Window objects can be used with the Window.default_panel or "
                "you can create your own panels with Window.panel calls. "
                "These panel options are mutually exclusive."
            )
