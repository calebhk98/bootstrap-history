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
