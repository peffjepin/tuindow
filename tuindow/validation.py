import contextlib

from typing import List
from typing import Iterator
from typing import Type

from . import structs


_pooling = False
_errors: List[Exception] = []


@contextlib.contextmanager
def pool(exception_type: Type[Exception]) -> Iterator[None]:
    global _pooling
    _pooling = True
    yield
    _pooling = False
    if not _errors:
        return
    errors = _errors.copy()
    _errors.clear()
    if len(errors) == 1:
        raise exception_type(str(errors[0]))
    raise exception_type(
        "\n".join(
            (
                "Multiple validation errors occured",
                *map(
                    lambda e: f'{" " * 4}{e.__class__.__name__}({str(e)})',
                    errors,
                ),
            )
        )
    )


def _error(exc: Exception) -> None:
    if _pooling:
        _errors.append(exc)
    else:
        raise exc


def not_negative(desc: str, value: int | float) -> None:
    if value < 0:
        _error(ValueError(f"{desc} ({value!r}) cannot be negative"))


def greater_than_x(desc: str, value: int | float, x: int | float) -> None:
    if not value > x:
        _error(ValueError(f"{desc} ({value=!r}) must be greater than {x!r}"))


def padding_overflow(padding: structs.Padding, length: int) -> None:
    if sum(v for v in padding.values if v > 0) >= length:
        _error(
            ValueError(
                f"padding values ({padding.values!r}) cannot consume entire {length=}"
            )
        )


def padding_fills(padding: structs.Padding) -> None:
    if any(len(v) != 1 for v in padding.fills):
        _error(
            ValueError(
                f"padding fill values ({padding.fills!r}) must be strings of length 1"
            )
        )


def length_one_string(desc: str, value: str) -> None:
    if len(value) != 1:
        _error(ValueError(f"{desc} ({value!r}) must be a string of length 1"))


def _rects_collide(r1: structs.Rect, r2: structs.Rect) -> bool:
    """
    None of the following can be True during a collision:
        r1 left   >= r2 right
        r1 top    >= r2 bottom
        r1 right  <= r2 left
        r1 bottom <= r2 top
    """
    return (
        r1.left < r2.right
        and r1.top < r2.bottom
        and r1.right > r2.left
        and r1.bottom > r2.top
    )


def _rect_contained(rect: structs.Rect, bounds: structs.Rect):
    return (
        rect.left >= bounds.left
        and rect.top >= bounds.top
        and rect.right <= bounds.right
        and rect.bottom <= bounds.bottom
    )


def rects_dont_collide(desc: str, r1: structs.Rect, r2: structs.Rect) -> None:
    if _rects_collide(r1, r2):
        _error(ValueError(f"{desc} collision detected ({r1!r}), ({r2!r})"))


def rect_in_bounds(
    desc: str, rect: structs.Rect, bounds: structs.Rect
) -> None:
    if not _rect_contained(rect, bounds):
        _error(ValueError(f"{desc} not in bounds ({rect=}, {bounds=})"))
