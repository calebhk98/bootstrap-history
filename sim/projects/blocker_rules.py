"""One classifier for why a project cannot begin.

`why`, `why ... compact`, `stuck`, `available` and the `start` refusal all
read `start_blockers`, so a readout cannot disagree with the gate: the gate
is the same list. Each entry is {"kind", "cause", "text", "ids"}; `cause` names the exact check that
refused (for example absent_trades, craft_staff, mothballed), so a reader tells two refusals of one kind apart
without reading the text.

Kinds: knowledge (prerequisites missing), power (a power capability missing),
supply (a material or vessel group with no option in hand), specialists
(people or trades missing), money (the bill is past cash and credit),
politics (the state or a patron), closed (built once but shut),
calendar (a floor of years still to serve, shown by `stuck`), hours (running
work waiting on the founder's own directed hours), idle (nothing in hand) and the terminal ones (done, active, goal, unavailable) where nothing is left to fix.
"""
from dataclasses import dataclass

BLOCKER_KINDS = frozenset((
    "knowledge", "power", "supply", "specialists", "money", "politics", "closed",
    "goal", "done", "active", "unavailable", "calendar", "idle", "hours"))

# Running work reads its blocker from the portfolio's constraint (the sentence
# `waiting_on` builds); this names the shared kind each constraint stands for.
RUNNING_CONSTRAINT_KIND = {
    "staffing": "specialists", "trade_hours": "specialists", "materials": "supply",
    "money": "money", "calendar": "calendar", "founder_hours": "hours", "unclear": "idle"}

BLOCKER_MEANING = {
    "specialists": "a trade is short or already booked: hire or train it, or pause a project that shares it",
    "supply": "a material is throttling the whole economy: buy or sink the source",
    "money": "the bill outruns what you can raise, or the yearly draw rate is what holds it: wait, sell, or pause a draw",
    "calendar": "only the calendar floor is left: it cannot be bought, so spend the hours elsewhere",
    "hours": "your own directed hours are fully committed: reprioritise or raise the pool",
    "idle": "no single cause is named: 'why <id>' for the project"}

TERMINAL_BLOCKER_KINDS = ("goal", "done", "active", "unavailable", "closed")



def supply_blocker_ids(cause, substitution_gap, is_visible):
    """The ids a "supply" refusal names: the visible options of the checked node's failed `req_any` group, and only for
    the substitution check, the one refusal that is about that group."""
    if cause != "substitution" or not substitution_gap:
        return []
    return [option for option in substitution_gap[1] if is_visible(option)]


@dataclass(frozen=True)
class StartCheck:
    """One legality check of the start gate. `cause` names it in a blocker entry; `source` is empty when the module
    runs it as its own method `_check_<cause>`, and otherwise the name of the view that answers it for the module."""
    cause: str
    kind: str
    source: str = ""

    def __post_init__(self):
        if self.kind not in BLOCKER_KINDS:
            raise ValueError("unknown blocker kind %r" % self.kind)


# THE ORDER IS THE CONTRACT. The gate reports the FIRST reason in this sequence that has an opinion, as the single
# if/elif chain it replaced did line by line: a player choosing between two blockers reads only ever the one named
# here first, so re-ordering this tuple changes what a refusal says even when every check's own logic is untouched.
START_CHECKS = (
    StartCheck("win_condition", "goal"),
    StartCheck("already_done", "done"),
    StartCheck("already_active", "active"),
    StartCheck("needs_first", "knowledge"),
    StartCheck("needs_held_herd", "supply"),
    StartCheck("unobtainable", "unavailable"),
    StartCheck("foreign_only", "unavailable"),
    StartCheck("missing_prereqs", "knowledge"),
    StartCheck("running_gates", "closed"),
    StartCheck("unheld_stock", "supply"),
    StartCheck("substitution", "supply"),
    StartCheck("materials_have_a_seller", "supply", "start_gate_material_seller"),
    StartCheck("credit_frozen", "money"),
    StartCheck("arrears", "money"),
    StartCheck("people_exist", "specialists"),
    StartCheck("scholar_staff", "specialists"),
    StartCheck("craft_staff", "specialists"),
    StartCheck("absent_trades", "specialists"),
    StartCheck("none_left_trades", "specialists"),
    StartCheck("group_prohibition", "politics", "start_gate_group_prohibition"),
    StartCheck("social_approval", "politics"),
)

# What mods add: the first refusal an `extra_start_checks` provider gives ends the test after the shipped checks.
EXTENSION_CHECK = StartCheck("extension", "idle", "extra_start_checks")


def classify_plain_check(cause, kind, text, supply_ids, shut_text, is_mothballed):
    """The entry a refusing start check reports. `shut_text` is not None when
    the work is a built venture that is not running: a done check then reads as
    closed with that text; a mothballed one says so in its cause."""
    if kind == "done" and shut_text is not None:
        kind, text = "closed", shut_text
    if cause == "already_done" and is_mothballed:
        kind, cause = "closed", "mothballed"
    elif kind == "closed" and cause == "already_done":
        cause = "built_but_shut"
    return {"kind": kind, "cause": cause, "ids": supply_ids if kind == "supply" else [], "text": text}


def collect_blockers(checks, run_check, classify, money_refusal):
    """Every refusal in gate order. `run_check(check)` returns None or
    (passes, text); `classify(check, text)` returns the entries a refusal
    stands for. A terminal kind ends the list; `money_refusal()` (text or
    None) is read last."""
    blockers = []
    for check in checks:
        verdict = run_check(check)
        if verdict is None or verdict[0]:
            continue
        entries = classify(check, verdict[1])
        blockers.extend(entries)
        if any(entry["kind"] in TERMINAL_BLOCKER_KINDS for entry in entries):
            return blockers
    money = money_refusal()
    if money:
        blockers.append({"kind": "money", "cause": "money_refusal", "ids": [], "text": money})
    return blockers


def power_gate_text(power_ids, generation_kw):
    return ("%s %s a knowledge gate, not installed capacity: your installed "
            "generation (%.0f kW) does not satisfy it, the named capability "
            "has to be reached"
            % (", ".join(power_ids), "is" if len(power_ids) == 1 else "are", generation_kw))


def missing_prereq_entries(missing_visible, any_hidden_missing, is_power, text, plain_text, power_text):
    """The entries for missing prerequisites: the plain ones as a knowledge blocker, the power capabilities as a
    power blocker. `missing_visible` are the missing prerequisites the player may see; `plain_text(ids)` and
    `power_text(ids)` build the sentences when the entry is split."""
    power_ids = [prereq_id for prereq_id in missing_visible if is_power(prereq_id)]
    plain_ids = [prereq_id for prereq_id in missing_visible if prereq_id not in power_ids]
    entries = []
    if plain_ids or any_hidden_missing or not power_ids:
        entries.append({"kind": "knowledge", "cause": "missing_prereqs", "ids": plain_ids,
                        "text": text if not power_ids else plain_text(plain_ids)})
    if power_ids:
        entries.append({"kind": "power", "cause": "power_gate", "ids": power_ids, "text": power_text(power_ids)})
    return entries
