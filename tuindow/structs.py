from typing import NamedTuple
from typing import Tuple


class Rect(NamedTuple):
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


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
