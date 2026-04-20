"""
Variable-order Markov model over the raw character stream.

No tokenization. No words. Just: for every observed context of length 0..K,
keep counts of what character followed it. Predict the next character by
blending counts from the longest matching context down to uniform (PPM-C-like
escape). Surprise is -log2 P(c | context).

This is the entity's only "semantic memory": a compressed statistical shadow
of its own history.
"""

import math
from collections import Counter, defaultdict

LOG2 = math.log(2)


class VariableOrderMarkov:
    def __init__(self, max_order=8, alphabet_size=256):
        self.max_order = max_order
        self.V = alphabet_size
        # ctx[order] : dict[context_suffix_str -> Counter(next_char -> count)]
        self.ctx = [dict() for _ in range(max_order + 1)]
        # Exponential moving average of surprise at each (order, context).
        # Used for habituation: contexts the entity has "seen enough of".
        self.surprise_ema = [dict() for _ in range(max_order + 1)]
        self.ema_alpha = 0.08
        self._floor = 1.0 / alphabet_size  # implicit uniform floor

    def _suffix(self, context, order):
        return context[-order:] if order > 0 else ""

    def longest_seen(self, context):
        """Return (order, suffix) of the longest context we've seen before."""
        for k in range(min(self.max_order, len(context)), -1, -1):
            sub = self._suffix(context, k)
            if sub in self.ctx[k]:
                return k, sub
        return 0, ""

    def predict(self, context):
        """
        PPM-C-like prediction with exclusion-free escape. Returns
        (probs_dict, floor) where probs_dict[c] is the probability assigned
        to characters seen from this context (at whichever order contributed),
        and `floor` is the per-character probability for unseen chars.
        """
        probs = defaultdict(float)
        remaining = 1.0
        for order in range(min(self.max_order, len(context)), -1, -1):
            sub = self._suffix(context, order)
            table = self.ctx[order].get(sub)
            if not table:
                continue
            total = sum(table.values())
            distinct = len(table)
            # escape mass proportional to novelty rate at this order
            escape = distinct / (total + distinct)
            local = remaining * (1.0 - escape)
            for c, n in table.items():
                probs[c] += local * (n / total)
            remaining *= escape
            if remaining < 1e-9:
                break
        floor = remaining / self.V
        return probs, floor

    def surprise(self, context, c):
        probs, floor = self.predict(context)
        p = probs.get(c, 0.0) + floor
        if p <= 0:
            p = 1e-12
        return -math.log(p) / LOG2  # bits

    def update(self, context, c, weight=1.0):
        """Increment counts at all orders for which we have enough context."""
        for order in range(self.max_order + 1):
            if len(context) < order:
                continue
            sub = self._suffix(context, order)
            table = self.ctx[order].get(sub)
            if table is None:
                table = Counter()
                self.ctx[order][sub] = table
            table[c] += weight

    def update_habituation(self, context, surprise_bits):
        order, sub = self.longest_seen(context)
        tbl = self.surprise_ema[order]
        prev = tbl.get(sub, surprise_bits)
        tbl[sub] = prev * (1 - self.ema_alpha) + surprise_bits * self.ema_alpha

    def habituation(self, context):
        order, sub = self.longest_seen(context)
        return self.surprise_ema[order].get(sub)

    def size(self):
        return sum(len(t) for t in self.ctx)
