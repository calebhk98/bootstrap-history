"""The techniques some producer in the society actually runs.

A technology that is held (researched, copied) but run by no producer changes no cost and no supply, so it
changes no price. The set is the techniques the society started with, the nodes the founder operates, and
the nodes any firm's concerns run. It decides which entries a concern may run (volume.py) and the
baseline for a good no incumbent makes (sim/prices/tables.py); it does not set a price: each producer offers at
the cost of its own entry (sim/prices/cost_books.py) and the market clears the offers.

A concern in the same line of business as a producer reaches the producer's technique only after the copying
time (the diffusion module's `techniques_spread`), so a new technique shows first in its adopter's volume and later
in the others'.
Needs: the views of READS_BY_OWNER in module_spec.py."""


class Techniques:

	def techniques_epoch(self):
		"""Changes whenever the techniques in use might."""
		done_version, operating_version, _units_version = self.needs.running_versions()
		return (done_version, operating_version, self.needs.concern_versions()[0])

	def price_epoch(self):
		"""Changes whenever the techniques in use might, or the price level does: for caches whose
		answers read prices."""
		return self.techniques_epoch() + (self.needs.home_price_level(),)

	def techniques_in_use(self):
		"""Nodes whose production entries some producer runs now."""
		needs = self.needs
		done_version, operating_version, _units_version = needs.running_versions()
		epoch = (done_version, operating_version, needs.concern_versions()[1])
		cached = getattr(self, "_techniques_in_use_cache", None)
		done = needs.techniques_held()
		operating = needs.operating()
		if cached is not None and cached[0] == epoch and cached[2] is done and cached[3] is operating:
			return cached[1]
		in_use = set(needs.techniques_granted()) | set(operating)
		in_use.update(needs.concerns_of_active_firms())
		in_use = frozenset(in_use)
		if cached is not None and cached[1] == in_use:
			in_use = cached[1]      # the same set stays the same object, so what is keyed on it holds
		self._techniques_in_use_cache = (epoch, in_use, done, operating)
		return in_use
