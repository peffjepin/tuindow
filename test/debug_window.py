#!/usr/bin/env python3

import tuindow


class Window(tuindow.Window):
    def __init__(self):
        super().__init__()
        self.left_panel = self.panel(0, 0, self.width//2, self.height)
        self.right_panel = self.panel(
            self.width//2, 0, self.width//2, self.height)

    def layout(self):
        self.left_panel.height = self.height
        self.left_panel.width = self.width//2

        self.right_panel.x = self.width//2
        self.right_panel.width = self.width//2
        self.right_panel.height = self.height


class UserInput:
    def __init__(self):
        self.data = []
        self.dirty = True

    def __str__(self):
        return "".join(self.data)

    def append(self, c):
        self.dirty = True
        self.data.append(c)

    def backspace(self):
        if self.data:
            self.data.pop(-1)
        self.dirty = True

    def consume(self):
        v = str(self)
        self.dirty = True
        self.data.clear()
        return v


def main():
    with Window() as window:
        user_input = UserInput()
        lines = 0

        input_line = window.left_panel.lines[0]
        input_line.data = user_input
        input_line.padding = 2

        while 1:
            window.draw()

            for key in window.keys:
                if key == tuindow.ESCAPE:
                    return 0
                elif key == "\n":
                    window.right_panel.lines[lines].data = user_input.consume()
                    lines += 1
                elif key == tuindow.BACKSPACE:
                    user_input.backspace()
                else:
                    user_input.append(key)

            window.tick()


if __name__ == "__main__":
    raise SystemExit(main())
