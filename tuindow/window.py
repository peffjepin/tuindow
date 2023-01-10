"""
This module is used internally for tracking `dirty` screen regions.
"""

from typing import List

from . import structs


class BoundsError(Exception):
    def __init__(self, rect: structs.Rect, bounds: "Window"):
        super().__init__(f"{rect!r} out of bounds: {bounds!r}")


class Window:
    """
    Represents the screen as a whole.

    Drawing to this window doesn't do anything visual, only logical.
    """

    _rect: structs.Rect
    _drawn: List[structs.Rect]
    _ndrawn: int

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self._rect = structs.Rect(x, y, width, height)
        self._drawn = []
        self._ndrawn = 0

    def resize(self, x: int, y: int, width: int, height: int) -> None:
        """
        Resize the window and invalidate all previously drawn regions.
        """

        self._rect = structs.Rect(x, y, width, height)
        self._ndrawn = 0

    def draw(self, rect: structs.Rect) -> bool:
        """
        Since Rects are immutable we can track rects based on identity.
        When a rect is drawn to the window it invalidates any rects currently
        in the window that are intersecting with the newly drawn rect.

        This function only returns False if the window already
        contains `rect` (by identity).

        Otherwise this function returns True.

        A return value of False means `rect` isn't `dirty` and only
        the lines within that rect that have changed need to be redrawn.
        """

        # iterate rects and remove intersecting rects by sliding them to the back
        # of the array and masking them off
        if not self._rect.contains(rect):
            raise BoundsError(rect, self)

        index = 0
        while index != self._ndrawn:
            drawn_rect = self._drawn[index]
            if rect is drawn_rect:
                # no rects in the drawn list intersect so if `rect`
                # collides with itself by identity we know it's previously
                # drawn state hasn't been invalidated
                # (unless data has gone stale) which is handled elsewhere
                return False
            if rect.intersects(drawn_rect):
                if index != self._ndrawn - 1:
                    self._drawn[index], self._drawn[self._ndrawn - 1] = (
                        self._drawn[self._ndrawn - 1],
                        self._drawn[index],
                    )
                self._ndrawn -= 1
            else:
                index += 1

        # ever other rect this rect intersects with has been cleared,
        # now we just have to add this rect to the drawn list
        if len(self._drawn) == self._ndrawn:
            self._drawn.append(rect)
        else:
            self._drawn[self._ndrawn] = rect
        self._ndrawn += 1
        return True
