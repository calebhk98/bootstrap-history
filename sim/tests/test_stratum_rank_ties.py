"""Strata that earn the same per head tie in rank, so the name orders them and not float noise
(sim/agents/strata_observed.py rank_key and observed_incomes), tested on plain stand-in strata."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.agents.strata_observed import observed_incomes, rank_key

QUICK_TOPIC = True

WORK_SHARE = 0.7
PAY = 0.1 + 0.2   # with these headcounts the per-head products differ in the last float digit


class BondedStand:
	"""A bonded stratum stand-in: its product is members x work share x pay of its trade."""

	def __init__(self, name, members):
		self.record = SimpleNamespace(stratum=name, members=members, plan={"trade": "labour", "work_share": WORK_SHARE})

	def is_bonded(self):
		return True


class FlatPayWorld:
	def __init__(self, pay):
		self.pay = pay

	def pay_per_person_year(self, trade):
		return self.pay


world = FlatPayWorld(PAY)
small, large = BondedStand("zzz", 3.0), BondedStand("aaa", 48696538.0)
raw_small = small.record.members * WORK_SHARE * PAY / small.record.members
raw_large = large.record.members * WORK_SHARE * PAY / large.record.members
check("the fixture is meaningful: unrounded per-head earnings differ by float noise", raw_small != raw_large,
      (raw_small, raw_large))
check("equal pay per head gives equal rank", rank_key(small, world) == rank_key(large, world),
      (rank_key(small, world), rank_key(large, world)))

curve = [(48696538.0, 10.0), (3.0, 1000.0)]   # a big poor cohort then a small rich one, as many people as the strata
for given in ([small, large], [large, small]):
	incomes = observed_incomes(given, world, curve)
	check("tied strata are laid along the curve by name, whatever order they are given",
	      incomes == {"aaa": 10.0, "zzz": 1000.0}, incomes)

check("a stratum that earns more per head ranks above one that earns less",
      rank_key(BondedStand("x", 4.0), FlatPayWorld(2.0)) > rank_key(BondedStand("x", 4.0), FlatPayWorld(1.0)))
