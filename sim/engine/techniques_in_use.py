"""The techniques some producer in the society actually runs.

A technology that is held (researched, copied) but run by no producer changes no cost and no supply, so it
changes no price. The set is the techniques the society started with, the nodes the founder operates, and
the nodes any firm's concerns run. It decides which entries a concern may run (concern_volume.py) and the
baseline for a good no incumbent makes (incumbent_prices.py); it does not set a price: each producer offers at
the cost of its own entry (producer_costs.py) and the market clears the offers.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): a technique counts for every concern in the line of business as soon as
one producer runs it (copying inside a line of business is instant); a producer-by-producer set would replace it.
"""


class TechniquesInUseMixin:

    def techniques_epoch(self):
        """Changes whenever the techniques in use might."""
        projects = self.state.projects
        return (self.household.done_version, self.household.operating_version,
                self.actor_market_version())

    def price_epoch(self):
        """Changes whenever the techniques in use might, or the price level does: for caches whose
        answers read prices."""
        return self.techniques_epoch() + (self.home_price_level(),)

    def techniques_in_use(self):
        """Nodes whose production entries some producer runs now."""
        epoch = self.techniques_epoch()
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
        if cached is not None and cached[1] == in_use:
            in_use = cached[1]      # the same set stays the same object, so what is keyed on it holds
        self._techniques_in_use_cache = (epoch, in_use, projects.done, projects.operating)
        return in_use
