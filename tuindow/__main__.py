"""
In the future this script could host many different examples,
for now it's just the one.
"""


import pathlib
import shutil
import subprocess
import sys


if __name__ == "__main__":
    simple_editor_script = (
        pathlib.Path(__file__).parent / "examples/simple_editor.py"
    )
    output_path = pathlib.Path.cwd() / "tuindow_simple_editor.py"
    backup_output_path = pathlib.Path.cwd() / "tuindow_simple_editor.py.old"
    if output_path.exists():
        shutil.move(str(output_path), str(backup_output_path))
    output_path.write_text(
        "# This file is a simple text editor written with the tuindow library\n\n"
        "# You are viewing this file with itself\n\n"
        "# See controls at the bottom of the window\n\n\n"
        + simple_editor_script.read_text()
    )
    subprocess.run([sys.executable, str(output_path), str(output_path)])
