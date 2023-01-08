from tuindow.structs import Rect
from tuindow.window import Window
from tuindow.window import BoundsError


def test_should_draw_rect_that_has_never_been_drawn():
    window = Window(0, 0, 10, 10)
    assert window.draw(Rect(0, 0, 10, 10))


def test_should_not_draw_same_rect_twice_if_nothing_has_changed():
    window = Window(0, 0, 10, 10)
    rect = Rect(0, 0, 10, 10)

    assert window.draw(rect)
    assert not window.draw(rect)


def test_should_draw_if_another_rect_dirties_area():
    window = Window(0, 0, 10, 10)
    rect1 = Rect(0, 0, 10, 10)
    rect2 = Rect(0, 0, 10, 10)

    assert window.draw(rect1)
    assert window.draw(rect2)

    assert window.draw(rect1)
    assert window.draw(rect2)


def test_non_colliding_rects_dont_interfere_with_one_another():
    window = Window(0, 0, 10, 10)
    rect1 = Rect(0, 0, 5, 10)
    rect2 = Rect(5, 0, 5, 10)

    assert window.draw(rect1)
    assert window.draw(rect2)

    assert not window.draw(rect1)
    assert not window.draw(rect2)


def test_all_intersecting_rects_get_invalidated():
    window = Window(0, 0, 10, 10)
    rect1 = Rect(0, 0, 5, 10)
    rect2 = Rect(5, 0, 5, 10)
    rect3 = Rect(0, 0, 10, 10)

    assert window.draw(rect1)
    assert window.draw(rect2)
    assert window.draw(rect3)

    assert window.draw(rect1)
    assert window.draw(rect2)
    assert window.draw(rect3)


def test_rects_invalidated_by_resize():
    window = Window(0, 0, 10, 10)
    rect1 = Rect(0, 0, 5, 10)
    rect2 = Rect(5, 0, 5, 10)

    assert window.draw(rect1)
    assert window.draw(rect2)

    window.resize(0, 0, 20, 20)

    assert window.draw(rect1)
    assert window.draw(rect2)


def test_out_of_bounds_rect_raises_error(expect_error):
    rect = Rect(1, 1, 5, 5)
    window = Window(0, 0, 5, 5)

    with expect_error(BoundsError, repr(rect), repr(window)):
        window.draw(rect)
