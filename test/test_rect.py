from .conftest import params

from tuindow.structs import Rect


@params(
    "rect_args,expected",
    ((-1, -1, 2, 2), True),
    ((1, -1, 1, 2), True),
    ((2, -1, 2, 2), True),
    ((2, 1, 2, 1), True),
    ((2, 2, 2, 2), True),
    ((1, 2, 1, 2), True),
    ((-1, 2, 2, 2), True),
    ((-1, 1, 2, 1), True),
    ((-2, -2, 2, 2), False),
    ((1, -2, 1, 2), False),
    ((3, -2, 2, 2), False),
    ((3, 1, 2, 1), False),
    ((3, 3, 2, 2), False),
    ((1, 3, 1, 2), False),
    ((-2, 3, 2, 2), False),
    ((-2, 1, 2, 1), False),
)
def test_rect_edge_intersections(rect_args, expected):
    base = Rect(0, 0, 3, 3)
    assert base.intersects(Rect(*rect_args)) is expected


@params("left", 0, 1, 2)
@params("top", 0, 1, 2)
def test_rect_contained_intersections(left, top):
    base = Rect(0, 0, 3, 3)
    assert base.intersects(Rect(left, top, 1, 1))


def test_identical_rect_collision():
    assert Rect(1, 2, 3, 4).intersects(Rect(1, 2, 3, 4))


@params("left", *range(-1, 3))
@params("top", *range(-1, 3))
def test_rect_contains(left, top):
    base = Rect(0, 0, 3, 3)
    expected = 0 <= left < 2 and 0 <= top < 2

    assert base.contains(Rect(left, top, 2, 2)) is expected


def test_rect_contains_full_overlap():
    assert Rect(0, 0, 2, 2).contains(Rect(0, 0, 2, 2))
