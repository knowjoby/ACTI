"""
Episodic memory: a rolling log of every character the entity has perceived,
with its original context, the surprise it carried in the moment, and any
reward that later got propagated back to it.

Reward is propagated when the user types GOOD or BAD. The magnitude decays
exponentially the further back in time you go, so the entity associates
reward most strongly with whatever just happened.
"""

import time
from collections import deque


class Episode:
    __slots__ = ("t", "c", "source", "context", "surprise", "reward", "salience")

    def __init__(self, t, c, source, context, surprise):
        self.t = t
        self.c = c
        self.source = source          # 'user' or 'self'
        self.context = context        # working memory at time of perception
        self.surprise = surprise      # bits
        self.reward = 0.0
        self.salience = surprise      # updated later as reward arrives


class EpisodicLog:
    def __init__(self, capacity=30000):
        self.log = deque(maxlen=capacity)

    def append(self, ep):
        self.log.append(ep)

    def recent(self, n):
        n = min(n, len(self.log))
        # newest last
        return [self.log[len(self.log) - n + i] for i in range(n)]

    def propagate_reward(self, r, window=40, decay=0.9):
        w = 1.0
        i = len(self.log) - 1
        remaining = window
        while i >= 0 and remaining > 0:
            ep = self.log[i]
            ep.reward += r * w
            ep.salience += abs(r) * w
            w *= decay
            remaining -= 1
            i -= 1

    def top_salient(self, k):
        n = len(self.log)
        if n == 0:
            return []
        return sorted(self.log, key=lambda e: e.salience, reverse=True)[:k]

    def __len__(self):
        return len(self.log)
