"""
Some data structures representing common themes in the package.

This module should not rely on other modules within the package.
"""

from typing import NamedTuple
from typing import Tuple
from typing import Optional
from typing import Union


class Rect(NamedTuple):
    """
    A rectangular region within a screen space coordinate system
    where (0, 0) is the top left corner.
    """

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
        Returns true if the two Rects are intersecting.
        """

        return (
            self.left < other.right
            and self.top < other.bottom
            and self.right > other.left
            and self.bottom > other.top
        )

    def contains(self, other: "Rect") -> bool:
        """
        Returns true if the other rect is entirely contained within this one.
        """

        return (
            other.left >= self.left
            and other.top >= self.top
            and other.right <= self.right
            and other.bottom <= self.bottom
        )


class Padding(NamedTuple):
    """
    Represents padding on the left and right side of a string.

    fills: (left, right)
        the single characters used to fill in respective pads
    values: (left, right)
        the integer lengths of the respective pads
        values < 0 are considered variable length padding and treated as weights
    pads: (left, right)
        the actual pads described by the former attributes
    """

    fills: Tuple[str, str]
    values: Tuple[int, int]
    pads: Tuple[str, str]

    @classmethod
    def calculate(
        cls, fills: Tuple[str, str], values: Tuple[int, int]
    ) -> "Padding":
        """
        Returns a Padding object who's pads are
        calculated from the given parameters.
        """

        return cls(
            fills,
            values,
            (
                fills[0] * values[0] if values[0] >= 0 else "",
                fills[1] * values[1] if values[1] >= 0 else "",
            ),
        )


class Style(NamedTuple):
    """
    The cumulative visual configuration for a string to be displayed
    on the screen.

    padding:
        see: tuindow.structs.Padding
    fill:
        the fill character to use if the data is not long
        enough to fill it's assigned space
    attributes:
        OR'd together tuindow.AttributeBit values
    """

    padding: Padding = Padding.calculate((" ", " "), (0, 0))
    fill: str = " "
    attributes: int = 0

    def padding_fills_equal(
        self, new_fills: Union[str, Tuple[str, str]]
    ) -> bool:
        if isinstance(new_fills, str):
            new_fills = (new_fills, new_fills)
        return new_fills == self.padding.fills

    def padding_values_equal(
        self, new_values: Union[int, Tuple[int, int]]
    ) -> bool:
        if isinstance(new_values, int):
            new_values = (new_values, new_values)
        return new_values == self.padding.values

    @classmethod
    def from_keywords(
        cls,
        fill: str = " ",
        padding_fills: Optional[Union[str, Tuple[str, str]]] = None,
        padding: Union[int, Tuple[int, int]] = (0, 0),
        attributes: int = 0,
    ) -> "Style":
        """
        Initializes a Style object from keywords.

        fill:
            the fill character to use when there is extra space leftover
            must be a string of length 1
        padding_fills:
            like fill but used for padding
            if not given defaults to `fill`
            a single string (ex padding_fills='!') is interpreted as padding_fills=('!', '!')
        padding:
            the length of the (left, right) padding
            a scalar value (ex padding=1) is interpreted as padding=(1, 1)
        attributes:
            OR'd together tuindow.AttributeBit values
        """

        if padding_fills is None:
            padding_fills = (fill, fill)
        elif isinstance(padding_fills, str):
            padding_fills = (padding_fills, padding_fills)
        if isinstance(padding, int):
            padding = (padding, padding)
        return cls(
            padding=Padding.calculate(padding_fills, padding),
            fill=fill,
            attributes=attributes,
        )

    def calculate_pads(self, string: str, max_length: int) -> Tuple[str, str]:
        """
        Returns the (left_pad, right_pad) values for padding `string`
        assuming a maximum line length of `max_length`.
        """

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
                # caller is responsible for filling the remaining display
                pass

        elif self.padding.values[1] >= 0:
            # left pad is variable/right pad is constant -- extend left with padding fill
            left_pad += remaining * self.padding.fills[0]

        else:
            # both pads are variable, treat values like weights and fill with padding fill
            total = sum(self.padding.values)
            left_extra = int(round(self.padding.values[0] / total * remaining))
            right_extra = int(
                round(self.padding.values[1] / total * remaining)
            )

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
