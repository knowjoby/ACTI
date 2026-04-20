"""
State persistence. Pickle for the Markov tables (they're just nested
dicts/Counters), JSON for scalar metadata. Written to ./state/ next to
main.py.
"""

import json
import os
import pickle


def save(entity, path):
    os.makedirs(path, exist_ok=True)
    tmp = os.path.join(path, "markov.pkl.tmp")
    final = os.path.join(path, "markov.pkl")
    with open(tmp, "wb") as f:
        pickle.dump(
            {
                "ctx": entity.markov.ctx,
                "ema": entity.markov.surprise_ema,
                "max_order": entity.markov.max_order,
            },
            f,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    os.replace(tmp, final)

    with open(os.path.join(path, "meta.json"), "w") as f:
        json.dump(
            {
                "total_chars": entity.total_chars,
                "tick_count": entity.tick_count,
                "copy_inhibition": entity.copy_inhibition,
                "dream_cycles": entity.dreamer.cycles,
            },
            f,
            indent=2,
        )


def load(entity, path):
    try:
        with open(os.path.join(path, "markov.pkl"), "rb") as f:
            d = pickle.load(f)
        entity.markov.ctx = d["ctx"]
        entity.markov.surprise_ema = d["ema"]
        with open(os.path.join(path, "meta.json")) as f:
            m = json.load(f)
        entity.total_chars = m.get("total_chars", 0)
        entity.tick_count = m.get("tick_count", 0)
        entity.copy_inhibition = m.get("copy_inhibition", 0.0)
        entity.dreamer.cycles = m.get("dream_cycles", 0)
        return True
    except (FileNotFoundError, EOFError):
        return False
