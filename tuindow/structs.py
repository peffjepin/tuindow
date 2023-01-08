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

    def calculate_pads(self, string: str, max_length: int) -> Tuple[str, str]:
        final_display_length = max_length - sum(map(len, self.padding.pads))
        remaining = final_display_length - len(string)

        if remaining == 0:
            return self.padding.pads

        left_pad, right_pad = self.padding.pads

        if self.padding.values[0] >= 0:
            if self.padding.values[1] < 0:
                # right pad variable/left pad constant -- extend right with padding fill
                right_pad = remaining * self.padding.fills[1] + right_pad
            else:
                # both pads constant, extend display with default fill
                right_pad = (remaining * self.fill) + right_pad

        elif self.padding.values[1] >= 0:
            # left pad is variable/right pad is constant -- extend left with padding fill
            left_pad += remaining * self.padding.fills[0]

        else:
            # both pads are variable, treat values like weights and fill with padding fill
            total = sum(self.padding.values)
            left_extra = int(round(self.padding.values[0] / total * remaining))
            right_extra = int(
                round(self.padding.values[1] / total * remaining))

            # fix off by one errors from rounding, leaving higher weight with the extra padding
            off = remaining - (left_extra + right_extra)
            assert off in (-1, 0, 1)
            if off == 1:
                if left_extra >= right_extra:
                    left_extra += off
                else:
                    right_extra += off
            elif off == -1:
                if left_extra >= right_extra:
                    right_extra += off
                else:
                    left_extra += off
            left_pad += self.padding.fills[0] * left_extra
            right_pad += self.padding.fills[1] * right_extra

        return left_pad, right_pad
