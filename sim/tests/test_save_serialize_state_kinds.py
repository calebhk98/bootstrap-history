"""`serialize_state` on written-out state, one kind of value per check, asserting the exact structure it returns.
The save detects fields itself (every dataclass field, bar aliases and `_on_change*` plumbing), so these cover the kinds
of value it handles rather than a list of fields: scalars and None, dicts with non-string keys, sets, nested records,
counters and default dicts, coded refusals, the contracts' purses, the seats and the economy's stored record. Order is
part of the claim: sets are written sorted, dicts in the order they hold, so a loaded collection comes back in saved order."""
QUICK_TOPIC = True

import collections
import dataclasses
import json

from sim.agents.api import ActorRecord, ActorsState
from sim.contracts import FACILITY, Contract
from sim.engine.economy import _InvalidatingSet
from sim.engine.state import (ActiveProjectState, EconomyState, FounderState, HoldingsState, HouseholdState, ProjectsState,
                              SimulationState, serialize_state, verbatim)
from sim.engine.state_seat import SeatState
from sim.invalidating import _InvalidatingDict
from sim.refusal import Refusal
from sim.tests.harness import check


def saved_field_names(cls):
	return [each.name for each in dataclasses.fields(cls) if not each.name.startswith("_on_change") and not each.metadata.get("alias")]


# ---- plain values
check("serialize_state: scalars and None are written as they are",
      [serialize_state(value) for value in (None, 3, 2.5, "text", True, False, 0)] == [None, 3, 2.5, "text", True, False, 0])
check("serialize_state: lists and tuples are lists, in order", serialize_state([3, (1, "b"), []]) == [3, [1, "b"], []])
check("serialize_state: a dict keeps its entries in the order it holds, not sorted",
      list(serialize_state({"z": 1, "a": 2, "m": 3})) == ["z", "a", "m"])
check("serialize_state: tuple, int and None keys become strings", serialize_state({(1, 2): "pair", 7: "seven", None: "never"}) == {"(1, 2)": "pair", "7": "seven", "None": "never"})
check("serialize_state: a dict's `_on_change` plumbing is not saved", serialize_state({"_on_change_hook": 1, "kept": 2}) == {"kept": 2})
check("serialize_state: an invalidating dict is a plain dict", serialize_state(_InvalidatingDict({"k": 1})) == {"k": 1})
check("serialize_state: a set is written sorted under __set__, whatever order it was built in",
      serialize_state({"carpenter", "mason", "baker"}) == {"__set__": ["baker", "carpenter", "mason"]})
check("serialize_state: an empty set is an empty __set__", serialize_state(set()) == {"__set__": []})
check("serialize_state: an invalidating set is written like a set", serialize_state(_InvalidatingSet({"b", "a"})) == {"__set__": ["a", "b"]})
check("serialize_state: a set of numbers is sorted numerically", serialize_state({10, 9, 100}) == {"__set__": [9, 10, 100]})
check("serialize_state: a counter is a dict of its counts", serialize_state(collections.Counter({"charcoal": 3})) == {"charcoal": 3})
check("serialize_state: a default dict is a dict of what it holds",
      serialize_state(collections.defaultdict(int, {"project": 2})) == {"project": 2})
check("serialize_state: a nested mix keeps each kind's own form",
      serialize_state({"a": {"b": [1, {"c"}]}}) == {"a": {"b": [1, {"__set__": ["c"]}]}})
check("serialize_state: a coded refusal keeps its code, text, choices and facts",
      serialize_state(Refusal("unknown_seat", "no such seat", choices=["a", "b"], seat="x"))
      == {"__refusal__": "unknown_seat", "text": "no such seat", "choices": ["a", "b"], "facts": {"seat": "x"}})

# ---- verbatim containers
plain_record = {"loans": [{"contract_id": "l1"}], "book": {"money": {}}}
with verbatim(plain_record):
	held_inside = serialize_state({"record": plain_record, "other": {"k": 1}})
	check("serialize_state: within `verbatim` the named container is handed back as the same object",
	      held_inside["record"] is plain_record and held_inside["other"] == {"k": 1} and held_inside["other"] is not None)
check("serialize_state: outside `verbatim` a dict is copied", serialize_state({"record": plain_record})["record"] is not plain_record)

# ---- dataclasses: the household (None-means-never fields, nested containers, tuples)
household = HouseholdState(capital=50.0, wages_earned=None, last_withdrawal=None, scandal_last_year=0.0,
                           trades_created={"mason", "baker"}, trade_introduced_year={"mason": 95}, employees={"mason": 2.0},
                           training=[["mason", 2]], log=[(100, "built a mill")], cash_flow={"wages": -12.5}, cash_mark=None,
                           cash_periods=[{"year": 99, "net": 3.0}], cause_mark={"wage": 1.0}, granted_staff=None,
                           unused_hours_reported={"order:1": [40.0, "no_hands"]}, last_settlement=-999)
blob = serialize_state(household)
check("serialize_state: a dataclass is a dict of its fields in declaration order", list(blob) == saved_field_names(HouseholdState), list(blob)[:5])
check("serialize_state: None-means-never fields stay None, and a zero stays zero",
      blob["wages_earned"] is None and blob["last_withdrawal"] is None and blob["cash_mark"] is None and blob["granted_staff"] is None
      and blob["scandal_last_year"] == 0.0 and blob["last_settlement"] == -999, None)
check("serialize_state: a dataclass's sets, dicts, lists and tuples inside",
      blob["trades_created"] == {"__set__": ["baker", "mason"]} and blob["trade_introduced_year"] == {"mason": 95}
      and blob["employees"] == {"mason": 2.0} and blob["training"] == [["mason", 2]] and blob["log"] == [[100, "built a mill"]]
      and blob["cash_flow"] == {"wages": -12.5} and blob["cash_periods"] == [{"year": 99, "net": 3.0}]
      and blob["cause_mark"] == {"wage": 1.0} and blob["unused_hours_reported"] == {"order:1": [40.0, "no_hands"]}, None)
check("serialize_state: the household's purse (a property, not a field) is saved as `capital` through the property", blob["capital"] == 50.0, blob["capital"])
check("serialize_state: the household's own purse links are not saved", "_purses" not in blob and "_account" not in blob and "_local_capital" not in blob)

# ---- nested records and retry counts
retries = collections.defaultdict(int, {"printing": 3, "alloy": 1})
projects = ProjectsState(
	active={"z_mill": ActiveProjectState(ph_left=80.0, cost_left=300.0, yrs=1.5, spent=100.0, lab_left={"mason": 15.0}),
	        "a_forge": ActiveProjectState(ph_left=10.0, cost_left=20.0, yrs=0.5, spent=5.0)},
	done={"stone_cutting", "fire"}, done_year={"fire": 3, "stone_cutting": 10}, failed_attempts=retries,
	disclosures={"fire": {"mode": "license", "published_year": None, "licensees": {"firm:2": {"fee": 5.0, "royalty": 0.1, "year": 101}}}},
	tenure={"mason": {"arch": 4.5}}, excluded={"category:war"})
blob = serialize_state(projects)
check("serialize_state: the retry counts are a dict of integers", blob["failed_attempts"] == {"printing": 3, "alloy": 1})
check("serialize_state: active projects are records, written in the order they were started",
      list(blob["active"]) == ["z_mill", "a_forge"] and blob["active"]["z_mill"] == {
		"ph_left": 80.0, "yrs": 1.5, "spent": 100.0, "cost_left": 300.0, "status": "ACTIVE", "lab_left": {"mason": 15.0}}, blob["active"])
check("serialize_state: done nodes are a sorted set and their years a dict",
      blob["done"] == {"__set__": ["fire", "stone_cutting"]} and blob["done_year"] == {"fire": 3, "stone_cutting": 10}, None)
check("serialize_state: a disclosure record keeps its None and its nested licensee",
      blob["disclosures"] == {"fire": {"mode": "license", "published_year": None,
                                      "licensees": {"firm:2": {"fee": 5.0, "royalty": 0.1, "year": 101}}}}, blob["disclosures"])
check("serialize_state: the founder's business is a nested record", blob["businesses"] == [{"business_id": "founder", "owner_id": "", "plants": []}], blob["businesses"])
check("serialize_state: nested dicts of floats and sets of exclusions", blob["tenure"] == {"mason": {"arch": 4.5}} and blob["excluded"] == {"__set__": ["category:war"]}, None)
check("serialize_state: the project fields come in declaration order", list(blob) == saved_field_names(ProjectsState))

# ---- mine stock and tranches, held goods, offers
holdings = HoldingsState(
	mines=[{"id": "m1", "ore": "iron", "capex": 500.0, "open": None}], mine_pending={"m2": 2.0}, mine_ready={"m1": 104},
	mine_cost_paid=500.0, mine_tranches=[["iron", 3, 2.5], ["tin", 1, 0.5]], deposits_found=[{"id": "d1", "tile": "t1"}],
	deposit_drawn={"d1": 12.0}, shortages=collections.Counter({"charcoal": 3}), binding=None, forest_ha=120.0,
	_material_stock_ledger={"iron": 4.0}, patents={"loom": {"granted": 1, "expires": 20, "licensees": ["firm:2"]}},
	shares_held={"guild": 0.1}, offers=[{"id": "x#1", "from": "x", "to": "y", "give": {}, "take": {}, "expires": 9}], offer_serial=1)
blob = serialize_state(holdings)
check("serialize_state: mine stock, in the order the mines were opened, with None inside",
      blob["mines"] == [{"id": "m1", "ore": "iron", "capex": 500.0, "open": None}] and blob["mine_pending"] == {"m2": 2.0}
      and blob["mine_ready"] == {"m1": 104} and blob["mine_cost_paid"] == 500.0, None)
check("serialize_state: mine tranches are lists in the order held", blob["mine_tranches"] == [["iron", 3, 2.5], ["tin", 1, 0.5]], blob["mine_tranches"])
check("serialize_state: a tranche list that is None means none (never an empty list)", serialize_state(HoldingsState())["mine_tranches"] is None)
check("serialize_state: found deposits, shortages, patents, shares and offers",
      blob["deposits_found"] == [{"id": "d1", "tile": "t1"}] and blob["deposit_drawn"] == {"d1": 12.0} and blob["shortages"] == {"charcoal": 3}
      and blob["patents"] == {"loom": {"granted": 1, "expires": 20, "licensees": ["firm:2"]}} and blob["shares_held"] == {"guild": 0.1}
      and blob["offers"] == [{"id": "x#1", "from": "x", "to": "y", "give": {}, "take": {}, "expires": 9}] and blob["offer_serial"] == 1, None)
check("serialize_state: underscore-led fields that are not `_on_change` plumbing are saved", blob["_material_stock_ledger"] == {"iron": 4.0})

# ---- the economy's stored record, with its held stock and late recipes
record = {"book": {"goods": {"iron": {"t1": 4.0}}}, "loans": [{"contract_id": "l1", "principal": 40.0, "kind": "term_loan"}]}
economy = EconomyState(
	agent_economy={"opening": {"recipes": ["bread", "brick"], "prices": {"bread": 1.5}}, "record": record, "cargo": {"leg:1": {"tile": "t1", "tonnes": 2.0}}},
	tile_owners={"t1": {"owner": "rome", "control": "high"}}, works={"t1": {"mill": 2.0}}, works_under_construction={"t1": {"mill": [105, 1.0]}},
	forest_felled={"t1": 3.5}, market_flows=None, nodes_money_per_labour_hour=None, foreign_trade_by_year={"100": {"in": 4.0, "out": 3.0}})
with verbatim(record):
	blob = serialize_state(economy)
check("serialize_state: the stored agent economy keeps its opening (the late recipes), record and cargo",
      blob["agent_economy"]["opening"] == {"recipes": ["bread", "brick"], "prices": {"bread": 1.5}}
      and blob["agent_economy"]["cargo"] == {"leg:1": {"tile": "t1", "tonnes": 2.0}}, blob["agent_economy"])
check("serialize_state: the stored record (its held stock and loans) is written as it is, untouched",
      blob["agent_economy"]["record"] is record and record["loans"][0]["principal"] == 40.0, None)
check("serialize_state: tile-keyed economy stores", blob["tile_owners"] == {"t1": {"owner": "rome", "control": "high"}}
      and blob["works"] == {"t1": {"mill": 2.0}} and blob["works_under_construction"] == {"t1": {"mill": [105, 1.0]}}
      and blob["forest_felled"] == {"t1": 3.5}, None)
check("serialize_state: an unset optional economy field is None", blob["market_flows"] is None and blob["nodes_money_per_labour_hour"] is None)
check("serialize_state: the economy's fields come in declaration order", list(blob) == saved_field_names(EconomyState))

# ---- actors: the contracts in the purses and the state's books
actors = ActorsState(home_country="rome")
actors.purses.contracts.facilities["zeta"] = {"bank": Contract("f2", "bank", "zeta", "engine_coin", 4.0, kind=FACILITY, arrears=1.0, issued_year=3)}
actors.purses.contracts.facilities["alpha"] = {"bank": Contract("f1", "bank", "alpha", "engine_coin", 9.0, kind=FACILITY)}
actors.records["government:rome"] = ActorRecord(kind="government", money=90.0, revenue_by_form={"tithe": 2.0}, arrears={"x": 1.5},
                                                knowledge={"writing", "iron"}, exited_year=None)
blob = serialize_state(actors)
check("serialize_state: facilities are written sorted by borrower however they were made",
      [row["contract_id"] for row in blob["purses"]["facilities"]] == ["f1", "f2"], blob["purses"]["facilities"])
check("serialize_state: a facility's arrears and issue year are kept",
      blob["purses"]["facilities"][1]["arrears"] == 1.0 and blob["purses"]["facilities"][1]["issued_year"] == 3
      and blob["purses"]["facilities"][1]["kind"] == FACILITY, None)
check("serialize_state: the state's books: money, revenue by form, arrears, knowledge and a None-means-never year",
      blob["records"]["government:rome"]["money"] == 90.0 and blob["records"]["government:rome"]["revenue_by_form"] == {"tithe": 2.0}
      and blob["records"]["government:rome"]["arrears"] == {"x": 1.5}
      and blob["records"]["government:rome"]["knowledge"] == {"__set__": ["iron", "writing"]}
      and blob["records"]["government:rome"]["exited_year"] is None and blob["home_country"] == "rome", None)

# ---- the root: seats, aliases and metadata
first = SeatState(HouseholdState(capital=10.0), ProjectsState(done={"fire"}), FounderState(life_left=30.0), goal="steam_engine", country="han")
second = SeatState(HouseholdState(capital=4.0), ProjectsState(), FounderState(), holdings=HoldingsState(forest_ha=1.0))
state = SimulationState(seats={"zed": first, "abe": second}, acting_seat="abe", economy=EconomyState(), _civ="rome", _rng=[3, [0, 1], None],
                        _seed="seed text", stores={"granary": {"t1|rome": 4.0}})
blob = serialize_state(state)
check("serialize_state: the root's aliases of the acting seat are not saved, the seats are", all(
	name not in blob for name in ("household", "projects", "founder", "governance", "holdings", "seat_progress")) and "seats" in blob, list(blob))
check("serialize_state: seats are saved in the order they joined, with the acting seat's id", list(blob["seats"]) == ["zed", "abe"] and blob["acting_seat"] == "abe")
check("serialize_state: a seat's own fields: goal, country, kind and holder",
      blob["seats"]["zed"]["goal"] == "steam_engine" and blob["seats"]["zed"]["country"] == "han"
      and blob["seats"]["zed"]["kind"] == "household" and blob["seats"]["zed"]["holder"] is None and blob["seats"]["abe"]["goal"] is None, None)
check("serialize_state: a seat's household, projects and founder are sections of it",
      blob["seats"]["zed"]["household"]["capital"] == 10.0 and blob["seats"]["zed"]["projects"]["done"] == {"__set__": ["fire"]}
      and blob["seats"]["zed"]["founder"]["life_left"] == 30.0 and blob["seats"]["abe"]["holdings"]["forest_ha"] == 1.0, None)
check("serialize_state: the metadata the load needs", blob["_civ"] == "rome" and blob["_rng"] == [3, [0, 1], None] and blob["_seed"] == "seed text"
      and blob["_fog"] is False and blob["_immortal"] is True and blob["_game_version"] is None, None)
check("serialize_state: the declared stores and the UI's own memory", blob["stores"] == {"granary": {"t1|rome": 4.0}} and blob["interface"] == {})
check("serialize_state: the whole state is JSON text", json.loads(json.dumps(blob)) == blob)
