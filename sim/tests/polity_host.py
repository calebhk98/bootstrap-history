"""The polity module for a test: built with `module_harness`, every view it reads answering a quiet default unless the test gives
its own.

    module = polity_host.build(seat=PolitySeat(reputation=98.0), danger_lines={"eminence": 30.0, "suspicion": 80.0})
    module.eminence_report()

A view given as a plain value is that value; as a function it is called with the view's arguments; a keyed view is a dict or a
function of the key. Defaults are the quiet answers: no work built, an empty purse, a state that reaches everyone, nothing
organised against the household. The commands the module sent are in `module_harness.sent(module)`. Dice are `random.Random`."""
import random
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, Dict, Optional

from sim.ledger.api import TakeFromHouseholdPurse
from sim.polity.module import Polity
from sim.polity.state import PolitySeat, PolityWorld
from sim.tests import module_harness

VALUE_WEIGHTS = {"w_magic_fear": 0.5, "w_religious_rigidity": 0.5, "w_labour_saving": 0.0, "w_novelty": 0.0, "w_military": 0.0,
                 "w_information": 0.0, "w_commerce": 0.0, "patronage_weight": 1.0, "bribability": 0.5, "adaptation_rate": 0.1}


@contextmanager
def _same_seat(seat_id):
	yield


def _government(unfunded: Optional[Dict[str, float]] = None):
	record = SimpleNamespace(unfunded=unfunded or {}, levy_requisition_rate=0.0, levy_office_rate=0.0)
	return SimpleNamespace(record=record, debt=lambda: 0.0, military_ask=lambda taxable, scale, world: 0.0)


def defaults(seed: int) -> Dict[str, Any]:
	world = SimpleNamespace(government=lambda: _government(), collectible_share=lambda: 1.0, order_share=lambda: 1.0,
	                        inspection_share=lambda: 1.0, forest_share=lambda: 1.0)
	return {
		"year": 100, "civilisation": {"id": "rome", "starting_tax_share": 0.1}, "events_enabled": True,
		"automation": {"manual": False, "bounty_set": set()}, "acting_seat": "founder",
		"danger_lines": {"eminence": 100.0, "suspicion": 100.0}, "legacy_dice": random.Random(seed), "legacy_said_once": set(),
		"legacy_game": SimpleNamespace(), "wealth_claims": lambda: [],
		"legacy_act_as": _same_seat, "money_text": lambda amount, grouped=False, short=False: "%d money" % round(amount),
		"mass_text": lambda amount, digits=0, grouped=False, short=False, unit="tonne": "%.1f %s" % (amount, unit),
		"state_treasury": _government(), "cast": SimpleNamespace(home_actors=lambda kind: [],
		                                                                        prohibitions=lambda: {}),
		"cast_state": None, "actor_world": world, "country_world": lambda owner: world,
		"acting_balance": 0.0, "legacy_acting_household": SimpleNamespace(capital=0.0),
		"legacy_household_actor": SimpleNamespace(), "transfer_listening": _same_seat,
		"effect_sum": lambda channel, start=0.0: start, "effect_values": lambda channel: [],
		"effect_factor": lambda channel, start=1.0, exponent=None: start, "effect_best": lambda channel: None,
		"running_mechanics": lambda name: [], "mechanic": lambda name: {}, "patrons_lost_to_eminence": [],
		"techniques_held": set(), "techniques_granted": set(), "tree": lambda node_id: None, "tree_nodes": {},
		"running": lambda node_id: False, "revenue_estimate": 0.0, "concern_revenue": lambda node_id: 0.0, "operating": set(),
		"standing_floor": 0.0, "rep_factor": 1.0, "legacy_done_versions": (0, 0),
		"headcount": 0.0, "base_annual_wage": lambda trade: 1.0, "labour_state_weights": {}, "money_per_labour_hour": 1.0,
		"seat_list": {"joined": ["founder"], "playing": ["founder"]}, "legacy_seats": {}, "founder": {"alive": True, "policy": {}},
		"population_total": 1.0e6, "pop_scale": 1.0, "material_pool": lambda material: (material,),
		"material_substitutes": lambda material: frozenset(), "real_output_per_head": 1.0, "output_factor": 1.0,
	}


def build(seed: int = 1, answers: Optional[Dict[type, Any]] = None, seat: Optional[PolitySeat] = None,
          value_weights: Optional[Dict[str, float]] = None, **views: Any) -> Polity:
	"""The module with `views` over the quiet defaults, a fresh seat unless given, and `answers`, the replies of owners to
	commands keyed by command class; `value_weights` is the society's, held as given (the defaults when not given)."""
	every_view = defaults(seed)
	every_view.update(views)
	return module_harness.build(Polity, views=every_view, answers=answers, world=PolityWorld(dict(VALUE_WEIGHTS) if value_weights is None else value_weights),
	                            seat=seat or PolitySeat(), module_id="polity")


def takes_from_purse(purse: Any, treasury: Any) -> Dict[type, Any]:
	"""The ledger's answer to `TakeFromHouseholdPurse` over a stand-in purse and treasury: the purse is debited and the
	treasury credited, as the ledger does it (the ledger's own test is test_ledger_commands)."""
	def take(command: Any) -> None:
		purse.debit(command.amount, command.purpose)
		treasury.credit(command.amount, command.purpose)
	return {TakeFromHouseholdPurse: take}


def shifting(weights: Dict[str, float]):
	"""The answer the polity module gives `ShiftValueWeight` over this live dict of the society's value weights."""
	return build(value_weights=weights).shift_value_weight
