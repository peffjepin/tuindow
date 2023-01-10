# tuindow -- A small package for creating TUI applications

## Requirements

Tested on python versions 3.8 - 3.11

This package makes use of the builtin curses module, so it's only available on Linux.
I will probably look into testing and supporting Windows in the future. I do not have a
macOS device to test on and so won't be supporting the OS.

## Installation

```sh
python3 -m pip install tuindow
```

## Basic Usage

```py
import tuindow

panel = tuindow.Panel()


def layout(width: int, height: int) -> None:
    panel.rect = (0, 0, width, height)


with tuindow.init(layout):
    tuindow.set_active_cursor(panel.cursor)

    while 1:
        for key in tuindow.keys():
            if key == tuindow.DOWN or key == "\n":
                try:
                    panel.cursor.down()
                except tuindow.Overscroll:
                    pass

            elif key == tuindow.UP or (
                panel.cursor.index == 0 and key == tuindow.BACKSPACE
            ):
                try:
                    panel.cursor.up()
                except tuindow.Overscroll:
                    pass

            elif key == tuindow.RIGHT:
                panel.cursor.right()

            elif key == tuindow.LEFT:
                panel.cursor.left()

            elif key == tuindow.ESCAPE:
                exit(0)

            elif key == tuindow.BACKSPACE:
                panel.cursor.backspace()

            elif key == tuindow.DELETE:
                panel.cursor.delete()

            elif key in tuindow.PRINTABLE:
                panel.cursor.insert(key)

        tuindow.draw(panel)
        tuindow.update()
```

## A More Advanced Example

This will create the code for a simple text editor in the current working directory and open the file using the editor itself.
In the future there may be more examples available using this method.

```sh
python3 -m tuindow
```

## More Documentation

The source code is documented fairly thoroughly.

For more documentation refer to the source code or get it interactively for specific objects using the python `help` builtin at an interactive prompt.
