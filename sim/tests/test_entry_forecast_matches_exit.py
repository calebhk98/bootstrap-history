"""Complaint 679: a firm entry admits is not one exit would close at full ramp in an unchanged market. Entry and exit are
built from the same market, costs and levy; the state's levy on takings is one of the costs entry weighs."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import adoption, imitation
from sim.agents.api import ActorRecord, Business, ActorRegistry, ActorsState, Firm

from sim.agents.government import Government

from .agents_fake_world import FakeWorld, make_node

LEVY_SHARE = 0.2   # a stand-in state's take of a firm's takings


class LevyGovernment:
	"""A state that levies a fixed share of what a payer takes."""

	def __init__(self, share):
		self.share = share

	def assess(self, payer, taxable, world):
		levy = self.share * max(0.0, taxable)
		return levy, {"requisition": levy}

	def collect(self, payer, taxable, world):
		return self.assess(payer, taxable, world)[0]


class LeviedMarketWorld(FakeWorld):
	"""One niche whose takings its sellers share, with a rent, a plant to build and a state that levies."""

	def __init__(self, share, takings=400000.0, rent=2000.0):
		super().__init__()
		self.takings, self.rent = takings, rent
		self.output = 1.0e12
		self.nodes["shop"] = make_node("shop", hours=4000.0, revenue=takings, upkeep=1000.0)
		self.demonstrated_nodes = {"shop"}
		self.proven = {"shop"}
		self.government_actor = LevyGovernment(share)

	def entry_gross(self, node_id, rivals, entrants):
		return self.takings / (rivals + entrants)

	def site_rent(self, node_id, capacity=1.0, tile=None):
		return self.rent * capacity

	def copy_cost(self, node_id):
		return 20000.0

	def plant_cost(self, node_id, actor=None, capacity=1.0):
		return imitation.copy_plan(actor, [node_id], self)["total"] * capacity   # as the engine prices a plant

	def market_rate(self):
		return 0.05


def admitted_then_run(share):
	"""Firms entry admits into a market, each then run one year at full ramp among the others. Returns the
	number admitted and how many of them earn no more than exit's
	hurdle (the market's return on their plant), a loss included."""
	world = LeviedMarketWorld(share)
	registry = ActorRegistry(ActorsState(home_country="home"))
	admitted = len(registry.consider_entry(world))
	weak = 0
	for number in range(admitted):
		firm = Firm("firm:%d" % (1000 + number), ActorRecord(kind="firm", founded_year=world.year - 10, money=1.0e9,
												  business=Business.running(["shop"], opened_year=world.year - 10)))
		firm.rivals_of = lambda node_id, asking_id, count=admitted: float(count - 1)
		firm.operate(world)
		weak += firm.record.last_margin <= world.plant_cost("shop", firm, 1.0) * world.market_rate()
	return admitted, weak


admitted_untaxed, weak_untaxed = admitted_then_run(0.0)
admitted_taxed, weak_taxed = admitted_then_run(LEVY_SHARE)
check("the market admits several firms", admitted_untaxed > 1, admitted_untaxed)
check("untaxed, no firm entry admits is one exit would close", weak_untaxed == 0, (admitted_untaxed, weak_untaxed))
check("a levy on takings means fewer entrants", admitted_taxed < admitted_untaxed, (admitted_taxed, admitted_untaxed))
check("taxed, no firm entry admits is one exit would close", weak_taxed == 0, (admitted_taxed, weak_taxed))


# ---- a firm founded to run its concern has no incumbent technique to trial against: its plant runs whole
class TrialWorld(FakeWorld):
	def __init__(self):
		super().__init__()
		self.baseline = {"base"}
		self.nodes["base"] = make_node("base")
		self.nodes["tech"] = make_node("tech", ["base"])
		self.nodes["other"] = make_node("other", ["base"])
		self.demonstrated_nodes = {"tech", "other"}
		self.government_actor = Government("government:home", ActorRecord(kind="government", money=1000.0))

	def concern_margin(self, node_id):
		return 10.0


def trialled(concerns):
	"""Whether a firm that knows `tech` and runs `concerns` starts a trial of it, and the weight its plant of it runs at."""
	firm = Firm("firm:1", ActorRecord(kind="firm", money=1000.0, founded_year=100, business=Business.running(concerns)))
	firm.knowledge.update({"tech"})
	firm.aware["tech"] = 100
	adoption.advance_actor(firm, TrialWorld())
	return "tech" in firm.adoption, adoption.plant_weight(firm.adoption, "tech")


check("a firm whose only concern is the technique runs it whole, without a trial", trialled(["tech"]) == (False, 1.0), trialled(["tech"]))
started, weight = trialled(["tech", "other"])
check("a firm with another concern to displace still trials the technique on a pilot share", started and weight < 1.0, (started, weight))
