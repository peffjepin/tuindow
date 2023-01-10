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
        "w: save    q: exit    " "i: insert    (h/j/k/l/Arrows): move"
    )

    def __init__(self, filename):
        # panels are not useful until we set their rects
        # but we don't know how large the rects should be at this moment

        self.main_panel = tuindow.Panel(padding=1)
        self.line_number_panel = tuindow.Panel(
            padding=(1, -1), attributes=tuindow.DIM | tuindow.YELLOW
        )
        self.help_panel = tuindow.Panel(padding=-1)

        self.mode = Mode.COMMAND

        self.filename = filename
        self.lines = []
        try:
            self.lines = pathlib.Path(filename).read_text().splitlines()
        except FileNotFoundError:
            pass
        if not self.lines:
            self.lines = [""]

        self.display_offset = 0

    def layout(self, width: int, height: int):
        # the library calls out to us whenever it gets updated information
        # on the screen size. This is where we should assign rects to our panels

        help_panel_height = 3
        editor_top = 1
        editor_height = height - editor_top - help_panel_height

        line_number_width = 5  # 1 padding + 4 supports up to 9999
        editor_width = width - line_number_width

        self.main_panel.rect = (
            line_number_width,
            editor_top,
            editor_width,
            editor_height,
        )
        self.line_number_panel.rect = (
            0,
            editor_top,
            line_number_width,
            editor_height,
        )
        self.help_panel.rect = (
            0,
            editor_top + editor_height,
            width,
            help_panel_height,
        )
        self.help_panel.styleln(
            1,
            attributes=tuindow.STANDOUT | tuindow.BOLD | tuindow.YELLOW,
            padding=-1,
        )
        self.update_help_display()
        self.update_line_numbers()
        self.update_editor_window()

    def update_editor_window(self):
        for i in range(self.main_panel.height):
            line_index = i + self.display_offset
            if line_index < len(self.lines):
                self.main_panel.writeln(i, self.lines[line_index])
            else:
                self.main_panel.clearln(i)

    def update_help_display(self):
        self.help_panel.writeln(2, self.filename)
        if self.mode == Mode.EDIT:
            self.help_panel.writeln(1, "EDIT MODE:   " + self.EDIT_HELP)
        else:
            self.help_panel.writeln(1, "COMMAND MODE:   " + self.COMMAND_HELP)

    def update_line_numbers(self):
        for i in range(self.line_number_panel.height):
            number = i + 1 + self.display_offset
            if number > len(self.lines):
                self.line_number_panel.clearln(i)
            else:
                self.line_number_panel.writeln(i, str(number))

    @property
    def file_line(self) -> int:
        return self.main_panel.cursor.line + self.display_offset

    def sync_cursor_line(self):
        # The cursor writes data directly into the Line buffers which
        # represent screen space. This data will move as the cursor
        # moves and may even be lost as we add more lines to the file.
        #
        # We will have to persist line data on our own aswell.
        # If we call this after all state changes we will stay synced.

        while self.file_line > len(self.lines) - 1:
            self.lines.append("")
        self.lines[self.file_line] = self.main_panel.cursor.data

    def write_from_file_data(self, display_index: int) -> None:
        # Writes a line we have cached away in self.lines back onto the display
        # at the given display index

        line_index = self.display_offset + display_index
        if line_index < len(self.lines):
            self.main_panel.writeln(display_index, self.lines[line_index])
        else:
            self.main_panel.clearln(display_index)

    def up(self) -> None:
        try:
            self.main_panel.cursor.up()
        except tuindow.Overscroll:
            self.handle_overscroll(-1)

    def down(self) -> None:
        try:
            self.main_panel.cursor.down()
        except tuindow.Overscroll:
            self.handle_overscroll(1)

    def handle_overscroll(self, y: int):
        # y < 0 for scroll_up
        # y > 0 for scroll_down

        if y < 0 and self.file_line > 0:
            self.display_offset -= 1
            self.main_panel.shift_down()
            self.write_from_file_data(0)
        elif y > 0:
            self.display_offset += 1
            self.main_panel.shift_up()
            self.write_from_file_data(self.main_panel.height - 1)
        self.update_line_numbers()

    def insert(self, value: str) -> None:
        self.main_panel.cursor.insert(value)
        self.sync_cursor_line()

    def delete(self, n: int = 1) -> str:
        returnval = self.main_panel.cursor.delete(n)
        self.sync_cursor_line()
        return returnval

    def insert_line(self, display_index: int, value: str) -> None:
        self.main_panel.insertln(display_index, value)
        self.lines.insert(self.display_offset + display_index, value)

    def delete_cursor_line(self) -> None:
        self.main_panel.deleteln(self.main_panel.cursor.line)
        del self.lines[self.file_line]

    def backspace(self) -> None:
        if self.main_panel.cursor.index > 0:
            self.main_panel.cursor.backspace()
            self.sync_cursor_line()
            return
        elif self.file_line == 0:
            return

        # following is the case when backspace is pressed at
        # the very beginning of the line and we should wrap up

        # delete line and shift data
        trailing_line = self.main_panel.cursor.consume_line()
        self.delete_cursor_line()

        # if the file extends beyond the screen then we have to fill
        # in the bottom line that is opened up from previous deletion
        self.write_from_file_data(self.main_panel.height - 1)

        # paste remainder to end of previous line (remembering the proper index)
        self.up()
        self.main_panel.cursor.index = -1
        index = self.main_panel.cursor.index
        self.insert(trailing_line)
        self.main_panel.cursor.index = index

    def enter(self):
        remainder_of_line = self.delete(-1)
        self.insert_line(self.main_panel.cursor.line + 1, remainder_of_line)
        self.down()
        self.main_panel.cursor.index = 0

    def handle_key(self, key: str):
        if self.mode == Mode.EDIT:
            if key == tuindow.LEFT:
                self.main_panel.cursor.left()

            elif key == tuindow.RIGHT:
                self.main_panel.cursor.right()

            elif key == tuindow.UP:
                if self.file_line == 0:
                    return
                self.up()

            elif key == tuindow.DOWN:
                if self.file_line == len(self.lines) - 1:
                    return
                self.down()

            elif key == tuindow.ESCAPE:
                self.mode = Mode.COMMAND
                self.update_help_display()

            elif key == tuindow.DELETE:
                # wont delete past endline with this implementation
                # see backspace or newline for example of how to handle this
                self.delete()

            elif key == tuindow.BACKSPACE:
                self.backspace()
                self.update_line_numbers()

            elif key == "\n":
                self.enter()
                self.update_line_numbers()

            elif key == "\t":
                self.insert("    ")

            elif key in tuindow.PRINTABLE:
                # don't assume remaining unhandled keys will be printable...
                # special keys are represented by multicharacter strings
                self.insert(key)

        elif self.mode == Mode.COMMAND:
            if key == tuindow.LEFT or key == "h":
                self.main_panel.cursor.left()

            elif key == tuindow.RIGHT or key == "l":
                self.main_panel.cursor.right()

            elif key == tuindow.UP or key == "k":
                self.up()

            elif key == tuindow.DOWN or key == "j":
                if len(self.lines) == self.file_line + 1:
                    return
                self.down()

            elif key == "w":
                pathlib.Path(self.filename).write_text("\n".join(self.lines))

            elif key == "q":
                exit(0)

            elif key == "i":
                self.mode = Mode.EDIT
                self.update_help_display()

            elif key == "a":
                self.mode = Mode.EDIT
                self.main_panel.cursor.index += 1
                self.update_help_display()

            elif key == "A":
                self.mode = Mode.EDIT
                self.main_panel.cursor.index = -1
                self.update_help_display()

            elif key == "x":
                self.delete()


parser = argparse.ArgumentParser()
parser.add_argument("filename")
args = parser.parse_args()
editor = Editor(args.filename)

with tuindow.init(editor.layout):
    while 1:
        tuindow.set_active_cursor(editor.main_panel.cursor)

        for key in tuindow.keys():
            editor.handle_key(key)

        tuindow.draw(
            editor.main_panel, editor.line_number_panel, editor.help_panel
        )
        tuindow.update()
