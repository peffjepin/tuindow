from typing import NamedTuple
from typing import Tuple


class Rect(NamedTuple):
    left: int
    top: int
    width: int
    height: int

    def __iter__(self):
        return iter((self.left, self.top, self.width, self.height))

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def intersects(self, other: "Rect") -> bool:
        """
        None of the following can be True during a collision:
            r1 left   >= r2 right
            r1 top    >= r2 bottom
            r1 right  <= r2 left
            r1 bottom <= r2 top
        """
        return (
            self.left < other.right
            and self.top < other.bottom
            and self.right > other.left
            and self.bottom > other.top
        )

    def contains(self, other: "Rect") -> bool:
        return (
            other.left >= self.left
            and other.top >= self.top
            and other.right <= self.right
            and other.bottom <= self.bottom
        )


class Padding(NamedTuple):
    fills: Tuple[str, str]
    values: Tuple[int, int]
    pads: Tuple[str, str]

    @classmethod
    def calculate(
        cls, fills: Tuple[str, str], values: Tuple[int, int]
    ) -> "Padding":
        return cls(
            fills,
            values,
            (
                fills[0] * values[0] if values[0] >= 0 else "",
                fills[1] * values[1] if values[1] >= 0 else "",
            ),
        )


class Style(NamedTuple):
    padding: Padding = Padding.calculate((" ", " "), (0, 0))
    fill: str = " "
