"""The materials module built for a test, with plain values for the views it reads (sim/tests/module_harness.py).

    module = materials_stand_in.build(tree_nodes={"furnace": {...}}, goods_stock=lambda commodity: 5.0)
    module.project_material_bill("furnace")            # a method of the module, called directly
    materials_stand_in.sent(module, ChangeStock)        # the commands of one class it sent, in order

Every default is the empty world: no tree, nothing held, nothing for sale, every factor one. A test overrides the views
it is about."""
import collections
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from sim.geography import api as geography
from sim.ledger.api import rules as ledger_rules
from sim.materials.module import Materials
from sim.materials.state import MaterialsSeat
from sim.tests import module_harness


def projects(done: Any = (), active: Optional[Dict[str, Any]] = None) -> Any:
    """A seat's projects as the module reads them: what is done, what is active (by id)."""
    active = dict(active or {})
    return SimpleNamespace(done=set(done), active=active, active_keys_sorted=lambda: sorted(active))


def build(seat: Optional[MaterialsSeat] = None, views: Optional[Dict[str, Any]] = None, answers: Optional[Dict[type, Any]] = None,
          **overrides: Any) -> Materials:
    """A Materials module whose reads are plain values; keyword arguments (or `views`) override a view by name."""
    plain: Dict[str, Any] = {
        "year": 100, "civilisation": {}, "legacy_world_map": geography.open_map(), "tree": lambda node_id: None,
        "tree_nodes": {}, "techniques_held": set(), "visibility": lambda node_id, memo=None: True,
        "hard_prerequisites": lambda node_id: [], "projects_record": projects(), "active_projects_version": 0, "techniques_version": 0,
        "operating": set(), "default_population": 65e6, "pop_scale": 1.0, "empire_output": {},
        "mechanic": collections.defaultdict(dict), "effect_best": lambda channel: None, "running_stamp": (None, (), None),
        "running": lambda node_id: False, "goods_stock": lambda commodity: 0.0,
        "held_goods": ledger_rules.StockLedger(), "goods_stock_opening": {}, "goods_quote": lambda material: None,
        "can_be_bought": lambda material: False,
        "purchase_quote": lambda material, tonnes, already=0.0: None if tonnes < 0 else (tonnes, 1.0),
        "partner_import": lambda material: (None, None), "agent_producer_capacity": lambda material: None,
        "material_freight_factor": lambda commodity: 1.0, "material_prices": {}, "material_commodity_map": {},
        "commodity_record": lambda commodity: {}, "commodity_country_output": lambda commodity: 0.0,
        "price_epoch": (), "producers_stamp": (), "foreign_supply_tonnes": lambda partner, material: 0.0,
        "mine_capacity": {}, "mine_depletion": lambda material: 1.0, "forest_hectares": 0.0,
        "nitre_beds": {"square_metres": 0.0, "tonnes_per_square_metre": 0.0}, "found_deposits": lambda material: [],
        "mine_works_materials": (), "shortage_remedy_plan": lambda binding, shortfall=None: {"text": "buy some"},
        "mineral_scale": lambda material: 1.0, "material_cost_factor": lambda node_id: 1.0,
        "project_cost": lambda node_id: 100.0, "project_cost_now": lambda node_id: 100.0,
        "opposition_factor": lambda node_id: 1.0, "cost_money_factor": 1.0, "rebuild_work_factor": lambda node_id: 1.0,
        "failure_reset_share": 0.4, "shared_bill": lambda node_id, compute: compute(),
        "civ_cost_factor": lambda node_id: 1.0, "can_pay": lambda cost: True,
        "purchase_refusal": lambda what, cost: ("refused", what, cost)}
    plain.update(views or {})
    plain.update(overrides)
    record = plain.pop("legacy_projects", None) or plain.pop("projects_record")   # a test gives its projects as one record
    plain.pop("projects_record", None)
    plain.setdefault("active_projects", record.active)
    plain.setdefault("active_project_ids", record.active_keys_sorted)
    if "techniques_held" not in (views or {}) and "techniques_held" not in overrides:
        plain["techniques_held"] = record.done   # the held set a test gives with its projects
    return module_harness.build(Materials, views=plain, answers=answers, seat=seat or MaterialsSeat(), module_id="materials")


def sent(module: Materials, kind: type) -> List[Any]:
    """The commands of one class the module sent, in order."""
    return [command for command in module_harness.sent(module) if isinstance(command, kind)]
