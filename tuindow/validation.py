"""
This module is used internally for validation
"""

import contextlib

from typing import List
from typing import Iterator
from typing import Type
from typing import Union

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


def not_negative(desc: str, value: Union[int, float]) -> None:
    if value < 0:
        _error(ValueError(f"{desc} ({value!r}) cannot be negative"))


def greater_than_x(
    desc: str, value: Union[int, float], x: Union[int, float]
) -> None:
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
