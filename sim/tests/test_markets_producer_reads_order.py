"""`ProducerReads.capacities` and `runs_last_year` list the producers in agent id order, whatever order the economy holds them
in, so a loaded game (producers held in id order) and a live one (in entry order) hand the same list to a consumer that sums floats."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer
from sim.markets.reads_producers import ProducerReads


def producer(agent_id, recipe_id, runs):
	return Producer(agent_id, "owner", recipe_id, "t_" + agent_id, runs, last_runs=runs)


class ProducerOrder(unittest.TestCase):
	def reads(self, producers):
		recipes = {"r": SimpleNamespace(inputs={"a": 1.0}, outputs={"b": 2.0})}
		economy = SimpleNamespace(record=SimpleNamespace(producers=ProducerStore({each.agent_id: each for each in producers})),
		                          setup=SimpleNamespace(countries=lambda: ["home"], recipes=recipes))
		agent = SimpleNamespace(opened=lambda: True, economy=lambda: economy)
		patches = ()
		for patch in patches:
			patch.start()
			self.addCleanup(patch.stop)
		return ProducerReads(agent)

	def test_capacities_are_listed_by_agent_id(self):
		reads = self.reads([producer("p3", "r", 3.0), producer("p1", "r", 1.0), producer("p2", "r", 2.0)])
		self.assertEqual(reads.capacities(), [("r", 1.0), ("r", 2.0), ("r", 3.0)])

	def test_the_producers_that_ran_are_listed_by_agent_id(self):
		reads = self.reads([producer("p3", "r", 3.0), producer("p1", "r", 1.0), producer("p2", "r", 0.0)])
		self.assertEqual([row["tile"] for row in reads.runs_last_year()], ["t_p1", "t_p3"])


if __name__ == "__main__":
	unittest.main()
