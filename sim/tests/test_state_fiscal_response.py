"""Complaints 625 and 626: a state short of money chooses among borrowing, cutting lines, deferring pay, debasing, levying
and demanding in kind. Each response has its consequences; the state's decision policy chooses, so a player's
state and an AI state face the same menu. No fixed cascade runs in `Government.advance`, and a rate the state
sets changes what its forms yield."""

QUICK_TOPIC = True

import inspect

from .harness import check

from sim.agents.tuning_fiscal import RATE_RAISE_STEP
from sim.agents import arrears, fiscal_response, government_levers, group_servants, revenue
from sim.agents.api import ActorRecord
from sim.agents.budget_line import Line
from sim.agents.government import Government
from sim.agents.policy import CallbackPolicy, IdlePolicy, make_policy

from .agents_fake_world import FakeWorld

GRAIN_FORM = {"form": "grain_levy", "basis": "harvest", "rate": 0.1, "paid_in": "wheat_kg"}
WEALTH_FORM = {"form": "wealth_tax", "basis": "coin_stock", "rate": 0.01}
COIN_STOCK = 20000.0
VISIBLE_INCOME = 5000.0
NEED = 1000.0
BORROWING_CEILING = 300.0


class ShortWorld(FakeWorld):
	"""A country with struck coin, one visible taxpayer and a grain levy; the government is set by the test."""

	def __init__(self):
		super().__init__()
		self.government_record = None
		self.prices = {"wheat_kg": 10.0}

	def state_may_borrow(self, state):
		return False

	def coin_regime(self):
		return "struck_coin"

	def coin_stock_value(self):
		return COIN_STOCK

	def visible_taxpayers(self):
		return [(1.0, VISIBLE_INCOME)]

	def notice_over(self, scale, capacity=None):
		return 1.0

	def revenue_forms(self):
		return government_levers.revenue_forms(self.government_record)

	def revenue_assessments(self):
		return revenue.assess(self)

	def harvest_tonnes(self):
		return 2000.0

	def arable_share(self, tiles):
		return 1.0

	def held_tiles(self):
		return ["a"]

	def output_tonnes(self, material, tiles=None):
		return 2000.0

	def material_price(self, material):
		return self.prices[material]

	def commodity_of(self, material):
		return material.replace("_kg", "")


class Lender(Government):
	"""A government that may borrow a little, at a stated rate."""

	def credit_ceiling(self, world):
		return BORROWING_CEILING

	def rate_on_loan(self, world, amount):
		return 0.08


def lines():
	return [Line("army", "requisition", transfer=600.0), Line("administration", "office", transfer=300.0),
			Line("roads", "office", transfer=100.0)]


def short_state(policy_kind=None, policy=None, borrows=True, coin_form=False):
	"""A government with an empty purse and a standing need of NEED, in a world that reads its record."""
	world = ShortWorld()
	state = (Lender if borrows else Government)("government:home", ActorRecord(kind="government", money=0.0), policy)
	if policy_kind:
		state.decision_policy = make_policy(policy_kind)
	state.record.revenue_in_kind = {"grain_levy": 200.0}
	state.record.revenue_forms = [dict(GRAIN_FORM)] + ([dict(WEALTH_FORM)] if coin_form else [])
	world.government_record = state.record
	return state, world


def decide(state, world):
	"""The share paid and the choice recorded, the way the year's standing need puts the question."""
	share = state.meet_shortfall(lines(), world)
	return share, dict(state.record.fiscal_response)


# ---- the menu: every response, each with its consequences --------------------------------------------------
state, world = short_state()
menu = fiscal_response.menu(state, world, lines(), NEED)
offered = {option.subject: option for option in menu.options}
coin_state, coin_world = short_state(coin_form=True)
coin_offered = {option.subject: option for option in fiscal_response.menu(coin_state, coin_world, lines(), NEED).options}
check("the menu offers every response but a rate raise, which needs a form collected in coin",
	  set(offered) == set(fiscal_response.RESPONSES) - {fiscal_response.RATE}, sorted(offered))
check("a state with a form collected in coin is offered raising its rate, and the cost is the burden on its base",
	  coin_offered[fiscal_response.RATE].detail["income_taken"] > 0.0
	  and abs(coin_offered[fiscal_response.RATE].worth - COIN_STOCK * WEALTH_FORM["rate"] * RATE_RAISE_STEP) < 1e-9, coin_offered.get(fiscal_response.RATE))
check("borrowing costs the interest the lender asks", offered["borrow"].detail["interest"] == 0.08, offered["borrow"].detail)
check("cutting lines loses the services", offered["cut_lines"].detail["services_lost"] > 0.0)
check("deferring pay leaves pay unpaid, which the army and officials feel",
	  offered["arrears"].detail["unpaid_pay"] > 0.0, offered["arrears"].detail)
check("debasing cuts the coin's metal, which is what raises prices",
	  offered["debase"].detail["coin_cut"] > 0.0, offered["debase"].detail)
check("levying and demanding in kind take more of the taxpayers' income",
	  offered["levy"].detail["income_taken"] > 0.0 and offered["demand_in_kind"].detail["income_taken"] > 0.0)
check("each response covers no more than it can",
	  offered["borrow"].worth == BORROWING_CEILING and offered["cut_lines"].worth == NEED
	  and offered["arrears"].worth == 900.0, {name: option.worth for name, option in offered.items()})

# ---- two states with different policies pick different responses to the same shortfall -----------------------
choices = {}
for kind in ("fiscal_consequence", "fiscal_cascade", "fiscal_austere", "fiscal_levy_first"):
	state, world = short_state(kind)
	share, choice = decide(state, world)
	choices[kind] = choice
	check("%s: what it covers adds up to the whole gap" % kind, abs(sum(choice.values()) - NEED) < 1e-6, choice)
check("the same shortfall is met in different ways by different policies",
	  len({tuple(sorted(choice)) for choice in choices.values()}) >= 3, choices)
check("the old order is one policy: it borrows, debases to the limit, and only then levies",
	  choices["fiscal_cascade"].get("borrow") == BORROWING_CEILING and choices["fiscal_cascade"].get("debase") == 500.0
	  and choices["fiscal_cascade"].get("levy") == NEED - BORROWING_CEILING - 500.0, choices["fiscal_cascade"])
check("a state that taxes before it debases levies and does not debase",
	  "levy" in choices["fiscal_levy_first"] and "debase" not in choices["fiscal_levy_first"], choices["fiscal_levy_first"])
check("a state that dreads debt, debasement and burden cuts lines before it will bear them",
	  choices["fiscal_austere"].get("cut_lines", 0.0) > 0.0 and "debase" not in choices["fiscal_austere"],
	  choices["fiscal_austere"])
check("a state valuing consequences defers pay rather than cutting it",
	  "arrears" in choices["fiscal_consequence"] and "cut_lines" not in choices["fiscal_consequence"],
	  choices["fiscal_consequence"])

# ---- a player's state faces the same menu and names its responses --------------------------------------------
player, world = short_state(policy=CallbackPolicy(lambda actor, decision: ["debase"]))
share, choice = decide(player, world)
check("a player's state that names debasing debases as far as it can reach, and the rest is cut",
	  choice.get("debase", 0.0) > 0.0 and choice.get("cut_lines", 0.0) >= 0.0 and abs(sum(choice.values()) - NEED) < 1e-6, choice)
idle, world = short_state(policy=IdlePolicy())
check("a state whose policy chooses nothing cuts its lines", decide(idle, world)[1] == {"cut_lines": NEED})

# ---- each response's consequence follows -------------------------------------------------------------------
borrower, world = short_state(policy=CallbackPolicy(lambda actor, decision: ["borrow"]))
share, choice = decide(borrower, world)
check("borrowing leaves less unpaid: the share paid is the purse plus the loan over the need",
	  abs(share - BORROWING_CEILING / NEED) < 1e-9, share)

for name, response_kind in (("arrears", "arrears"), ("cut_lines", "cut")):
	state, world = short_state(policy=CallbackPolicy(lambda actor, decision, name=name: [name]), borrows=False)
	share, choice = decide(state, world)
	arrears.owe(state.record, lines(), share, state.deferred_fraction(lines(), share))
	if name == "arrears":
		check("deferring pay books the pay it did not pay as owed", abs(arrears.total(state.record) - 600.0 - 300.0) < 1e-6
			  and state.record.arrears["army"] == 600.0, state.record.arrears)
	else:
		check("cutting a line owes nothing", arrears.total(state.record) == 0.0, state.record.arrears)

owed_state, world = short_state(policy=CallbackPolicy(lambda actor, decision: ["arrears"]), borrows=False)
share, choice = decide(owed_state, world)
owed_state.record.need = {"army": 600.0}
owed_state.record.income_reference = {group_servants.ARMY_PAY_SHARE: 1.0}
owed_state.record.arrears_paid = {}
check("unpaid pay is the grievance that lowers the army's loyalty",
	  group_servants.step_loyalty(1.0, 0.5) < 1.0 and group_servants.step_loyalty(1.0, 0.0) == 1.0)

debaser, world = short_state(policy=CallbackPolicy(lambda actor, decision: ["debase"]))
decide(debaser, world)
steady, world = short_state(policy=CallbackPolicy(lambda actor, decision: ["borrow"]))
decide(steady, world)
check("debasing cuts the metal in the coin and a state that did not debase leaves it whole",
	  debaser.record.coin_cut_share > 0.0 and debaser.record.coin_metal_kept < 1.0
	  and steady.record.coin_cut_share == 0.0 and steady.record.coin_metal_kept == 1.0,
	  (debaser.record.coin_cut_share, steady.record.coin_cut_share))

levier, world = short_state(policy=CallbackPolicy(lambda actor, decision: ["levy"]), borrows=False)
share, choice = decide(levier, world)
levier.record.unfunded = {"army": 600.0 * (1 - share), "administration": 300.0 * (1 - share), "roads": 100.0 * (1 - share)}
levier.seek_shortfall(lines(), world)
other, world = short_state(policy=CallbackPolicy(lambda actor, decision: ["arrears"]), borrows=False)
decide(other, world)
other.record.unfunded = dict(levier.record.unfunded)
other.seek_shortfall(lines(), world)
check("levying raises the rate it takes from what it can see, and deferring does not",
	  levier.record.levy_requisition_rate + levier.record.levy_office_rate > 0.0
	  and other.record.levy_requisition_rate + other.record.levy_office_rate == 0.0,
	  (levier.record.levy_requisition_rate, other.record.levy_requisition_rate))

# ---- 626: a rate the state sets is read after the file's starting rate, and changes what the form yields ------------
kinder, world = short_state(policy=CallbackPolicy(lambda actor, decision: ["demand_in_kind"]), borrows=False)
before = {assessed.form: assessed for assessed in revenue.assess(world)}["grain_levy"]
decide(kinder, world)
after = {assessed.form: assessed for assessed in revenue.assess(world)}["grain_levy"]
check("the file's rate is only the starting rate: the state's demand in kind sets a higher one",
	  before.rate == GRAIN_FORM["rate"] and after.rate > before.rate and GRAIN_FORM["rate"] == 0.1, (before.rate, after.rate))
check("a state-set rate yields more of the same base", after.tonnes > before.tonnes and after.money > before.money,
	  (before.tonnes, after.tonnes))
check("the rate it set is a lever like any a player pulls",
	  kinder.record.levers["revenue"]["grain_levy"]["rate"] == after.rate, kinder.record.levers)
plain, plain_world = short_state(policy=CallbackPolicy(lambda actor, decision: ["borrow"]), borrows=False)
decide(plain, plain_world)
check("a state that did not demand in kind keeps the starting rate",
	  {assessed.form: assessed for assessed in revenue.assess(plain_world)}["grain_levy"].rate == GRAIN_FORM["rate"])

# ---- 626: an AI state under a shortfall raises the rate of a form it collects in coin ----------------------------
raiser, world = short_state(borrows=False, coin_form=True)
raiser.decision_policy = fiscal_response.OrderedFiscalPolicy((fiscal_response.RATE, fiscal_response.CUT))
before = {assessed.form: assessed for assessed in revenue.assess(world)}["wealth_tax"]
share, choice = decide(raiser, world)
after = {assessed.form: assessed for assessed in revenue.assess(world)}["wealth_tax"]
check("an AI state that values taxing its people raises the rate of a coin form to cover the shortfall",
	  choice.get(fiscal_response.RATE, 0.0) > 0.0 and after.rate > before.rate == WEALTH_FORM["rate"], (choice, before.rate, after.rate))
check("the raised rate yields more of the same base next year", after.money > before.money and after.base == before.base)
check("the file's form is left as it was: the rate is the state's own", WEALTH_FORM["rate"] == 0.01
	  and raiser.record.revenue_forms[1]["rate"] == 0.01 and raiser.record.levers["revenue"]["wealth_tax"]["rate"] == after.rate,
	  (raiser.record.revenue_forms, raiser.record.levers))
steady_rate, world = short_state(policy=CallbackPolicy(lambda actor, decision: ["borrow"]), borrows=True, coin_form=True)
decide(steady_rate, world)
check("a state that does not choose it keeps its rate", "revenue" not in steady_rate.record.levers, steady_rate.record.levers)

# ---- no fixed cascade remains in the year -----------------------------------------------------------------------
source = inspect.getsource(Government.advance)
check("the year does not run a debasement or a uniform cut itself", "decide_debasement" not in source
	  and "funded_share" not in source and "funded_share" not in inspect.getsource(Government.pay_standing_need), source)
check("how a shortfall is met is recorded as the state's choice", hasattr(ActorRecord(kind="government"), "fiscal_response"))
