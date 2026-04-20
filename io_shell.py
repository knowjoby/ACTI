"""
Terminal I/O. Entity output is cyan. Status lines are dim.
"""

import sys

CYAN = "\033[36m"
DIM = "\033[2m"
RESET = "\033[0m"


def entity_say(s):
    if not s:
        return
    sys.stdout.write(CYAN + s + RESET)
    sys.stdout.flush()


def status(s):
    sys.stderr.write(DIM + s + RESET + "\n")
    sys.stderr.flush()


def status_inline(s):
    sys.stderr.write(DIM + s + RESET)
    sys.stderr.flush()
