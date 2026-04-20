"""
Entry point. Reads your line, feeds it character-by-character into the
entity, then gives the entity a short window of idle ticks to do whatever
it wants (emit, ruminate, or stay silent) before asking for your next line.

Ctrl+C or EOF puts it to sleep cleanly.
"""

import os
import random
import re
import signal
import sys
import time

from entity import Entity
from io_shell import CYAN, DIM, RESET, entity_say, status

REWARD_LINE = re.compile(r"^\s*(GOOD|BAD)\s*$")

STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
SAVE_EVERY_SECONDS = 300
IDLE_BUDGET = 24           # max internal ticks between your lines
MAX_OUTPUT_PER_TURN = 8    # hard cap on chars it can emit per your line


def _banner(e):
    status("")
    status("  inner world — an entity that begins empty.")
    status("  it has no language. teach it or not. type GOOD or BAD to reward.")
    status(f"  memory: {e.markov.size()} contexts   experience: {e.total_chars} chars")
    status("  ctrl-c to let it sleep.")
    status("")


def main():
    e = Entity()
    loaded = False
    try:
        from persistence import load, save
        loaded = load(e, STATE_DIR)
    except Exception as ex:
        status(f"[could not load prior state: {ex}]")
    _banner(e)
    if not loaded:
        status("[first waking.]")

    last_save = time.time()

    def _sleep_and_exit(*_):
        try:
            from persistence import save
            save(e, STATE_DIR)
            status("\n[sleeping.]")
        except Exception as ex:
            status(f"\n[save failed: {ex}]")
        sys.exit(0)

    signal.signal(signal.SIGINT, _sleep_and_exit)

    try:
        while True:
            try:
                line = input()
            except EOFError:
                break

            # Reward-only lines don't enter perception. They're an
            # out-of-band signal that reaches episodic memory as a scalar,
            # but the entity never sees the bytes GOOD / BAD.
            m = REWARD_LINE.match(line)
            if m:
                r = +1.0 if m.group(1) == "GOOD" else -1.0
                e.reward(r)
                status(f"  [reward {r:+.1f} diffused into recent memory]")
                continue

            # feed the user's line, character by character
            for c in line + "\n":
                e.perceive(c, source="user")
                # rare mid-line reaction on large surprise spikes
                if e.last_surprise > 5.5 and random.random() < 0.04:
                    out = e.consider_output()
                    if out:
                        entity_say(out)
                        e.perceive(out, source="self")

            # give it idle time to think / maybe speak
            emitted = 0
            for _ in range(IDLE_BUDGET):
                if emitted >= MAX_OUTPUT_PER_TURN:
                    break
                out = e.idle_tick()
                if out is None:
                    continue
                entity_say(out)
                e.perceive(out, source="self")
                emitted += 1

            if emitted > 0:
                sys.stdout.write("\n")
                sys.stdout.flush()

            sys.stderr.write(
                f"{DIM}  [surprise={e.last_surprise:.2f} bits   "
                f"mem={e.markov.size()}   "
                f"chars={e.total_chars}   "
                f"dreams={e.dreamer.cycles}   "
                f"inh={e.copy_inhibition:.2f}]{RESET}\n"
            )
            sys.stderr.flush()

            if time.time() - last_save > SAVE_EVERY_SECONDS:
                from persistence import save
                save(e, STATE_DIR)
                last_save = time.time()
    finally:
        from persistence import save
        save(e, STATE_DIR)


if __name__ == "__main__":
    main()
