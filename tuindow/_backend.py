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
    ENTER = "\n"
    TAB = "\t"
    INSERT = "INSERT"
    HOME = "HOME"
    END = "END"
    PAGE_UP = "PAGE_UP"
    PAGE_DOWN = "PAGE_DOWN"
    KEY_BREAK = "Break key (unreliable)"
    KEY_DL = "Delete line"
    KEY_IL = "Insert line"
    KEY_EIC = "Exit insert char mode"
    KEY_CLEAR = "Clear screen"
    KEY_EOS = "Clear to end of screen"
    KEY_EOL = "Clear to end of line"
    KEY_SF = "Scroll 1 line forward"
    KEY_SR = "Scroll 1 line backward (reverse)"
    KEY_NPAGE = "Next page"
    KEY_PPAGE = "Previous page"
    KEY_STAB = "Set tab"
    KEY_CTAB = "Clear tab"
    KEY_CATAB = "Clear all tabs"
    KEY_SRESET = "Soft (partial) reset (unreliable)"
    KEY_RESET = "Reset or hard reset (unreliable)"
    KEY_PRINT = "Print"
    KEY_LL = "Home down or bottom (lower left)"
    KEY_A1 = "Upper left of keypad"
    KEY_A3 = "Upper right of keypad"
    KEY_B2 = "Center of keypad"
    KEY_C1 = "Lower left of keypad"
    KEY_C3 = "Lower right of keypad"
    KEY_BTAB = "Back tab"
    KEY_BEG = "Beg (beginning)"
    KEY_CANCEL = "Cancel"
    KEY_CLOSE = "Close"
    KEY_COMMAND = "Cmd (command)"
    KEY_COPY = "Copy"
    KEY_CREATE = "Create"
    KEY_END = "End"
    KEY_EXIT = "Exit"
    KEY_FIND = "Find"
    KEY_HELP = "Help"
    KEY_MARK = "Mark"
    KEY_MESSAGE = "Message"
    KEY_MOVE = "Move"
    KEY_NEXT = "Next"
    KEY_OPEN = "Open"
    KEY_OPTIONS = "Options"
    KEY_PREVIOUS = "Prev (previous)"
    KEY_REDO = "Redo"
    KEY_REFERENCE = "Ref (reference)"
    KEY_REFRESH = "Refresh"
    KEY_REPLACE = "Replace"
    KEY_RESTART = "Restart"
    KEY_RESUME = "Resume"
    KEY_SAVE = "Save"
    KEY_SBEG = "Shifted Beg (beginning)"
    KEY_SCANCEL = "Shifted Cancel"
    KEY_SCOMMAND = "Shifted Command"
    KEY_SCOPY = "Shifted Copy"
    KEY_SCREATE = "Shifted Create"
    KEY_SDC = "Shifted Delete char"
    KEY_SDL = "Shifted Delete line"
    KEY_SELECT = "Select"
    KEY_SEND = "Shifted End"
    KEY_SEOL = "Shifted Clear line"
    KEY_SEXIT = "Shifted Exit"
    KEY_SFIND = "Shifted Find"
    KEY_SHELP = "Shifted Help"
    KEY_SHOME = "Shifted Home"
    KEY_SIC = "Shifted Input"
    KEY_SLEFT = "Shifted Left arrow"
    KEY_SMESSAGE = "Shifted Message"
    KEY_SMOVE = "Shifted Move"
    KEY_SNEXT = "Shifted Next"
    KEY_SOPTIONS = "Shifted Options"
    KEY_SPREVIOUS = "Shifted Prev"
    KEY_SPRINT = "Shifted Print"
    KEY_SREDO = "Shifted Redo"
    KEY_SREPLACE = "Shifted Replace"
    KEY_SRIGHT = "Shifted Right arrow"
    KEY_SRSUME = "Shifted Resume"
    KEY_SSAVE = "Shifted Save"
    KEY_SSUSPEND = "Shifted Suspend"
    KEY_SUNDO = "Shifted Undo"
    KEY_SUSPEND = "Suspend"
    KEY_UNDO = "Undo"
    KEY_MOUSE = "Mouse event has occurred"

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
    curses.KEY_IC: SpecialKeys.INSERT.value,
    curses.KEY_IC: SpecialKeys.INSERT.value,
    curses.KEY_HOME: SpecialKeys.HOME.value,
    curses.KEY_END: SpecialKeys.END.value,
    curses.KEY_NPAGE: SpecialKeys.PAGE_DOWN.value,
    curses.KEY_PPAGE: SpecialKeys.PAGE_UP.value,
    curses.KEY_BREAK: SpecialKeys.KEY_BREAK.value,
    curses.KEY_DL: SpecialKeys.KEY_DL.value,
    curses.KEY_IL: SpecialKeys.KEY_IL.value,
    curses.KEY_EIC: SpecialKeys.KEY_EIC.value,
    curses.KEY_CLEAR: SpecialKeys.KEY_CLEAR.value,
    curses.KEY_EOS: SpecialKeys.KEY_EOS.value,
    curses.KEY_EOL: SpecialKeys.KEY_EOL.value,
    curses.KEY_SF: SpecialKeys.KEY_SF.value,
    curses.KEY_SR: SpecialKeys.KEY_SR.value,
    curses.KEY_NPAGE: SpecialKeys.KEY_NPAGE.value,
    curses.KEY_PPAGE: SpecialKeys.KEY_PPAGE.value,
    curses.KEY_STAB: SpecialKeys.KEY_STAB.value,
    curses.KEY_CTAB: SpecialKeys.KEY_CTAB.value,
    curses.KEY_CATAB: SpecialKeys.KEY_CATAB.value,
    curses.KEY_SRESET: SpecialKeys.KEY_SRESET.value,
    curses.KEY_RESET: SpecialKeys.KEY_RESET.value,
    curses.KEY_PRINT: SpecialKeys.KEY_PRINT.value,
    curses.KEY_LL: SpecialKeys.KEY_LL.value,
    curses.KEY_A1: SpecialKeys.KEY_A1.value,
    curses.KEY_A3: SpecialKeys.KEY_A3.value,
    curses.KEY_B2: SpecialKeys.KEY_B2.value,
    curses.KEY_C1: SpecialKeys.KEY_C1.value,
    curses.KEY_C3: SpecialKeys.KEY_C3.value,
    curses.KEY_BTAB: SpecialKeys.KEY_BTAB.value,
    curses.KEY_BEG: SpecialKeys.KEY_BEG.value,
    curses.KEY_CANCEL: SpecialKeys.KEY_CANCEL.value,
    curses.KEY_CLOSE: SpecialKeys.KEY_CLOSE.value,
    curses.KEY_COMMAND: SpecialKeys.KEY_COMMAND.value,
    curses.KEY_COPY: SpecialKeys.KEY_COPY.value,
    curses.KEY_CREATE: SpecialKeys.KEY_CREATE.value,
    curses.KEY_END: SpecialKeys.KEY_END.value,
    curses.KEY_EXIT: SpecialKeys.KEY_EXIT.value,
    curses.KEY_FIND: SpecialKeys.KEY_FIND.value,
    curses.KEY_HELP: SpecialKeys.KEY_HELP.value,
    curses.KEY_MARK: SpecialKeys.KEY_MARK.value,
    curses.KEY_MESSAGE: SpecialKeys.KEY_MESSAGE.value,
    curses.KEY_MOVE: SpecialKeys.KEY_MOVE.value,
    curses.KEY_NEXT: SpecialKeys.KEY_NEXT.value,
    curses.KEY_OPEN: SpecialKeys.KEY_OPEN.value,
    curses.KEY_OPTIONS: SpecialKeys.KEY_OPTIONS.value,
    curses.KEY_PREVIOUS: SpecialKeys.KEY_PREVIOUS.value,
    curses.KEY_REDO: SpecialKeys.KEY_REDO.value,
    curses.KEY_REFERENCE: SpecialKeys.KEY_REFERENCE.value,
    curses.KEY_REFRESH: SpecialKeys.KEY_REFRESH.value,
    curses.KEY_REPLACE: SpecialKeys.KEY_REPLACE.value,
    curses.KEY_RESTART: SpecialKeys.KEY_RESTART.value,
    curses.KEY_RESUME: SpecialKeys.KEY_RESUME.value,
    curses.KEY_SAVE: SpecialKeys.KEY_SAVE.value,
    curses.KEY_SBEG: SpecialKeys.KEY_SBEG.value,
    curses.KEY_SCANCEL: SpecialKeys.KEY_SCANCEL.value,
    curses.KEY_SCOMMAND: SpecialKeys.KEY_SCOMMAND.value,
    curses.KEY_SCOPY: SpecialKeys.KEY_SCOPY.value,
    curses.KEY_SCREATE: SpecialKeys.KEY_SCREATE.value,
    curses.KEY_SDC: SpecialKeys.KEY_SDC.value,
    curses.KEY_SDL: SpecialKeys.KEY_SDL.value,
    curses.KEY_SELECT: SpecialKeys.KEY_SELECT.value,
    curses.KEY_SEND: SpecialKeys.KEY_SEND.value,
    curses.KEY_SEOL: SpecialKeys.KEY_SEOL.value,
    curses.KEY_SEXIT: SpecialKeys.KEY_SEXIT.value,
    curses.KEY_SFIND: SpecialKeys.KEY_SFIND.value,
    curses.KEY_SHELP: SpecialKeys.KEY_SHELP.value,
    curses.KEY_SHOME: SpecialKeys.KEY_SHOME.value,
    curses.KEY_SIC: SpecialKeys.KEY_SIC.value,
    curses.KEY_SLEFT: SpecialKeys.KEY_SLEFT.value,
    curses.KEY_SMESSAGE: SpecialKeys.KEY_SMESSAGE.value,
    curses.KEY_SMOVE: SpecialKeys.KEY_SMOVE.value,
    curses.KEY_SNEXT: SpecialKeys.KEY_SNEXT.value,
    curses.KEY_SOPTIONS: SpecialKeys.KEY_SOPTIONS.value,
    curses.KEY_SPREVIOUS: SpecialKeys.KEY_SPREVIOUS.value,
    curses.KEY_SPRINT: SpecialKeys.KEY_SPRINT.value,
    curses.KEY_SREDO: SpecialKeys.KEY_SREDO.value,
    curses.KEY_SREPLACE: SpecialKeys.KEY_SREPLACE.value,
    curses.KEY_SRIGHT: SpecialKeys.KEY_SRIGHT.value,
    curses.KEY_SRSUME: SpecialKeys.KEY_SRSUME.value,
    curses.KEY_SSAVE: SpecialKeys.KEY_SSAVE.value,
    curses.KEY_SSUSPEND: SpecialKeys.KEY_SSUSPEND.value,
    curses.KEY_SUNDO: SpecialKeys.KEY_SUNDO.value,
    curses.KEY_SUSPEND: SpecialKeys.KEY_SUSPEND.value,
    curses.KEY_UNDO: SpecialKeys.KEY_UNDO.value,
    curses.KEY_MOUSE: SpecialKeys.KEY_MOUSE.value,
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
