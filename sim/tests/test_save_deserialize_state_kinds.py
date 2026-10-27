"""`deserialize_state` on a written-out saved structure, one kind of value per check, asserting the exact state it builds.
Types come from the dataclass annotations: sets from sorted lists, integer-typed values coerced back from the JSON's
text or floats, counters and default dicts rebuilt, None-means-never kept, nested records rebuilt as their classes. Order
is part of the claim: a dict comes back in the order the save holds it, a list likewise, so a loaded game iterates as saved."""
QUICK_TOPIC = True

import collections

from sim.agents.api import ActorsState, Business
from sim.contracts import FACILITY, Contract
from sim.diffusion.api import DiffusionSeat
from sim.finance.api import FinanceSeat
from sim.materials.state import MaterialsSeat
from sim.polity.state import PolitySeat
from sim.production.api import ProductionSeat
from sim.workforce.api import WorkforceSeat
from sim.engine.state import (ActiveProjectState, EconomyState, FounderState, HoldingsState, HouseholdState, ProjectsState,
                              SimulationState, deserialize_state)
from sim.foreign_trade.api import ForeignTradeWorld
from sim.refusal import Refusal, cause_of
from sim.reporting.api import ReportingSeat
from sim.resources.api import ResourcesSeat
from sim.tests.harness import check

EMPTY_BOOK = {"money": {}, "goods": {}, "gross_money": {}, "gross_goods": {}, "money_by_purpose": {}, "goods_by_purpose": {},
              "edge_money_volume": {}, "edge_money_net": {}, "edge_goods_volume": {}, "edge_goods_net": {}, "supply_at_start": {}}

# ---- what the blob is read as when no class is named
check("deserialize_state: None is None", deserialize_state(None) is None)
check("deserialize_state: a blob that is not a dict is handed back", deserialize_state([1, 2]) == [1, 2] and deserialize_state("text") == "text")
check("deserialize_state: a blob with ph_left is an active project",
      type(deserialize_state({"ph_left": 1, "cost_left": 2, "yrs": 1, "spent": 0.5, "status": "ACTIVE"})) is ActiveProjectState)
check("deserialize_state: any other dict is the whole simulation state",
      type(deserialize_state({"seats": {"a": {"household": {"capital": 1.0}, "projects": {}, "founder": None}}, "acting_seat": "a"})) is SimulationState)
check("deserialize_state: a scalar is coerced to the class named", deserialize_state("7", int) == 7 and deserialize_state(3, float) == 3.0
      and deserialize_state(5, str) == "5" and deserialize_state("true", bool) is True and deserialize_state("0", bool) is False)

# ---- the household: None-means-never, defaults for what the save lacks, unknown and plumbing keys ignored
household = deserialize_state({"capital": 50.0,
                               "cash_flow": {"wages": -12.5}, "cash_mark": None, "cash_periods": [{"year": 99, "net": 3.0}],
                               "_on_change_hook": 1, "not_a_field": 9}, HouseholdState)
workforce = deserialize_state({"wages_earned": None, "trades_created": {"__set__": ["baker", "mason"]}, "trade_introduced_year": {"mason": 95},
                               "employees": {"mason": 2}, "training": [["mason", 2]],
                               "unused_hours_reported": {"order:1": [40.0, "no_hands"]}, "_on_change_hook": 1, "not_a_field": 9}, WorkforceSeat)
check("deserialize_state: a household's purse, None-means-never fields and zeros are as saved",
      household.capital == 50.0 and workforce.wages_earned is None
      and household.cash_mark is None, None)
_debt = deserialize_state({"interest_paid": None, "last_settlement": -999, "insolvent_years": 0}, FinanceSeat)
check("deserialize_state: a finance seat's None-means-never fields, negative defaults and zeros are as saved, and what the save lacks is the default",
      _debt.interest_paid is None and _debt.last_settlement == -999 and _debt.insolvent_years == 0 and _debt.credit_frozen_until == 0, None)
_standing = deserialize_state({"last_withdrawal": None, "scandal_last_year": 0.0}, PolitySeat)
check("deserialize_state: a polity seat's None-means-never fields and zeros are as saved, and what the save lacks is the default",
      _standing.last_withdrawal is None and _standing.scandal_last_year == 0.0 and _standing.reputation == 5.0
      and _standing.demand_stance == "comply", None)
check("deserialize_state: a seat's sets are sets, its dicts typed, its lists kept",
      workforce.trades_created == {"baker", "mason"} and type(workforce.trades_created) is set
      and workforce.trade_introduced_year == {"mason": 95} and workforce.employees == {"mason": 2.0}
      and workforce.training == [["mason", 2]] and household.cash_flow == {"wages": -12.5}
      and household.cash_periods == [{"year": 99, "net": 3.0}] and workforce.unused_hours_reported == {"order:1": [40.0, "no_hands"]}, None)
_reporting = deserialize_state({"log": [[100, "built a mill"]]}, ReportingSeat)
check("deserialize_state: a list of pairs annotated as tuples comes back as tuples", _reporting.log == [(100, "built a mill")] and type(_reporting.log[0]) is tuple, _reporting.log)
check("deserialize_state: a field the save lacks takes its default", workforce.trades_endemic == set() and workforce.granted_staff is None and workforce.work_trade is None, None)
check("deserialize_state: an unknown key and an `_on_change` key are not set", not hasattr(workforce, "not_a_field") and not hasattr(workforce, "_on_change_hook"))

# ---- the retry counts, nested records and sets of the projects
projects = deserialize_state({
	"active": {"z_mill": {"ph_left": 80, "cost_left": 300, "yrs": 1.5, "spent": 100, "status": "ACTIVE", "lab_left": {"mason": 15}},
	           "a_forge": {"ph_left": 10, "cost_left": 20, "yrs": 0.5, "spent": 5, "status": "ACTIVE"}},
	"done": {"__set__": ["fire", "stone_cutting"]}, "done_year": {"fire": "3", "stone_cutting": 10}, "failed_attempts": {"printing": "3", "alloy": 1},
	"businesses": [{"business_id": "founder", "owner_id": "", "plants": []}],
	}, ProjectsState)
check("deserialize_state: the retry counts are a default dict of integers that counts from zero",
      type(projects.failed_attempts) is collections.defaultdict and dict(projects.failed_attempts) == {"printing": 3, "alloy": 1}
      and projects.failed_attempts["never_tried"] == 0, projects.failed_attempts)
check("deserialize_state: active projects are rebuilt as records, in the saved order",
      list(projects.active) == ["z_mill", "a_forge"] and all(type(each) is ActiveProjectState for each in projects.active.values())
      and (projects.active["z_mill"].ph_left, projects.active["z_mill"].cost_left, projects.active["z_mill"].spent,
           projects.active["z_mill"].lab_left, projects.active["z_mill"].status) == (80.0, 300.0, 100.0, {"mason": 15.0}, "ACTIVE")
      and projects.active["a_forge"].lab_left is None, None)
check("deserialize_state: done is a set, years are integers", projects.done == {"fire", "stone_cutting"} and type(projects.done) is set
      and projects.done_year == {"fire": 3, "stone_cutting": 10}, None)
check("deserialize_state: the founder's business is a Business", projects.businesses == [Business(business_id="founder")], projects.businesses)
disclosures = deserialize_state({"disclosures": {"fire": {"mode": "license", "published_year": None, "licensees": {
	"firm:2": {"fee": 5.0, "royalty": 0.1, "year": 101}}}}}, DiffusionSeat).disclosures
check("deserialize_state: a disclosure record (an untyped dict) is as saved",
      disclosures == {"fire": {"mode": "license", "published_year": None,
                               "licensees": {"firm:2": {"fee": 5.0, "royalty": 0.1, "year": 101}}}}, disclosures)
check("deserialize_state: nested floats", deserialize_state({"tenure": {"mason": {"arch": 4.5}}}, ProductionSeat).tenure == {"mason": {"arch": 4.5}})

# ---- mine stock and tranches, shortages
mines = deserialize_state({
	"mines": [{"id": "m1", "ore": "iron", "capex": 500.0, "open": None}], "mine_pending": {"m2": 2}, "mine_ready": {"m1": 104},
	"mine_tranches": [["iron", 3, 2.5], ["tin", 1, 0.5]], "deposit_drawn": {"d1": 12}}, ResourcesSeat)
materials = deserialize_state({"shortages": {"charcoal": "3"}}, MaterialsSeat)
holdings = deserialize_state({
	"_material_stock_ledger": {"iron": 4.0}}, HoldingsState)
check("deserialize_state: mine stock keeps its entries and order, None inside", mines.mines == [{"id": "m1", "ore": "iron", "capex": 500.0, "open": None}]
      and mines.mine_pending == {"m2": 2.0} and mines.mine_ready == {"m1": 104}, None)
check("deserialize_state: mine tranches are the saved lists, in order", mines.mine_tranches == [["iron", 3, 2.5], ["tin", 1, 0.5]], mines.mine_tranches)
check("deserialize_state: tranches the save holds as None stay None", deserialize_state({"mine_tranches": None}, ResourcesSeat).mine_tranches is None)
check("deserialize_state: shortages are a counter of integers", type(materials.shortages) is collections.Counter and materials.shortages == {"charcoal": 3}, materials.shortages)
check("deserialize_state: underscore-led fields", holdings._material_stock_ledger == {"iron": 4.0}, None)
check("deserialize_state: a holdings blob with nothing in it is the defaults", deserialize_state({}, HoldingsState) == HoldingsState())

# ---- the economy's stored record, tile-keyed stores
from sim.markets.state import MarketsWorld
markets = deserialize_state({
	"agent_economy": {"opening": {"recipes": ["bread", "brick"]}, "record": {"loans": [{"contract_id": "l1"}]}, "cargo": {"leg:1": {"tonnes": 2.0}}},
	"market_flows": None}, MarketsWorld)
economy = deserialize_state({
	"works_under_construction": {"t1": {"mill": [105, 1]}},
	"nodes_money_per_labour_hour": None}, EconomyState)
check("deserialize_state: the stored agent economy (opening with its recipes, record, cargo) is as saved",
      markets.agent_economy == {"opening": {"recipes": ["bread", "brick"]}, "record": {"loans": [{"contract_id": "l1"}]}, "cargo": {"leg:1": {"tonnes": 2.0}}}, None)
check("deserialize_state: tile-keyed stores, with their numbers typed", economy.works_under_construction == {"t1": {"mill": [105.0, 1.0]}}, None)
check("deserialize_state: a module's world state types its nested numbers",
      deserialize_state({"trade_by_year": {"100": {"in": 4, "out": 3}}}, ForeignTradeWorld).trade_by_year == {"100": {"in": 4.0, "out": 3.0}})
check("deserialize_state: unset optional economy fields stay None", markets.market_flows is None and economy.nodes_money_per_labour_hour is None)

# ---- actors: contracts in the purses, the state's books
actors = deserialize_state({
	"records": {"government:rome": {"kind": "government", "money": 90.0, "revenue_by_form": {"tithe": 2.0}, "arrears": {"x": 1.5},
	                                "knowledge": {"__set__": ["iron", "writing"]}, "exited_year": None}},
	"home_country": "rome", "purses": {"book": EMPTY_BOOK, "offers": {}, "interest_pending": 0.0, "named_lenders": {}, "bonds": {},
	                                   "facilities": [{"contract_id": "f1", "lender": "bank", "borrower": "alpha", "currency": "engine_coin", "principal": 9.0, "kind": "facility"},
	                                                  {"contract_id": "f2", "lender": "bank", "borrower": "zeta", "currency": "engine_coin", "principal": 4.0, "kind": "facility", "arrears": 1.0, "issued_year": 3}]}},
	ActorsState)
record = actors.records["government:rome"]
check("deserialize_state: the state's books are an actor record with its set and its None",
      (record.kind, record.money, record.revenue_by_form, record.arrears, record.knowledge, record.exited_year)
      == ("government", 90.0, {"tithe": 2.0}, {"x": 1.5}, {"iron", "writing"}, None) and actors.home_country == "rome", None)
check("deserialize_state: facilities are loaded as contracts by borrower and lender, in the saved order",
      list(actors.purses.contracts.facilities) == ["alpha", "zeta"]
      and actors.purses.contracts.facilities["zeta"]["bank"] == Contract("f2", "bank", "zeta", "engine_coin", 4.0, kind=FACILITY, arrears=1.0, issued_year=3), None)

# ---- coded refusals
refusal = deserialize_state({"__refusal__": "unknown_seat", "text": "no such seat", "choices": ["a", "b"], "facts": {"seat": "x"}})
check("deserialize_state: a coded refusal is a Refusal with its code, choices and facts",
      isinstance(refusal, Refusal) and cause_of(refusal) == "unknown_seat" and refusal.choices == ["a", "b"] and refusal.facts == {"seat": "x"}, vars(refusal))

# ---- the root: seats in saved order, the acting seat's aliases, metadata
state = deserialize_state({
	"seats": {"zed": {"household": {"capital": 10.0}, "projects": {"done": {"__set__": ["fire"]}}, "founder": {"_founder_death_year": 30},
	                  "holdings": {"market_pressure": 3.0}, "goal": "steam_engine", "country": "han", "kind": "household", "holder": None},
	          "abe": {"household": {"capital": 4.0}, "projects": {}, "founder": None, "goal": None}},
	"acting_seat": "abe", "economy": {}, "scenario": {"year": 115}, "_civ": "rome", "_rng": [3, [0, 1], None], "_seed": "seed text",
	"stores": {"granary": {"t1|rome": 4.0}}, "interface": {"panel": "map"}}, SimulationState)
check("deserialize_state: seats come back in the saved order and as seats",
      list(state.seats) == ["zed", "abe"] and state.seats["zed"].goal == "steam_engine" and state.seats["zed"].country == "han"
      and state.seats["zed"].projects.done == {"fire"} and state.seats["zed"].founder._founder_death_year == 30
      and state.seats["zed"].holdings.market_pressure == 3.0 and state.seats["abe"].founder is None, None)
check("deserialize_state: the acting seat's objects are the root's household, projects and holdings",
      state.acting_seat == "abe" and state.household is state.seats["abe"].household and state.projects is state.seats["abe"].projects
      and state.holdings is state.seats["abe"].holdings and state.household.capital == 4.0, None)
check("deserialize_state: the metadata and the other sections", state._civ == "rome" and state._rng == [3, [0, 1], None] and state._seed == "seed text"
      and state.scenario.year == 115 and state.stores == {"granary": {"t1|rome": 4.0}} and state.interface == {"panel": "map"}, None)
