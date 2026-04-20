"""
Dream phase.

Periodically (every DREAM_INTERVAL characters of lived experience) the entity
stops consuming new input and instead replays its most salient past episodes
into the Markov counts. Positively-rewarded episodes are amplified;
strongly punished ones are skipped entirely (a kind of active forgetting).

Rare max-order contexts are pruned. This is the only structural cleanup
the system ever does — the rest is pure accumulation.
"""


class Dreamer:
    def __init__(self, markov, episodic):
        self.markov = markov
        self.episodic = episodic
        self.cycles = 0

    def dream(self, top_k=60, passes=2, prune_budget=200):
        self.cycles += 1
        top = self.episodic.top_salient(top_k)
        for ep in top:
            if ep.reward < -0.5:
                # actively avoid re-learning this
                continue
            weight = 1.0 + max(0.0, ep.reward)
            for _ in range(passes):
                self.markov.update(ep.context, ep.c, weight=weight)
        self._prune_rare(prune_budget)

    def _prune_rare(self, budget):
        k = self.markov.max_order
        table_dict = self.markov.ctx[k]
        to_del = []
        for ctx_str, cnts in table_dict.items():
            if sum(cnts.values()) <= 1:
                to_del.append(ctx_str)
                if len(to_del) >= budget:
                    break
        for ctx_str in to_del:
            del table_dict[ctx_str]
