#!/usr/bin/env python3

import tuindow


class Window(tuindow.Window):
    def __init__(self):
        super().__init__()
        self.left_panel = self.panel(0, 0, self.width // 2, self.height)
        self.right_panel = self.panel(
            self.width // 2, 0, self.width // 2, self.height
        )

    def layout(self):
        self.left_panel.rect = (0, 0, self.width // 2, self.height)
        self.right_panel.rect = (
            self.width // 2,
            0,
            self.width // 2,
            self.height,
        )


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
        window.left_panel.styleline(0, padding=2)

        while 1:
            window.update()

            window.left_panel.writeline(0, str(user_input))

            for key in window.keys:
                if key == tuindow.ESCAPE:
                    return 0
                elif key == "\n":
                    index = window.right_panel.first_available
                    if index is not None:
                        window.right_panel.styleline(index, padding=2)
                        window.right_panel.writeline(
                            index, user_input.consume())
                elif key == tuindow.BACKSPACE:
                    user_input.backspace()
                else:
                    user_input.append(key)


if __name__ == "__main__":
    raise SystemExit(main())
