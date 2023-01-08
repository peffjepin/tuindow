#!/usr/bin/env python3

import tuindow


left_panel = tuindow.Panel(padding=-1)
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
    while 1:
        cursor = left_panel.cursor
        cursor.set_active()
        for key in tuindow.keys():
            if key == tuindow.ESCAPE:
                exit(0)
            elif key == "\n":
                right_panel.write_if_available(cursor.consume())
            elif key == tuindow.BACKSPACE:
                cursor.backspace()
            elif key == tuindow.RIGHT:
                cursor.right()
            elif key == tuindow.LEFT:
                cursor.left()
            elif key == tuindow.DELETE:
                cursor.delete()
            else:
                cursor.insert(key)

        tuindow.draw(left_panel, right_panel)
        tuindow.update()
