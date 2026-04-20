"""
Solo mode.

The entity speaks to itself. No user input. Its own output becomes its
next perception, which reshapes its expectations, which shapes the next
output. Closed loop.

Loads existing state (otherwise there is nothing for it to think with).
Prints each emitted character in cyan, soft-wrapping at column 80.
Ctrl+C stops it and saves.

No metrics, no status — just the stream. Watch what happens.
"""

import os
import random
import signal
import sys
import time

from entity import Entity
from io_shell import DIM, RESET, entity_say, status
from persistence import load, save

STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")

TICK_DELAY = 0.08          # seconds between characters (readable pace)
DREAM_EVERY = 500
SELF_WEIGHT_SOLO = 0.4     # higher than interactive; self IS the signal
WRAP_AT = 80


def _force_emit(e):
    """Ask for an output; if the entity stays silent, force a sample from
    its Markov model so the stream never stops. Newlines are replaced with
    spaces so the output reads as one continuous murmur."""
    out = e.consider_output()
    if not out:
        probs, floor = e.markov.predict(e.working)
        if probs:
            total = sum(probs.values())
            if total > 0:
                r = random.random() * total
                acc = 0.0
                for c, p in probs.items():
                    acc += p
                    if acc >= r:
                        out = c
                        break
    if not out:
        out = " "
    if out in ("\n", "\r"):
        out = " "
    return out


def main():
    e = Entity()
    loaded = load(e, STATE_DIR)
    if not loaded:
        status("[empty state. it has nothing of its own to say.]")
        status("[run main.py first and give it some experience, then come back.]")
        return

    status(f"[loaded: {e.total_chars} chars of past experience]")
    status("[solo. it speaks only to itself. ctrl-c to stop.]")
    status("")

    def _exit(*_):
        try:
            save(e, STATE_DIR)
        finally:
            sys.stderr.write("\n" + DIM + "[sleeping.]" + RESET + "\n")
            sys.exit(0)

    signal.signal(signal.SIGINT, _exit)

    col = 0
    try:
        while True:
            out = _force_emit(e)
            entity_say(out)
            # Perceive own output at elevated weight so solo learning
            # actually reshapes the model.
            e.perceive(out, source="self", weight=SELF_WEIGHT_SOLO)

            col += 1
            if col >= WRAP_AT:
                sys.stdout.write("\n")
                sys.stdout.flush()
                col = 0

            time.sleep(TICK_DELAY)
    finally:
        save(e, STATE_DIR)


if __name__ == "__main__":
    main()
