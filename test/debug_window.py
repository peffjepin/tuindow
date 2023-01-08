#!/usr/bin/env python3

import tuindow


left_panel = tuindow.Panel(padding=2)
right_panel = tuindow.Panel(padding=2, fill=".")


def layout(width: int, height: int):
    left_panel.set_rect(0, 0, width // 2, height)
    right_panel.set_rect(
        width // 2,
        0,
        width // 2,
        height,
    )


with tuindow.init(layout):
    user_input = ""

    while 1:
        left_panel.writeline(0, user_input)

        for key in tuindow.keys():
            if key == tuindow.ESCAPE:
                exit(0)
            elif key == "\n":
                right_panel.write_if_available(user_input)
                user_input = ""
            elif key == tuindow.BACKSPACE:
                if user_input:
                    user_input = user_input[:-1]
            else:
                user_input += key

        tuindow.draw(left_panel, right_panel)
        tuindow.update()
