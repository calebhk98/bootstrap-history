"""What each kind of log line means to a reader: its severity tier and whether it is bad news, a step stop or notable.

The engine tags a line with a `kind` (sim/refusal.py LogLine); this table says how the protocol treats that kind.
A line with no kind, or a kind not listed, is informational and none of the flags. Nothing here reads a line's text.
"""
from sim.refusal import cause_of, facts_of

RUN_ENDING, SACK, DEMOGRAPHIC, ECONOMIC, MAJOR_FAILURE, MINOR, COMPLETION = (
    "run_ending", "regime_war_or_sack", "demographic_catastrophe", "economic_crisis",
    "major_project_failure", "minor_setback", "project_completion")
INFORMATIONAL = "informational"


def _entry(tier=INFORMATIONAL, failure=False, stop=False, notable=False):
    return {"tier": tier, "failure": failure, "stop": stop, "notable": notable}


# failure: shown by `log failures`; stop: interrupts a multi-year step; notable: listed by `changes`.
EVENT_KINDS = {
    "founder_dies": _entry(RUN_ENDING, failure=True, stop=True, notable=True),
    "run_ends": _entry(RUN_ENDING, failure=True, notable=True),
    "programme_dissolving": _entry(RUN_ENDING, failure=True, notable=True),
    "goal_achieved": _entry(COMPLETION),
    "project_completed": _entry(COMPLETION),
    "site_sacked": _entry(SACK, failure=True, notable=True),
    "state_noticed": _entry(SACK),
    "debt_bondage": _entry(SACK, failure=True),
    "wage_cascade": _entry(DEMOGRAPHIC),
    "hazard_hit": _entry(DEMOGRAPHIC, notable=True),
    "world_hazard": _entry(DEMOGRAPHIC),
    "colony_died_out": _entry(notable=True),
    "credit_exhausted": _entry(ECONOMIC, failure=True, stop=True, notable=True),
    "credit_near_limit": _entry(ECONOMIC, failure=True, stop=True),
    "insolvency_settled": _entry(ECONOMIC, failure=True, notable=True),
    "arrears_closed_concerns": _entry(ECONOMIC, failure=True),
    "arrears_staff_leaving": _entry(ECONOMIC, failure=True),
    "arrears_hours_lost": _entry(ECONOMIC, failure=True),
    "staff_left_unpaid": _entry(ECONOMIC, failure=True),
    "creditors_took": _entry(ECONOMIC),
    "treasury_watching": _entry(ECONOMIC),
    "household_disperses": _entry(failure=True),
    "works_abandoned_arrears": _entry(MAJOR_FAILURE, failure=True),
    "project_halted_no_labour": _entry(MAJOR_FAILURE, failure=True),
    "project_abandoned": _entry(MAJOR_FAILURE, failure=True),
    "project_cannot_go_on": _entry(MAJOR_FAILURE, failure=True),
    "concerns_closed_unstaffed": _entry(MAJOR_FAILURE, failure=True),
    "staff_lost_stops_concerns": _entry(MAJOR_FAILURE, failure=True, stop=True),
    "knowledge_lost": _entry(MAJOR_FAILURE, failure=True),
    "fire": _entry(MAJOR_FAILURE, failure=True, notable=True),
    "project_failed": _entry(MINOR, failure=True),
    "mines_mothballed": _entry(MINOR, failure=True),
    "work_mothballed": _entry(MINOR, failure=True),
    "material_shortage": _entry(MINOR, failure=True),
    "directed_hours_unused": _entry(MINOR),
    "eminence_warning": _entry(MINOR),
    "scandal_warning": _entry(MINOR, notable=True),
    "prominence_confiscated": _entry(MINOR, failure=True),
    "prominence_demand_kept": _entry(MINOR),
    "prominence_patron_destroyed": _entry(MINOR, failure=True),
    "hazard_condition_failed": _entry(MINOR),
    "banditry": _entry(MINOR, notable=True),
    # informational: reported, but no tier above the quietest and none of the flags
    "army_mutiny": _entry(),
    "arrears_interest": _entry(),
    "bondage_served": _entry(),
    "bought_people_trained": _entry(),
    "bounty_posted": _entry(),
    "colony_founded": _entry(),
    "concern_levy": _entry(),
    "concern_unprofitable": _entry(),
    "concerns_reopened": _entry(),
    "confiscation_refused": _entry(),
    "confiscation_too_large": _entry(),
    "coppice_limit": _entry(),
    "deputies_directing": _entry(),
    "failure_loss": _entry(),
    "goal_effect": _entry(),
    "group_eased": _entry(),
    "group_petition": _entry(),
    "hazard_attack_averted": _entry(),
    "hazard_coin_debased": _entry(),
    "hazard_output_fall": _entry(),
    "hazard_values_shift": _entry(),
    "hidden_wealth_found": _entry(),
    "hire_ordered": _entry(),
    "let_go_ordered": _entry(),
    "nitre_bed_laid": _entry(),
    "opening_shortfall": _entry(),
    "patron_dies": _entry(),
    "people_bought": _entry(),
    "people_freed": _entry(),
    "policy_hire": _entry(),
    "policy_housing": _entry(),
    "project_restarted": _entry(),
    "project_started": _entry(),
    "project_stopped": _entry(),
    "requisition_enforced": _entry(),
    "requisition_negotiated": _entry(),
    "requisition_unenforced": _entry(),
    "restored": _entry(),
    "school_progress": _entry(),
    "society_changed": _entry(),
    "staff_lost": _entry(),
    "state_confiscation": _entry(),
    "state_military_demand": _entry(),
    "state_notice_approaching": _entry(),
    "state_paid": _entry(),
    "teaching_begun": _entry(),
    "trade_no_longer_only_yours": _entry(),
    "training_finished": _entry(),
    "venture_opened": _entry(),
    "wage_work_sold": _entry(),
    "withdrew_from_public_life": _entry(),
    "work_closed_gate_lapsed": _entry(),
    "work_opened": _entry(),
    "work_restored": _entry(),
    "workings_closed": _entry(),
    "workings_exhausted": _entry(),
    "hazard_condition_met": _entry(),
    "hazard_condition_unmet": _entry(),
}
TIER_NAMES = (RUN_ENDING, SACK, DEMOGRAPHIC, ECONOMIC, MAJOR_FAILURE, MINOR, COMPLETION, INFORMATIONAL)


def kind_of(line):
    """The kind of a log line, or of a reply event (a dict carrying `event_kind`); None when it has none."""
    return line.get("event_kind") if isinstance(line, dict) else cause_of(line)


def _facts_of(line):
    return (line.get("facts") if isinstance(line, dict) else facts_of(line)) or {}


def _entry_of(line):
    return EVENT_KINDS.get(kind_of(line)) or _entry()


def tier_name(message):
    """The severity tier name of a log line or reply event, by its kind."""
    return _entry_of(message)["tier"]


def is_failure(message):
    """Whether a log line is bad news for `log failures`."""
    return _entry_of(message)["failure"]


def is_notable(message):
    """Whether a log line is a political event `changes` lists."""
    return _entry_of(message)["notable"]


def stops_a_step(message):
    """Whether a log line is a warning that interrupts a multi-year step."""
    return _entry_of(message)["stop"]


def is_minor_failure(message):
    """Whether a log line reports a project failure of minor size."""
    return kind_of(message) == "project_failed" and _facts_of(message).get("severity") == "minor"


def is_severe_failure(message):
    """Whether a log line reports a project failure that is not minor."""
    return kind_of(message) == "project_failed" and not is_minor_failure(message)


def worst_kind(events):
    """The kind of the worst-tier event among `events` (the first on a tie), or None when none has a kind."""
    kinds = [kind_of(event) for event in events if kind_of(event) in EVENT_KINDS]
    return min(kinds, key=lambda kind: TIER_NAMES.index(EVENT_KINDS[kind]["tier"]), default=None)
