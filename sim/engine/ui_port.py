"""The UI's one door into the engine: every engine name sim/ui/ uses is re-exported here by
explicit name, and each private `Sim` member the UI reads or writes has a public function that
delegates exactly. sim/ui/ imports nothing from sim.engine except this module.

The game itself is read as `sim.view(name)` (a published view of its owner module) and changed as
`sim.send(ui_port.<Command>(...))`; the commands the UI sends are re-exported below, and the views it reads
are listed by `python3 tools/check_ui_views.py --list`, which also checks each is published. What is left
as a function here is the new-game setup, the UI's own memory on the `Sim`, and the engine tables that
no module publishes yet."""
from sim.engine import (  # noqa: F401
    state_paths, civ_start_check, fuzzy_estimates, path_search, planner,
    purchase_rule, settings, settings_table, topic_tags, units,
    validate_material_gating, validate_node_money, validate_copy_visibility, validate_production, validate_unheld_gates, validate_running_gates, validate_defence_stores)
from sim.production.api import node_revenue_census  # noqa: F401
from sim.engine.blockers import BLOCKER_MEANING, RUNNING_CONSTRAINT_KIND  # noqa: F401
from sim.content.api import build_tree, foreign_economy_document, load_production_catalog, merge_problems  # noqa: F401
from sim.engine.core import Sim  # noqa: F401
from sim.engine.critical_path_remaining import active_years_left, remaining_critical_path_years  # noqa: F401
from sim.engine.data import (  # noqa: F401
    CIVDIR, civilization_ids, DEFAULTS, downstream_count, goal_catalog,
    is_downstream, KNOWLEDGE_DIR, load, load_civ, node_names, load_geography, MODDIR, money_short,
    money_unit_note, money_word, resolve_goal, ROOT, selectable_goals, STARTING_KITS, STRATS,
    trade_family, TRADE_FAMILY, TRADE_NOTES, TRADES_ABSENT, WAGES,
    win_condition_describe)
from sim.engine.default_civilisation import default_civilisation_id  # noqa: F401
from sim.knowledge.api import check_category_traits, closure, critical_path, hard_pre, prerequisite_names, strip_self_play_advice, topo_order  # noqa: F401
from sim.engine.mod_code import code_report, run_mod_code  # noqa: F401
from sim.engine.game_assembly import build as build_assembly  # noqa: F401
from sim.engine.mod_code import allow as allow_mod_code  # noqa: F401
from sim.hazards.api import hazards_not_yet_past  # noqa: F401
from sim.prices.api import identity_cache, shared_ledger  # noqa: F401
IdentityCache = identity_cache.IdentityCache  # noqa: F401
from sim.labour.api import format_occupational_report, hours_by_trade_of_all_employers, occupational_report, people_by_trade_of_all_employers  # noqa: F401
from sim.engine.knowledge_warning import knowledge_loss_warning, warning_lines  # noqa: F401
from sim.projects.api import FAILED_PREFIX, MINOR_MARK, goal_movement, oversubscription_notes, permanent_parts  # noqa: F401
from sim.projects.api import exclusion_rules
CATEGORY_PREFIX, TRAIT_PREFIX = exclusion_rules.CATEGORY_PREFIX, exclusion_rules.TRAIT_PREFIX
from sim.engine.purchase_rule import purchase_budget  # noqa: F401
from sim.engine.run_setup import DetRNG, ensure_fixed_hash_seed, load_strategy, topo_stable  # noqa: F401
from sim.engine.saveload import (  # noqa: F401
    _SET_FIELDS_OF_NODE_IDS as SET_FIELDS_OF_NODE_IDS,
    _SET_FIELDS_OF_TRADE_NAMES as SET_FIELDS_OF_TRADE_NAMES, _validate_save as validate_save,
    civ_of_save, EconomyNotOpened, goal_of_save, load_state, REQUIRED_SAVE_FIELDS, SAVE_FIELDS, save_state)
from sim.engine.save_companions import save_session  # noqa: F401
from sim.engine.settings_table import normal_seed, valid_seed_text  # noqa: F401
from sim.projects.api import funding as project_funding
paid_credit = project_funding.paid_credit
from sim.materials.api import rules as materials_rules
condition_line = materials_rules.condition_line
material_words = materials_rules.material_words
from sim.engine.units_summary import summary_line  # noqa: F401
from sim.engine.units import tagged  # noqa: F401
from sim.engine.units_prose import area_text, mass_per_area_text, mass_rate_text, mass_text, money_text, plain_number  # noqa: F401
from sim.engine.readable import is_readable  # noqa: F401


from sim.projects.api import constants as project_constants  # noqa: F401
from sim.polity.api import constants as polity_constants  # noqa: F401

# Commands the UI sends (`sim.send(ui_port.<Command>(...))`); each is its owner's.
from sim.campaigns.api import DisbandArmy, OrderArmy, RaiseArmy, RecallArmy  # noqa: F401
from sim.diffusion.api import Disclose  # noqa: F401
from sim.finance.api import FoundBank  # noqa: F401
from sim.ledger.api import CloseCashPeriod  # noqa: F401
from sim.reporting.api import NOTICE, WAGE, CloseCausePeriod  # noqa: F401
from sim.agriculture.api import InvestFarm, SellFarm  # noqa: F401
from sim.land.api import BuildWay, FoundColony  # noqa: F401
from sim.markets.api import BuyMaterial, SellMaterial  # noqa: F401
from sim.polity.api import SettleWithState, WithdrawFromPublicLife  # noqa: F401
from sim.projects.api import (Bribe, MothballWork, PostBounty, ReorderProjects, RestoreProjectOrder, RestoreWork,  # noqa: F401
                              StartProject, StopProject)  # noqa: F401
from sim.knowledge.api import RevealNodes, StartDoneYearRecord  # noqa: F401
from sim.scenario.api import SetEndYear, SetFog, SetFuzzyEstimates  # noqa: F401
from sim.seats.api import AnswerOffer, ApplyForPatent, EndRun, HandOverSeat, JoinSeat, MakeOffer, RememberGoalClosure, RememberGoalFloor, SetGoal, SetPolicy  # noqa: F401
from sim.ventures.api import OpenVenture, RollOut, SellConcern  # noqa: F401
from sim.workforce.api import (BuildHousing, BuySlaves, CommissionHours, FireStaff, FoundTradeSchool, HireStaff, Manumit, MoveBase,  # noqa: F401
                               NoteBuyRefusal, TrainStaff, WorkForWages)


# A new game's options, set once by the command line or the options screen before the first step.

def begin_game(sim, goal, end_year, fog, fuzzy_estimates):
    sim.send(SetGoal(goal))
    sim.send(StartDoneYearRecord())
    sim.send(SetEndYear(end_year))
    sim.send(SetFog(bool(fog)))
    set_fuzzy_estimates(sim, fuzzy_estimates)


def reset_done_years(sim):
    sim.send(StartDoneYearRecord())


def set_end_year(sim, year):
    sim.send(SetEndYear(year))


def set_fuzzy_estimates(sim, on):
    """Show the needs of unfinished work as estimates; the blur's salt is drawn the first time it is turned on."""
    salt = sim.rng.getrandbits(30) + 1 if on and not sim.view("fuzzy_salt")() else None
    sim.send(SetFuzzyEstimates(bool(on), salt))


def seat_progress(sim):
    """The acting seat's interface record (dashboard cap, last score, explanations said), saved with the seat."""
    return sim.state.acting_record.seat_progress


def saving_book(sim):
    """The acting seat's household record of the project it is saving for (`saving_for`, `saving_target`)."""
    return sim.state.acting_record.household


def state_path_declared(name):
    return state_paths.declared(name)


def state_path_root(sim, name):
    return state_paths.root_value(sim, name)


def interface_memory(sim):
    """The slot of the save the UI owns; the engine never reads it."""
    return sim.state.interface


def set_interface_memory(sim, memory):
    sim.state.interface = memory


# Engine reads: private methods and fields of the `Sim`, under public names.

def material_prices(sim):
    """Every material someone in reach sells, at the price households are asked."""
    return sim.view("household_prices")()


def commodity_ledger(sim):
    return shared_ledger()


def material_stock(sim):
    return sim.view("held_goods")()


def goods_category_ratios(sim, category):
    return sim.view("goods_category_ratios")(category, 0)


def own_production_tags(sim):
    return sim.view("own_production_tags")()


def own_material_supply(sim, tag):
    return sim.view("material_own_supply")[tag]


def demand_by_supply_tag(sim, demand):
    return sim.view("demand_by_supply_tag")(demand)


def material_market_tonnes(sim, material):
    return sim.view("material_market_tonnes")[material]


def material_tag(sim, material):
    return sim.view("material_pool")[material]


def electricity_demand_kw(sim):
    return sim.view("electricity_demand")()


def shortage_condition_rows(sim):
    """The standing material shortage as rows for the state screen, empty when none."""
    return sim.view("shortage_conditions")()


def disease_burden(sim):
    return sim.view("disease_burden")()


def epidemic_forecast(sim):
    """The disease model's forecast of the coming year (see the disease module's `epidemic_forecast`)."""
    return sim.view("epidemic_forecast")(None)


def last_demographic_step(sim):
    return sim.view("demographic_flows")()


def effect_terms(sim, effect):
    return sim.view("effect_terms")(effect)


def schooling_flow(sim):
    return sim.view("schooling_flow")(None)


def practice_set(sim):
    return sim.view("practice_set")()


def visible_to_player(sim, node_id):
    return sim.view("visible_to_player")(node_id)


def tech_effects(sim, node_id):
    return sim.view("tech_effects")[node_id]


def settings_meta_path(path):
    return settings._meta_path(path)


# Memory the UI keeps on the `Sim`: saved or read by the engine, so it stays there.

def dashboard_history(sim):
    return sim._dashboard_history


def set_dashboard_history(sim, history):
    sim._dashboard_history = history


def founder_death_aged(sim):
    return sim._founder_death_aged


def founder_death_year(sim):
    return sim._founder_death_year


def set_founder_death(sim, aged, year):
    sim._founder_death_aged, sim._founder_death_year = aged, year


def founder_death_cache(sim):
    return sim._founder_death_cache


def set_founder_death_cache(sim, cache):
    sim._founder_death_cache = cache


def goal_closure(sim):
    return sim.view("goal_closure")()


def set_goal_closure(sim, closure_set):
    sim.send(RememberGoalClosure(closure_set))


def goal_years(sim):
    return dict(sim.view("goal")()["years"])


def set_goal(sim, node_id):
    sim.send(SetGoal(node_id))


def win_condition_anatomy(sim, condition):
    return sim.view("win_condition_anatomy")(condition)


def goal_critical_floor(sim):
    return sim.view("goal_critical_floor")()


def set_goal_critical_floor(sim, years):
    sim.send(RememberGoalFloor(years))


def last_buy_refusal(sim):
    return sim.view("last_buy_refusal")()


def set_last_buy_refusal(sim, refusal):
    sim.send(NoteBuyRefusal(refusal))


def said_command_index(sim):
    return bool(sim._said_command_index)


def set_said_command_index(sim, said):
    sim._said_command_index = said


def said_stack_caution(sim):
    return sim._said_stack_caution


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
