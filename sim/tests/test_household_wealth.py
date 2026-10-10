"""Complaint 376: a firm's founder is a household of a stratum with its own wealth, not the stratum's average member.
Savings are spread over the households as a power law, a household's stake stays committed to it while the firm
runs, and a closed firm frees it again."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import firm_entry, firm_exit, household_wealth
from sim.agents.stratum import Stratum  # noqa: F401  (registers the kind)

from .agents_fake_world import FakeWorld, make_node, total_money


def make_stratum(members=1000.0, savings=1.0e6):
	registry = ActorRegistry(ActorsState(home_country="home"))
	stratum = registry.add("stratum:home:merchants", ActorRecord(kind="stratum", stratum="merchants", members=members, money=savings))
	return registry, stratum


# ---- savings are spread: the richest household holds far more than the average, the poorest far less -------
registry, stratum = make_stratum()
mean = 1.0e6 / 1000.0
richest = household_wealth.wealth_of_rank(stratum, 1)
poorest = household_wealth.wealth_of_rank(stratum, 1000)
check("the richest household holds many times the average", richest > 10.0 * mean, (richest, mean))
check("the poorest holds a fraction of it", poorest < 0.5 * mean, (poorest, mean))
total = sum(household_wealth.wealth_of_rank(stratum, rank) for rank in range(1, 1001))
check("the households together hold about the stratum's savings", abs(total - 1.0e6) / 1.0e6 < 0.2, total)

# ---- a founder can never put up more than the stratum holds -----------------------------------------------
registry, thin = make_stratum(members=2.0, savings=10.0)
check("a founder puts up no more than the purse", household_wealth.personal_capital(thin) <= 10.0)
registry, empty = make_stratum(savings=0.0)
check("a stratum with no savings has no founder", household_wealth.personal_capital(empty) == 0.0)

# ---- what a household commits stays committed ------------------------------------------------------------
registry, stratum = make_stratum()
first = household_wealth.personal_capital(stratum)
rank = household_wealth.commit(stratum, first * 0.9)
check("the richest household is the first to found", rank == 1, rank)
check("its commitment is remembered on the stratum", abs(stratum.record.plan["committed"]["1"] - first * 0.9) < 1e-9)
next_rank, next_free = household_wealth.richest_free(stratum)
check("the next founder is another household once the first has tied its wealth up", next_rank != 1 or next_free < first)
household_wealth.release(stratum, 1, first * 0.9)
check("freeing it restores the household", "1" not in stratum.record.plan["committed"]
	and abs(household_wealth.personal_capital(stratum) - first) < 1e-6)

# ---- entry draws on one household, and its firm gives the stake back on closing ----------------------------
class EntryWorld(FakeWorld):
	def entry_gross(self, node_id, rivals, entrants):
		return float(self.nodes[node_id]["rev"]) / (rivals + entrants)

	def plant_cost(self, node_id, actor, step):
		return 1000.0 * step


world = EntryWorld()
world.nodes["shop"] = make_node("shop", hours=100.0, revenue=60000.0, upkeep=1000.0)
world.demonstrated_nodes = {"shop"}
world.proven = {"shop"}
registry, stratum = make_stratum(members=1000.0, savings=1.0e9)
before = total_money(registry.actors.values())
founded = registry.consider_entry(world)
check("a stratum founds firms", len(founded) >= 1, founded)
firm = registry.actors[founded[0]]
check("the firm names the household that funded it", firm.record.plan.get("founder_household") == 1 and firm.record.plan.get("stake", 0.0) > 0.0, firm.record.plan)
check("money is conserved", abs(total_money(registry.actors.values()) - before) < 1e-6)
committed = sum(stratum.record.plan["committed"].values())
paid = sum(registry.actors[firm_id].record.plan.get("stake", 0.0) for firm_id in founded)
check("the households together have committed what the firms were given", abs(committed - paid) < 1e-6, (committed, paid))
firm_exit.close_firm(firm, world)
check("closing the firm frees the household's stake", sum(stratum.record.plan["committed"].values()) < committed)
