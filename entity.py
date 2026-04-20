"""
The entity.

All three memories live here:
    - working memory   : the last WORKING_CAP chars of its stream (user + self)
    - episodic memory  : every perceived char as an Episode
    - semantic memory  : the Markov counts (patterns that have survived)

One public verb: perceive(char, source). Two actions it can take between
your lines: consider_output() or idle_tick() (a silent internal attention
shift — replaying a salient memory to itself).
"""

import random
import time

from dream import Dreamer
from episodic import Episode, EpisodicLog
from markov import VariableOrderMarkov


def _common_suffix(a, b):
    i = 0
    la, lb = len(a), len(b)
    m = min(la, lb)
    while i < m and a[la - 1 - i] == b[lb - 1 - i]:
        i += 1
    return i


class Entity:
    def __init__(self, max_order=8, working_cap=64, dream_interval=500):
        self.markov = VariableOrderMarkov(max_order=max_order)
        self.episodic = EpisodicLog()
        self.dreamer = Dreamer(self.markov, self.episodic)

        self.working = ""
        self.working_cap = working_cap
        self.dream_interval = dream_interval

        self.tick_count = 0
        self.total_chars = 0
        self.last_surprise = 0.0
        self.copy_inhibition = 0.0          # 0 at birth, grows toward 1

    # ---------- perception ------------------------------------------------

    def perceive(self, c, source="user", weight=None):
        ctx = self.working
        s = self.markov.surprise(ctx, c)

        ep = Episode(time.time(), c, source, ctx, s)
        self.episodic.append(ep)

        # Learn from perception — but weight self-output much lower than
        # user input. Otherwise a single output becomes a teaching signal of
        # equal weight to your entire sentence, and the system can lock into
        # self-reinforcing attractors. The caller may override the weight
        # (e.g. solo mode needs higher self-weight since self IS the signal).
        if weight is None:
            weight = 1.0 if source == "user" else 0.2
        self.markov.update(ctx, c, weight=weight)
        self.markov.update_habituation(ctx, s)

        self.working = (self.working + c)[-self.working_cap:]
        self.last_surprise = s
        self.tick_count += 1
        self.total_chars += 1

        # copy-mirror fades over the first few hundred chars
        self.copy_inhibition = min(1.0, self.total_chars / 300.0)

        if self.total_chars % self.dream_interval == 0:
            self.dreamer.dream()

        return s

    def reward(self, r, window=50, decay=0.92):
        """
        Out-of-band reward signal. Not perceived as characters — the entity
        never sees the token that produced it. The reward diffuses backwards
        through recent episodes with exponential decay.
        """
        self.episodic.propagate_reward(r, window=window, decay=decay)

    # ---------- action ----------------------------------------------------

    def consider_output(self):
        """Return a single character to emit, or '' for silence."""
        ctx = self.working
        if not ctx:
            return ""

        last = ctx[-1]

        # Silence gating.
        # - If this context is deeply habituated AND the last character was
        #   unsurprising, stay almost entirely quiet (break ruts).
        # - Otherwise the more surprising / less-settled things feel, the
        #   more likely it is to speak.
        habit = self.markov.habituation(ctx)
        if habit is not None and habit < 0.5 and self.last_surprise < 0.5:
            silence_prob = 0.95
        else:
            excitement = max(self.last_surprise, habit or 0.0)
            silence_prob = 0.7 - min(0.55, excitement / 8.0)
        if random.random() < silence_prob:
            return ""

        # 1. Reward-biased recall:
        # find a high-reward past episode whose context most resembles ours,
        # and emit what followed it.
        best_ep = None
        best_score = 0.0
        for ep in self.episodic.recent(600):
            if ep.reward <= 0:
                continue
            overlap = _common_suffix(ep.context, ctx)
            if overlap == 0:
                continue
            score = ep.reward * (1 + overlap)
            if score > best_score:
                best_score = score
                best_ep = ep
        if best_ep is not None and best_score >= 1.2:
            if best_ep.c not in ("\n",):
                return best_ep.c

        # 2. Copy-mirror (infant behavior), decays as copy_inhibition grows.
        if random.random() < (1.0 - self.copy_inhibition) * 0.35:
            if last not in ("\n", "\r"):
                return last

        # 3. Orienting / sampled response: when the current context carries
        # surprise, sample from the model's learned distribution.
        if self.last_surprise > 1.5:
            probs, floor = self.markov.predict(ctx)
            if probs:
                total = sum(probs.values())
                if total > 0:
                    r = random.random() * total
                    acc = 0.0
                    for c, p in probs.items():
                        acc += p
                        if acc >= r:
                            if c not in ("\n", "\r"):
                                return c
                            break
        return ""

    def idle_tick(self):
        """
        One step of 'thinking' between user lines. Either emit a char, or
        perform an internal attention shift (silently re-experience a salient
        memory, updating only habituation). Returns the char to emit, or None.
        """
        if random.random() < 0.12 and len(self.episodic) > 0:
            self._attention_shift()
            return None
        out = self.consider_output()
        return out if out else None

    def _attention_shift(self):
        eps = self.episodic.top_salient(6)
        if not eps:
            return
        ep = random.choice(eps)
        s = self.markov.surprise(ep.context, ep.c)
        # Don't update counts here — this is private rumination, not learning.
        self.markov.update_habituation(ep.context, s * 0.5)
