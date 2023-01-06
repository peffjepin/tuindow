from .conftest import params

from tuindow import WindowError, Panel
from tuindow import Window as LibraryWindow

TEST_WIDTH = 10
TEST_HEIGHT = 10


class Window(LibraryWindow):
    @property
    def width(self):
        return TEST_WIDTH

    @property
    def height(self):
        return TEST_HEIGHT

    def _init_curses(self, *args, **kwargs):
        pass

    def _cleanup_curses(self, *args, **kwargs):
        pass


@params(
    "args",
    (1, 1, 1, 1),
    (0, 0, TEST_WIDTH, TEST_HEIGHT),
)
def test_making_panel_with_window(args):
    p1 = Panel(*args)

    window = Window()
    p2 = window.panel(*args)

    assert p1.left == p2.left
    assert p1.top == p2.top
    assert p1.width == p2.width
    assert p1.height == p2.height


@params(
    "args",
    (0, 0, TEST_WIDTH + 1, 1),
    (0, 0, 1, TEST_HEIGHT+1),
    (0, 0, TEST_WIDTH+1, TEST_HEIGHT+1),
    (TEST_WIDTH-1, TEST_HEIGHT-1, 2, 2)
)
def test_out_of_bounds_panel(args, expect_error):
    with expect_error(WindowError, "panel", "bounds"):
        window = Window()
        window.panel(*args)


def test_mutually_exclusive_user_panels_and_default_panel(expect_error):
    with expect_error(WindowError, "panel", "default_panel", "mutually exclusive"):
        window = Window()
        window.panel(0, 0, 1, 1)
        window.default_panel

    with expect_error(WindowError, "panel", "default_panel", "mutually exclusive"):
        window = Window()
        window.default_panel
        window.panel(0, 0, 1, 1)


@params(
    "args",
    (1, 1, 3, 3),                          # top left corner
    (1, TEST_HEIGHT-5, 3, 3),              # bottom left corner
    (TEST_WIDTH-5, 1, 3, 3,),              # top right corner
    (TEST_WIDTH-5, TEST_HEIGHT-5, 3, 3),   # bottom right corner
    (0, TEST_HEIGHT//2, 5, 1),             # left edge
    (TEST_WIDTH//2, 0, 1, 5),              # top edge
    (TEST_WIDTH//2, TEST_HEIGHT-5, 1, 3),  # bottom edge
    (TEST_WIDTH-5, TEST_HEIGHT//2, 3, 1),  # right edge
)
def test_error_when_creating_colliding_panels(expect_error, args):
    window = Window()
    # panel 3 away from any edge
    p1_args = (3, 3, TEST_WIDTH-6, TEST_HEIGHT-6)
    window.panel(*p1_args)

    with expect_error(WindowError, "collision", *map(str, p1_args), *map(str, args)):
        window.panel(*args)


def test_collision_with_many_panels_in_window(expect_error):
    window = Window()

    collide_args1 = (3, 3, 3, 3)
    collide_args2 = (4, 4, 4, 4)

    window.panel(0, 0, 1, 1)
    window.panel(*collide_args1)  # this one will collide
    window.panel(1, 1, 1, 1)
    window.panel(2, 2, 1, 1)

    with expect_error(WindowError, "collision", *map(str, collide_args1), *map(str, collide_args2)):
        window.panel(*collide_args2)


def test_default_panel_covers_whole_window():
    window = Window()
    assert window.default_panel.left == 0
    assert window.default_panel.top == 0
    assert window.default_panel.width == window.width
    assert window.default_panel.height == window.height
