"""Complaints 220 and 248: `quote hire`, `quote commission`, `quote open` and `quote bounty` show the figure the sim function that
the command charges with returns, and the charge is that function's figure (`hire` and `commission` pay what `hire_check` and
`commission_check` return; `post_bounty` pays `bounty_price`). Each quoter and each charge runs on a stand-in carrying only
what it reads, with the sim's cost functions returning figures written out here. Opening's charge goes through the large
`open_venture`, which this does not stand in for."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.labour.labour_training import TrainingMixin
from sim.engine.project_materials import ProjectMaterialsMixin
from sim.engine.projects_starting import StartingMixin
from sim.refusal import Refusal
from sim.ui.proto import quote_spending


def quote_game(**attributes):
    labour = SimpleNamespace(
        hire_check=lambda trade, count: (count, 412.34, None),
        commission_check=lambda trade, hours: (207.77, None),
        market=SimpleNamespace(quote_annual=lambda trade, count: 400.04))
    defaults = dict(
        capital=5000.0, labour=labour, BOUNTY_PRICE_MULTIPLIER=3.0, done=set(), operating=set(), active={}, civ={"name": "Testland"},
        bounty_price=lambda node_id: 9000.06, bounty_eligible=lambda node_id: True, project_cost_now=lambda node_id: 3000.0,
        opening_fee=lambda node_id, units: (812.34, 1.0), is_venture=lambda node_id: True,
        venture_upkeep_quote=lambda node_id, units: {"now": 61.1, "at_full_staffing": 120.9},
        venture_real_earnings=lambda node_id, units, fully_ramped: 300.0, spending_power=lambda kind: 1000.0,
        opening_shortfall=lambda node_id: None)
    defaults.update(attributes)
    return SimpleNamespace(**defaults)


NODES = {"mill": {"name": "Mill", "pre": [], "cat": "craft"}}

hire = quote_spending._quote_hire(quote_game(), NODES, {"trade": "Smith", "n": 2})
check("quote hire shows the fee hire_check returns, rounded to a tenth, and the wage due each later year",
      hire["paid_now"] == 412.3 and hire["from_next_year_per_year"] == 800.1 and hire["people"] == 2 and hire["trade"] == "smith", hire)
refusing = quote_game(labour=SimpleNamespace(hire_check=lambda trade, count: (None, None, Refusal("no_such_trade", "no such trade"))))
check("quote hire passes hire_check's refusal on", quote_spending._quote_hire(refusing, NODES, {"trade": "x"}).get("ok") is False)
check("quote hire refuses a count that is not a number",
      quote_spending._quote_hire(quote_game(), NODES, {"trade": "smith", "n": "banana"}).get("ok") is False)

commission = quote_spending._quote_commission(quote_game(), NODES, {"trade": "smith", "hours": 100})
check("quote commission shows the fee commission_check returns", commission["paid_now"] == 207.8 and commission["hours"] == 100, commission)
check("quote commission passes commission_check's refusal on",
      quote_spending._quote_commission(quote_game(labour=SimpleNamespace(commission_check=lambda trade, hours: (None, "no"))), NODES,
                                       {"trade": "smith", "hours": 5}).get("ok") is False)

opened = quote_spending._quote_open(quote_game(done={"mill"}), NODES, {"id": "mill"})
check("quote open shows opening_fee's charge and whether it can be paid from the spending power",
      opened["paid_now"] == 812.3 and opened["can_afford"] is True and opened["size"] == 1.0, opened)
check("quote open shows the running cost now and at full staffing as venture_upkeep_quote gives them",
      (opened["costs_a_year_to_run"], opened["costs_a_year_at_full_staffing"]) == (61.1, 120.9), opened)
check("quote open says it cannot be afforded when the charge passes the spending power",
      quote_spending._quote_open(quote_game(done={"mill"}, spending_power=lambda kind: 100.0), NODES, {"id": "mill"})["can_afford"] is False)
check("quote open names the staff short when the concern cannot be supervised",
      "staff_short" in quote_spending._quote_open(quote_game(done={"mill"}, opening_shortfall=lambda node_id: (1.0, 2.0, 0.0, 0.5)),
                                                  NODES, {"id": "mill"}))
check("quote open refuses what is not worked out, not a concern, or already running",
      [quote_spending._quote_open(quote_game(**changes), NODES, {"id": "mill"}).get("ok")
       for changes in ({}, {"done": {"mill"}, "is_venture": lambda node_id: False}, {"done": {"mill"}, "operating": {"mill"}})]
      == [False, False, False])

bounty = quote_spending._quote_bounty(quote_game(), NODES, {"id": "mill"})
check("quote bounty shows bounty_price's figure, the multiplier and that it is allowed",
      bounty["paid_now"] == 9000.1 and bounty["price_multiplier"] == 3.0 and bounty["eligible"] is True, bounty)
refused = quote_spending._quote_bounty(quote_game(bounty_eligible=lambda node_id: False), NODES, {"id": "mill"})
check("quote bounty for what the craft cannot recognise says it is not eligible and carries the refusal",
      refused["eligible"] is False and refused["refusal"].cause == "not_bounty_eligible", refused)


charge_hire = TrainingMixin.hire   # the method under test, called on the stand-in below


class Payer(TrainingMixin):
    """The labour side of a Sim that a hire or commission charge touches, recording the money paid."""

    def __init__(self, fee):
        self.paid = []
        household = SimpleNamespace(wages_prepaid=0.0, contract_hours={}, commissioned={})
        self._world = SimpleNamespace(
            wages={"smith": 1.0}, state=SimpleNamespace(household=household), EDGE_WORKERS="workers", HOURS_PER_PERSON_YEAR=2000.0,
            pay_edge=lambda edge, money, purpose: self.paid.append((edge, money, purpose)), money_text=lambda money, grouped=False: "%.0f" % money)
        self.labour_market = SimpleNamespace(hire=lambda *arguments: None)
        self.fee = fee
        self.hire_asked = []

    def hire_check(self, trade, count, pay_premium=0.0):
        self.hire_asked.append((trade, count))
        return count, self.fee, None

    def commission_check(self, trade, hours):
        return self.fee, None

    def note_hire_pay(self, trade, count, premium):
        pass

    def add_employed(self, trade, count):
        pass

    def _resync_pools(self):
        pass

    def employed(self, trade):
        return 1.0

    def household_room(self):
        return 5.0


payer = Payer(412.34)
done, message = charge_hire(payer, "Smith", 2)
check("hire pays the workers' edge exactly the fee hire_check returned, and carries it as prepaid wages",
      done and payer.paid == [("workers", 412.34, "hiring fee and first year's wages")]
      and payer._world.state.household.wages_prepaid == 412.34, payer.paid)
check("hire asks hire_check for the trade as typed lower-case", payer.hire_asked == [("smith", 2)], payer.hire_asked)
payer = Payer(207.77)
done, message = payer.commission("smith", 100)
check("commission pays the workers' edge exactly the fee commission_check returned and books the hours",
      done and payer.paid == [("workers", 207.77, "commissioned craftsmen")]
      and payer._world.state.household.contract_hours == {"smith": 100}, payer.paid)
refusing_payer = Payer(0.0)
refusing_payer.commission_check = lambda trade, hours: (None, "refused")
check("a commission refused by its check pays nothing", refusing_payer.commission("smith", 100) == (False, "refused") and not refusing_payer.paid)


class Poster(StartingMixin):
    """The parts of a Sim a bounty touches."""

    def __init__(self, capital, price):
        self.nodes = {"mill": {"name": "Mill"}}
        self.state = SimpleNamespace(
            household=SimpleNamespace(capital=capital, total_spend=0.0, bounties_paid=0, log=[]),
            projects=SimpleNamespace(active={}, bountied=set()), scenario=SimpleNamespace(year=100))
        self.price = price
        self.paid = []

    def bounty_price(self, node_id):
        return self.price

    def pay_edge(self, edge, money, purpose):
        self.paid.append((money, purpose))

    def initialize_project(self, node_id, **fields):
        self.state.projects.active[node_id] = {}

    def money_text(self, money, *arguments, **keywords):
        return "%.0f" % money


poster = Poster(10000.0, 9000.06)
check("post_bounty pays exactly bounty_price, the figure quote bounty shows",
      poster.post_bounty("mill") is True and poster.paid == [(9000.06, "bounties posted")], poster.paid)
broke = Poster(100.0, 9000.06)
check("post_bounty pays nothing when the prize passes the cash", broke.post_bounty("mill") is False and not broke.paid)
