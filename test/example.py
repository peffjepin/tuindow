#!/usr/bin/env python3

import tuindow
import enum
import argparse
import pathlib


class Mode(enum.Enum):
    EDIT = enum.auto()
    COMMAND = enum.auto()


class Editor:
    EDIT_HELP = "move cursor: (Left/Right/Up/Down)    command mode: (Esc)"
    COMMAND_HELP = (
        "w: save & exit    q: exit w/o saving    "
        "i: insert text    move cursor: (h/j/k/l/Arrows)"
    )

    def __init__(self, filename):
        # panels are not useful until we set their rects
        # but we don't know how large the rects should be at this moment
        self.main_panel = tuindow.Panel(padding=1)
        self.line_number_panel = tuindow.Panel(padding=(1, -1))
        self.help_panel = tuindow.Panel(padding=-1)

        self.mode = Mode.COMMAND

        self.filename = filename
        self.lines = []
        try:
            self.lines = pathlib.Path(
                filename).read_text().splitlines()
        except FileNotFoundError:
            pass
        if not self.lines:
            self.lines = [""]

        self.cursor = self.main_panel.cursor
        self.offset = 0

    def layout(self, width: int, height: int):
        # the library calls out to us whenever it gets updated information
        # on the screen size. This is where we should assign rects to our panels

        help_panel_height = 3
        editor_top = 1
        editor_height = height - editor_top - help_panel_height

        line_number_width = 5  # 1 padding + 4 supports up to 9999
        editor_width = width - line_number_width

        self.main_panel.set_rect(
            line_number_width, editor_top, editor_width, editor_height
        )
        self.line_number_panel.set_rect(
            0, editor_top, line_number_width, editor_height
        )
        self.help_panel.set_rect(
            0, editor_top + editor_height, width, help_panel_height
        )

        self.update_help_display()
        self.update_line_numbers()
        self.update_editor_window()

    def update_editor_window(self):
        for i in range(self.main_panel.height):
            line_index = i + self.offset
            if line_index < len(self.lines):
                self.main_panel.writeline(i, self.lines[line_index])
            else:
                self.main_panel.clearline(i)

    def update_help_display(self):
        if self.mode == Mode.EDIT:
            self.help_panel.writeline(1, self.EDIT_HELP)
        else:
            self.help_panel.writeline(1, self.COMMAND_HELP)

    def update_line_numbers(self):
        for i in range(self.line_number_panel.height):
            number = i + 1 + self.offset
            if number > len(self.lines):
                self.line_number_panel.clearline(i)
            else:
                self.line_number_panel.writeline(i, str(number))

    @property
    def absolute_line(self) -> int:
        return self.cursor.line + self.offset

    def sync_cursor_line(self):
        # the cursor writes data directly into the line buffers.
        # we will need to extract that data into our own data structure
        # if we want to persist it
        difference = self.absolute_line - len(self.lines) - 1
        if difference > 0:
            self.lines.extend([""] * difference)
        self.lines[self.absolute_line] = self.main_panel.readline(
            self.cursor.line
        )

    def handle_overscroll(self, y: int):
        # y < 0 for scroll_up
        # y > 0 for scroll_down
        if y < 0 and self.absolute_line > 0:
            self.offset -= 1
            self.main_panel.shift_down()
            self.write_cached_line(0)
        elif y > 0:
            self.offset += 1
            self.main_panel.shift_up()
            self.write_cached_line(self.main_panel.height - 1)

    def handle_newline(self):
        # delete the data remaining after the cursor and update
        # the cursor line to reflect the change in our own list
        # before we move away from the line
        remainder_of_line = self.cursor.delete(-1)
        self.sync_cursor_line()

        # since we are inserting a new line we need to shift all of
        # the lines below the cursor down by one
        for i in reversed(range(self.cursor.line + 2, self.main_panel.height)):
            self.main_panel.writeline(i, self.main_panel.readline(i - 1))

        # we can reflect the change in our own data structure with an insert
        self.lines.insert(self.absolute_line+1, remainder_of_line)

        # update cursor
        try:
            self.cursor.down()
        except tuindow.Overscroll:
            self.handle_overscroll(1)
        self.cursor.index = 0

        # finally write in the remainder of the line we clipped off
        self.main_panel.writeline(self.cursor.line, remainder_of_line)

    def handle_backspace(self):
        if self.cursor.index > 0:
            self.cursor.backspace()
            return
        elif self.absolute_line == 0:
            return

        # delete line and shift data
        remainder = self.cursor.consume()
        del self.lines[self.absolute_line]
        for i in range(self.cursor.line, self.main_panel.height - 1):
            self.main_panel.writeline(i, self.main_panel.readline(i + 1))

        # if the file is longer than the screen we have to fill in the bottom line
        if self.offset + self.main_panel.height <= len(self.lines):
            self.write_cached_line(self.main_panel.height - 1)
        else:
            self.main_panel.clearline(self.main_panel.height-1)

        # paste remainder to end of previous line (remembering the proper index)
        try:
            self.cursor.up()
        except tuindow.Overscroll:
            self.handle_overscroll(-1)
        self.cursor.index = -1
        index = self.cursor.index
        self.cursor.insert(remainder)
        self.cursor.index = index

        # make sure to sync up our line list
        self.sync_cursor_line()

    def write_cached_line(self, index):
        # write a line from our line cache into the main panel at the given index
        self.main_panel.writeline(index, self.lines[self.offset + index])

    def handle_key(self, key: str):
        if self.mode == Mode.EDIT:
            if key == tuindow.LEFT:
                self.cursor.left()

            elif key == tuindow.RIGHT:
                self.cursor.right()

            elif key == tuindow.UP:
                if self.absolute_line == 0:
                    return
                self.sync_cursor_line()
                try:
                    self.cursor.up()
                except tuindow.Overscroll:
                    self.handle_overscroll(-1)
                self.update_line_numbers()

            elif key == tuindow.DOWN:
                if self.absolute_line == len(self.lines) - 1:
                    return
                self.sync_cursor_line()
                try:
                    self.cursor.down()
                except tuindow.Overscroll:
                    self.handle_overscroll(1)
                self.update_line_numbers()

            elif key == tuindow.ESCAPE:
                self.mode = Mode.COMMAND
                self.sync_cursor_line()
                self.update_help_display()

            elif key == tuindow.DELETE:
                # wont delete past endline with this implementation
                # see backspace or newline for example of how to handle this
                self.cursor.delete()

            elif key == tuindow.BACKSPACE:
                self.handle_backspace()
                self.update_line_numbers()

            elif key == "\n":
                self.handle_newline()
                self.update_line_numbers()

            elif key == "\t":
                self.cursor.insert("    ")
                self.sync_cursor_line()

            elif key in tuindow.PRINTABLE:
                # don't assume remaining unhandled keys will be printable...
                # special keys are represented by multicharacter strings
                self.cursor.insert(key)
                self.sync_cursor_line()

        elif self.mode == Mode.COMMAND:
            if key == tuindow.LEFT or key == "h":
                self.cursor.left()

            elif key == tuindow.RIGHT or key == "l":
                self.cursor.right()

            elif key == tuindow.UP or key == "k":
                try:
                    self.cursor.up()
                except tuindow.Overscroll:
                    self.handle_overscroll(-1)
                self.update_line_numbers()

            elif key == tuindow.DOWN or key == "j":
                if len(self.lines) == self.absolute_line + 1:
                    return
                try:
                    self.cursor.down()
                except tuindow.Overscroll:
                    self.handle_overscroll(1)
                self.update_line_numbers()

            elif key == "w":
                pathlib.Path(self.filename).write_text("\n".join(self.lines))
                exit(0)

            elif key == "q":
                exit(0)

            elif key == "i":
                self.mode = Mode.EDIT
                self.update_help_display()

            elif key == "a":
                self.mode = Mode.EDIT
                self.cursor.index += 1
                self.update_help_display()

            elif key == "A":
                self.mode = Mode.EDIT
                self.cursor.index = -1
                self.update_help_display()

            elif key == "x":
                self.cursor.delete()
                self.sync_cursor_line()


parser = argparse.ArgumentParser()
parser.add_argument("filename")
args = parser.parse_args()
editor = Editor(args.filename)

with tuindow.init(editor.layout):
    while 1:
        editor.main_panel.cursor.set_active()

        for key in tuindow.keys():
            editor.handle_key(key)

        tuindow.draw(
            editor.main_panel, editor.line_number_panel, editor.help_panel
        )
        tuindow.update()
