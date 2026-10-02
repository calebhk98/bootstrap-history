"""The techniques some producer in the society actually runs, which is what the goods' prices follow.

A technology that is held (researched, copied) but run by no producer changes no cost and no supply, so it
changes no price. The set is the techniques the society started with, the nodes the founder operates, and
the nodes any firm's concerns run. The price solver is asked about this set, not about everything held.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): a technique counts for every producer of the good as soon as one
producer runs it (copying inside a line of business is instant); a per-producer technique, with cost from
what that producer runs and supply from what it makes, would replace the solved long-run price as the anchor.
"""


class TechniquesInUseMixin:

    def price_epoch(self):
        """Changes whenever the techniques in use might, or the price level does: for caches whose
        answers read prices."""
        projects = self.state.projects
        return (getattr(projects, "_done_ver", 0), getattr(projects, "_operating_ver", 0),
                self.actor_market_version(), self.home_price_level())

    def techniques_in_use(self):
        """Nodes whose production entries some producer runs now."""
        epoch = self.price_epoch()
        cached = getattr(self, "_techniques_in_use_cache", None)
        projects = self.state.projects
        if (cached is not None and cached[0] == epoch and cached[2] is projects.done
                and cached[3] is projects.operating):
            return cached[1]
        in_use = set(projects.granted) | set(projects.operating)
        if self.state.actors is not None and self.state.actors.records:
            for firm in self.actors.active_firms():
                in_use.update(firm.concerns)
        in_use = frozenset(in_use)
        self._techniques_in_use_cache = (epoch, in_use, projects.done, projects.operating)
        return in_use
