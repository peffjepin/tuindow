#!/usr/bin/env python3

import tuindow


def main():
    with tuindow.Window() as window:
        window.default_panel.lines[1].data = "tuindow -- hello, world"
        print_key_line = window.default_panel.lines[2]
        while 1:
            window.draw()
            for key in window.keys:
                if key == "q":
                    return 0
                else:
                    print_key_line.data = key
            window.tick()


if __name__ == "__main__":
    raise SystemExit(main())
