# Sets the working director to be the src
import os
import sys

here = os.path.dirname(__file__)
dir_path = os.path.join(os.path.dirname(here), "src")
os.chdir(dir_path)
sys.path.append(dir_path)

from file_system.utils import in_working
from grading.utils import run_annotate_ui

if __name__ in {"__main__", "__mp_main__"}:
    folder = sys.argv[1]
    if not folder.startswith("/"):
        folder = in_working(folder)
    run_annotate_ui(folder)
