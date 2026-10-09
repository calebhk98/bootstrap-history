"""The UI's one door into the engine: every engine name sim/ui/ uses is re-exported here by
explicit name, and each private `Sim` member the UI reads or writes has a public function that
delegates exactly. sim/ui/ imports nothing from sim.engine except this module."""
from sim.engine import (  # noqa: F401
    automation_audit, cash_book, category_traits, cause_book, civ_start_check, fuzzy_estimates, path_search, planner,
    purchase_rule, settings, settings_table, shortage_conditions, topic_tags, tree_merge, units,
    validate_material_gating, validate_output_bounds, validate_copy_visibility, validate_production, validate_unheld_gates)
from sim.engine.blockers import BLOCKER_MEANING, RUNNING_CONSTRAINT_KIND  # noqa: F401
from sim.engine.catalog import load_production_catalog  # noqa: F401
from sim.engine.core import Sim  # noqa: F401
from sim.engine.critical_path_remaining import active_years_left, remaining_critical_path_years  # noqa: F401
from sim.engine.data import (  # noqa: F401
    CIVDIR, civilization_ids, closure, critical_path, DEFAULTS, downstream_count, goal_catalog,
    hard_pre, is_downstream, KNOWLEDGE_DIR, load, load_civ, load_geography, MODDIR, money_short,
    money_unit_note, money_word, resolve_goal, ROOT, selectable_goals, STARTING_KITS, STRATS,
    topo_order, trade_family, TRADE_FAMILY, TRADE_NOTES, TRADES_ABSENT, WAGES,
    win_condition_describe)
from sim.engine.default_civilisation import default_civilisation_id  # noqa: F401
from sim.engine.fog import strip_self_play_advice  # noqa: F401
from sim.engine.hazard_window import hazards_not_yet_past  # noqa: F401
from sim.engine.identity_cache import IdentityCache  # noqa: F401
from sim.engine.mods import get_ordered_mods  # noqa: F401
from sim.engine.knowledge_warning import knowledge_loss_warning, warning_lines  # noqa: F401
from sim.engine.permanent_benefit import permanent_parts  # noqa: F401
from sim.engine.projects_completion import FAILED_PREFIX, goal_movement, MINOR_MARK  # noqa: F401
from sim.engine.projects_exclusions import CATEGORY_PREFIX, TRAIT_PREFIX  # noqa: F401
from sim.engine.purchase_rule import purchase_budget  # noqa: F401
from sim.engine.run_setup import DetRNG, ensure_fixed_hash_seed, load_strategy, topo_stable  # noqa: F401
from sim.engine.saveload import (  # noqa: F401
    _SET_FIELDS_OF_NODE_IDS as SET_FIELDS_OF_NODE_IDS,
    _SET_FIELDS_OF_TRADE_NAMES as SET_FIELDS_OF_TRADE_NAMES, _validate_save as validate_save,
    civ_of_save, goal_of_save, load_state, REQUIRED_SAVE_FIELDS, SAVE_FIELDS, save_state)
from sim.engine.settings_table import normal_seed, valid_seed_text  # noqa: F401
from sim.engine.shortage_conditions import condition_line  # noqa: F401
from sim.engine.units_summary import summary_line  # noqa: F401
from sim.engine.ui_data import load_figure_specs  # noqa: F401
from sim.engine.readable import is_readable  # noqa: F401


def interface_memory(sim):
    """The slot of the save the UI owns; the engine never reads it."""
    return sim.state.interface


def set_interface_memory(sim, memory):
    sim.state.interface = memory


# Engine reads: private methods and fields of the `Sim`, under public names.

def material_prices(sim):
    return sim._material_prices()


def commodity_ledger(sim):
    return sim._commodity_ledger()


def material_stock(sim):
    return sim._material_stock()


def goods_category_ratios(sim, category):
    return sim._goods_category_ratios(category)


def own_production_tags(sim):
    return sim._own_production_tags()


def own_material_supply(sim, tag):
    return sim._own_material_supply(tag)


def demand_by_supply_tag(sim, demand):
    return sim._demand_by_supply_tag(demand)


def material_market_tonnes(sim, material):
    return sim._material_market_tonnes(material)


def material_tag(sim, material):
    return sim._material_tag(material)


def electricity_demand_kw(sim):
    return sim._electricity_demand_kw()


def disease_burden(sim):
    return sim._disease_burden()


def last_demographic_step(sim):
    return sim._last_demographic_step


def effect_terms(sim, effect):
    return sim._effect_terms(effect)


def schooling_flow(sim):
    return sim._schooling_flow()


def practice_set(sim):
    return sim._practice_set()


def visible_to_player(sim, node_id):
    return sim._visible_to_player(node_id)


def tech_effects(sim):
    return sim._tech_effects


def settings_meta_path(path):
    return settings._meta_path(path)


# Memory the UI keeps on the `Sim`: saved or read by the engine, so it stays there.

def dashboard_history(sim):
    return getattr(sim, "_dashboard_history", None)


def set_dashboard_history(sim, history):
    sim._dashboard_history = history


def founder_death_aged(sim):
    return getattr(sim, "_founder_death_aged", None)


def founder_death_year(sim):
    return getattr(sim, "_founder_death_year", None)


def set_founder_death(sim, aged, year):
    sim._founder_death_aged, sim._founder_death_year = aged, year


def founder_death_cache(sim):
    return getattr(sim, "_founder_death_cache", None)


def set_founder_death_cache(sim, cache):
    sim._founder_death_cache = cache


def goal_closure(sim):
    return getattr(sim, "_goal_closure", None)


def set_goal_closure(sim, closure_set):
    sim._goal_closure = closure_set


def goal_years(sim):
    return dict(sim.state.seat_progress.goal_years)


def set_goal(sim, node_id):
    sim.set_goal(node_id)


def win_condition_anatomy(sim, condition):
    return sim.win_condition_anatomy(condition)


def goal_critical_floor(sim):
    return getattr(sim, "_goal_critical_floor", None)


def set_goal_critical_floor(sim, years):
    sim._goal_critical_floor = years


def last_buy_refusal(sim):
    return getattr(sim, "_last_buy_refusal", None)


def set_last_buy_refusal(sim, refusal):
    sim._last_buy_refusal = refusal


def said_command_index(sim):
    return getattr(sim, "_said_command_index", False)


def set_said_command_index(sim, said):
    sim._said_command_index = said


def said_stack_caution(sim):
    return getattr(sim, "_said_stack_caution", False)


def set_said_stack_caution(sim, said):
    sim._said_stack_caution = said


def said_parallelism(sim):
    return sim._said_parallelism


def set_said_parallelism(sim, said):
    sim._said_parallelism = said


def said_explanations(seat_progress):
    return seat_progress._said_explanations


def set_said_explanations(seat_progress, said):
    seat_progress._said_explanations = said
