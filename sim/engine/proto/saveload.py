"""Reading and writing a save file, and validating one before it is trusted."""

import collections, hashlib, json, math, os, random, re
from collections import defaultdict

from ..data import *          # the shared tables and loaders
from ..data import (ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, closure,
                   critical_path, downstream_count, is_downstream, load, money_word,
                   topo_order, trade_family)
from ..fog import strip_self_play_advice

from ..core import Sim




SAVE_VERSION = 2

SAVE_FIELDS = (
    # THE LOG, which the `log` command exists to read back and which was not
    # saved. The opening screen promises "progress is written to this file
    # after every command, so you can stop any time - close the terminal,
    # anything - and come back to exactly where you left off", and a break
    # tester did exactly that and found `log` answering "nothing has happened
    # yet" while money, reputation and technologies were all intact. A history
    # that does not survive the thing the game tells you to do is not a history.
    "log",
    "year", "capital", "done", "granted", "active", "done_year", "training",
    "scholars", "artisans", "directors_extra", "reputation",
    "scandal", "eminence", "protection", "familiarity", "forest_ha",
    "nitre_bed_m2", "mine_pending", "mine_ready",
    # WORKINGS, PLURAL: the list each aggregate mine-capacity figure is
    # computed from, including commissioning year, capex and depletion clock.
    "mines",
    "mine_tranches", "market_pressure", "slaves", "freedmen",
    "manumitted_total", "goal_year", "dead_reason", "insolvent_years",
    "bribes_ytd", "living_cost_paid", "mine_cost_paid", "spend_last_year",
    "output_factor", "economy", "throttle", "binding", "bountied",
    "stalled", "life_left", "founder_alive", "revealed", "last_settlement",
    "employees", "trades_created", "policy", "mothballed", "operating",
    "forgotten", "opened_year", "last_taught", "paid_towards",
    "contract_hours",
    # "ALLOCATE" IS A STANDING INSTRUCTION, NOT A ONE-TURN COMMAND - see
    # core.py's own comment on hour_allocations. Like `policy`, it has to
    # survive a save or a player who set it once would see it quietly
    # revert to "let the allocator decide" on every resume, which is the
    # exact silent-reset fault `policy` itself was fixed for.
    "hour_allocations", "work_trade",
    # teaching_hours_this_year was listed here as well as below. Harmless -
    # the tuple is only ever iterated, so the field was simply saved twice -
    # but it made the list 99 literals naming 98 fields, and a list that does
    # not agree with itself is a list nobody trusts to be complete. It lives
    # below, with the other within-year tallies its comment is about.
    "commissioned", "wages_paid",
    "bondage_years_left", "bondage_debt", "money_real", "credit_frozen_until",
    # Counters and within-year tallies that were being silently reset on every
    # single command, because with --session every command is a save and a load.
    # wage_hours_this_year is the dangerous one: it is the tally that stops you
    # selling the same year's hours twice, so dropping it handed the exploit
    # straight back to anyone playing the ordinary way, across sittings.
    "interest_paid", "wage_hours_this_year", "teaching_hours_this_year",
    "trade_hours_used", "total_spend", "director_hours_spent_founder",
    "bounties_paid", "atrocity", "gov", "wages_earned",
    "last_patron_death", "_said_debasement", "_said_autoopen", "_said_output",
    "_said_scandal", "_said_parallelism",
    "_said_command_index",
    "_said_deputies",
    "_said_near_limit",
    "shut_for_staff",
    # THE COUNTRY'S OWN ADOPTION OF WHAT YOU BUILT. See
    # SocietyMixin._advance_food_diffusion_population (society.py).
    "_food_pop_bonus_applied",
    # THE COUNTRY'S OWN AGE-COHORT POPULATION (sim/world/demography.py's
    # `Population`, wired in by docs/architecture/WIRING_MILESTONE_4.md).
    # Three plain floats, not the object itself - JSON has no `Population`,
    # and Sim.__init__ always builds one before load_state runs (see
    # core.py's pop_children/pop_working_age/pop_elderly properties), so
    # only the three cohort counts need to round-trip, the same way
    # `mine_tranches` stores structured-but-flat data rather than an object.
    # NONE of the nine attributes _demographic_recovery's scalar model
    # replaced were ever in this tuple - this is not a rename of an
    # existing save field, it is the fix for a live bug (see the properties'
    # own comment in core.py): a demographic shock's effect was silently
    # wiped by the very next --session command because nothing carried it
    # across a save/load cycle.
    "pop_children", "pop_working_age", "pop_elderly",
    # THE GRANARY (Complaints/45-no-granary-so-the-baseline-collapses.md):
    # agriculture.Storage's carried-forward stock, in kilograms of grain.
    # A plain float, not an object - same reasoning as the three pop_*
    # fields just above (JSON has no `Storage` either, and `Sim.__init__`
    # always sets a default of 0.0 before `load_state` runs, so only the
    # one number needs to round-trip). Before this field existed, a fresh
    # `agriculture.Storage(stock_kg=0.0, ...)` was constructed every single
    # year regardless of what the previous year's harvest banked, which is
    # the missing-buffer bug Complaints/45 measured (rome_100ad,
    # events=False, falling to 21.9% of its starting population over a
    # century with no hazard of any kind - Jensen's inequality on
    # demography.py's own one-sided mortality/fertility response to
    # symmetric weather noise, with nothing damping it). Without this in
    # SAVE_FIELDS, a --session game would silently re-lose its entire
    # banked surplus on every single command, the exact "every command is
    # a save and a load, so an unsaved field breaks the game in normal
    # play" fault CLAUDE.md SS3.5 calls out pop_children/pop_working_age/
    # pop_elderly as the precedent for.
    "farm_stock_kg",
    # TONNES ON HAND. Own production a year did not use banks here instead of
    # evaporating, which is what lets a twenty-gram gold demand be met by
    # buying twenty grams rather than by commissioning a mine. It has to
    # survive a save: without it a resumed game silently starts at zero stock
    # and plays differently from the one that was saved, which is the same
    # class of fault as the fog that could be rewound by reloading. Counter
    # round-trips through JSON as a plain object and comes back a dict, which
    # the accessor treats alike.
    "_material_stock_ledger",
    "farm_hectares",
    "worker_housing_places",
    "trade_schools",
    "last_withdrawal",
    "wages_prepaid",
    # WHAT AN INSTITUTION GAVE YOU OUTRIGHT (see _grant_staff, labour.py).
    # scholars/artisans are saved as their current totals two lines up, but
    # _resync_pools() recomputes both from `employees` on every step and adds
    # this back in - so a save missing it would read correctly right up until
    # the next step, then silently lose the school's +4 scholars the same way
    # the bug this field fixes did.
    "granted_staff",
    # hours_this_year: last year's founder-hours accounting (see step(), just
    # before the within-year tallies above reset). Without it, `state` right
    # after a `--session` reload would report nothing for a figure the player
    # just saw.
    "hours_this_year",
    # THE FOUNDER'S AGE AT DEATH, so it survives a --session reload. `log`
    # is not a saved field, so without these two the one place the age had
    # ever been written would go empty on resume and `state` would silently
    # stop being able to say it - see _founder_death_info.
    "_founder_death_aged", "_founder_death_year",
    # HOW MANY UNITS OF EACH SCALABLE INSTITUTION ARE ACTUALLY FOUNDED. See
    # ProjectsMixin.institution_units (projects.py).
    "inst_units",
    # WHEN a taught trade was first taught, and which taught trades this
    # society has since naturalised on its own.
    "trade_introduced_year", "trades_endemic",
    # ONE SNAPSHOT A YEAR, for `changes` and `economy`'s "what moved most" -
    # see _dashboard_snapshot. Missing entirely, as in every save from
    # before this existed, reads back as no history at all, which `changes`
    # already handles by name ("nothing has been recorded yet"); it is not
    # backfilled, because there is nothing honest to backfill it from.
    "_dashboard_history",
    # RETRY LEARNING, WHICH WAS BEING ERASED BY THE VERY ACT OF SAVING.
    # failed_attempts is what _retry_risk_multiplier and
    # _retry_calendar_retain are computed from (projects.py), so a node the
    # household has failed three times faces 0.53 of its bare risk and banks
    # 56.9% of the elapsed clock toward the next attempt. None of that was
    # in this tuple, so it all reset to "nothing has ever been tried" on
    # every resume: three failures on zone_refining went from a 23.8% next
    # attempt back to the full 45%, and `why`'s own attempts_already_failed
    # told the player 0 about a node they had failed six times. The player
    # who won this game complained that repeated 45% failures had "no
    # strategic mitigation visible" - the mitigation existed and the save
    # round-trip was deleting it. A defaultdict comes back from JSON as a
    # plain dict, which is promoted in load_state before anything adds to it.
    #
    # `shortages` is the same omission with far lower stakes: a diagnostic
    # tally of which material bound in which year, read by `run`/`compare`'s
    # cross-seed summary (cli.py) and by nothing that decides anything. It
    # is here so that a resumed game's own record of what it has been short
    # of is continuous, not because any mechanic reads it.
    "failed_attempts", "shortages",
)


def save_state(s, path):
    """Write the whole game to a file.

    There was no save, which is why every playtester ended up writing a driver
    script to hold one long session across many calls. That is a thing a tester
    can do and a player should never have to, so the fix is not a better script,
    it is a save file.
    """
    blob = {}
    for field_name in SAVE_FIELDS:
        value = getattr(s, field_name, None)
        if isinstance(value, set):
            value = {"__set__": sorted(value)}
        blob[field_name] = value
    blob["_civ"] = s.civ.get("id")
    # THE GOAL YOU CHOSE, same reasoning as _fog/_immortal just below: it is
    # a choice the menu asked about when this game began, not a flag that
    # should silently reset to the transistor because a resume happened to
    # omit --goal. See load_state.
    blob["_goal"] = getattr(s, "goal", None)
    blob["_civ_live"] = {attr: s.civ.get(attr) for attr in
                         ("literacy_general", "literacy_elite", "state_capacity")}
    blob["_weights"] = dict(s.w)
    blob["_fog"] = getattr(s, "fog", False)
    # WHETHER THE FOUNDER AGES, saved for the same reason fog is: they are
    # choices the menu asks you to make about what game this is, and resuming
    # into the other one is resuming into a different game. _fog was already
    # written here and never read back, so every resumed game silently had the
    # whole tree in view; see load_state.
    blob["_immortal"] = bool(s.cfg.get("immortal", True))
    # THE DICE, TOO. Nothing saved the random state, so every resume restarted
    # it from the seed and re-rolled everything the world does. A break tester
    # found the sharp edge of that: a project sitting at its completion
    # threshold re-rolls its failure check on each resume, so
    # `start fin_bimetallism` then one `step` per process oscillated
    # 100%/60%/100%/60% for ever, burning hours and money and never finishing.
    # They reproduced it 5 times out of 5. It also meant hazards, sackings and
    # events were silently re-drawn every time a player came back to a save,
    # which is a different game from the one they left.
    try:
        rng_state = s.rng.getstate()
        blob["_rng"] = [rng_state[0], list(rng_state[1]), rng_state[2]]
    except Exception:
        blob["_rng"] = None
    blob["_version"] = SAVE_VERSION
    tmp = path + ".tmp"
    # A save into a directory that is not there killed the process outright on
    # a FileNotFoundError, which is the one thing a save must never do.
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(tmp, "w") as handle:
        json.dump(blob, handle, indent=1, sort_keys=True, default=str)
    os.replace(tmp, path)          # atomic: a crash mid-save cannot eat the game
    return path


# A run is short and save files are deliberately tied to the code that wrote
# them. There is no upgrade path: accepting a partial older shape quietly
# invents state, which is worse than asking the player to begin a new run.
REQUIRED_SAVE_FIELDS = SAVE_FIELDS + (
    "_civ", "_goal", "_civ_live", "_weights", "_fog", "_immortal", "_rng",
    "_version",
)

# Fields that hold a SET of node ids (see save_state's {"__set__": [...]}
# encoding). Anything named here is checked against the currently loaded
# tree, because the tree is data and does get edited: a node can be renamed
# or removed between when a save was written and when it is read back.
# NOT trades_created. That holds TRADE names - "optician", "chemist" - and it
# was in this list, so `train optician 1` wrote a perfectly valid trade into
# the save and the next load refused the whole file for referring to a
# technology called optician that the tree does not have and never did. A
# normal-play tester lost two runs to it, and it is worse than losing a save:
# the five trades that have to be taught are the ones gating chemistry,
# precision and electricity, so the one action that opens the second half of
# the game was the one action that destroyed the game.
_SET_FIELDS_OF_NODE_IDS = ("done", "granted", "mothballed", "operating",
                           "bountied",
                           "revealed")
# Checked against the wage table instead, which is what they actually are.
# trades_endemic holds trade names for the same reason trades_created does
# (see the comment just above) and needs exactly the same protection: it is
# a set of TRADE names, not node ids, so it belongs here and not in
# _SET_FIELDS_OF_NODE_IDS.
_SET_FIELDS_OF_TRADE_NAMES = ("trades_created", "trades_endemic")


def _validate_save(blob, s):
    """None if `blob` looks like a save this game could have produced and can
    be loaded into `s` as it stands right now; otherwise a short, plain
    sentence saying why not.

    `load` used to accept any JSON object at all: a typo'd filename, an
    unrelated file, a save from a different civilisation, or a save that
    refers to a node a later edit to the tech tree renamed or removed. Every
    one of those went straight into setattr() - which either corrupted the
    running game half-applied (fields earlier in SAVE_FIELDS take, the rest
    do not, because the loop does not stop for a bad value) or surfaced as a
    bare Python exception. This runs to completion BEFORE a single attribute
    of `s` is touched, so a bad file costs exactly one clear sentence and
    nothing else about the running game changes.
    """
    if not isinstance(blob, dict):
        return ("this is not a save from this game: expected a JSON object, "
                "got %s" % type(blob).__name__)
    missing = [field_name for field_name in REQUIRED_SAVE_FIELDS if field_name not in blob]
    if missing:
        shown = ", ".join(missing[:8])
        if len(missing) > 8:
            shown += ", and %d more required fields" % (len(missing) - 8)
        return "this is not a save from this game: missing %s" % shown
    if not isinstance(blob.get("_version"), int):
        return "this save is corrupt: '_version' should be a whole number"
    if blob["_version"] != SAVE_VERSION:
        return ("this save uses format version %s; this build requires version %s. "
                "Saved runs are not migrated; start a new run."
                % (blob["_version"], SAVE_VERSION))
    if blob["_goal"] not in s.nodes:
        return "this save's goal is not in the current technology tree"
    if not isinstance(blob["_civ_live"], dict) or not isinstance(blob["_weights"], dict):
        return "this save is corrupt: civilization state should be objects"
    try:
        rng_version, rng_keys, rng_gaussian = blob["_rng"]
        probe = random.Random()
        probe.setstate((rng_version, tuple(int(state_int) for state_int in rng_keys), rng_gaussian))
    except (TypeError, ValueError):
        return "this save has an invalid random-number state"
    for field_name in ("year", "capital"):
        value = blob.get(field_name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "this save is corrupt: '%s' should be a number, got %r" % (field_name, value)

    civ_id = blob.get("_civ")
    have_civ = s.civ.get("id")
    if civ_id != have_civ:
        return ("this save is from a different civilisation (%r); this game "
                "is running %r. Start the agent with --civ %s to load it."
                % (civ_id, have_civ, civ_id))

    active = blob.get("active")
    if not isinstance(active, dict):
        return "this save is corrupt: 'active' should be an object of id -> progress"
    for node_id, value in active.items():
        if not isinstance(node_id, str) or not isinstance(value, dict):
            return "this save is corrupt: active[%r] is not a valid entry" % (node_id,)
        for field_name in ("ph_left", "spent", "cost_left"):
            if field_name not in value or isinstance(value[field_name], bool) or not isinstance(value[field_name], (int, float)):
                return ("this save is corrupt: active[%r] is missing a numeric "
                         "'%s'" % (node_id, field_name))
        if not isinstance(value.get("lab_left"), dict):
            return "this save is corrupt: active[%r] is missing 'lab_left'" % (node_id,)

    done = blob.get("done")
    if not (isinstance(done, dict) and isinstance(done.get("__set__"), list)):
        return "this save is corrupt: 'done' should be a set of ids"

    # Every node id the save refers to must still exist in the tree we have
    # loaded right now.
    unknown = set()
    for field_name in _SET_FIELDS_OF_NODE_IDS:
        value = blob.get(field_name)
        if value is None:
            continue
        ids = value.get("__set__") if isinstance(value, dict) else None
        if ids is None or not all(isinstance(node_id, str) for node_id in ids):
            return "this save is corrupt: '%s' should be a set of id strings" % field_name
        unknown |= {node_id for node_id in ids if node_id not in s.nodes}
    unknown |= {node_id for node_id in active if node_id not in s.nodes}
    for field_name in _SET_FIELDS_OF_TRADE_NAMES:
        value = blob.get(field_name)
        if value is None:
            continue
        ids = value.get("__set__") if isinstance(value, dict) else None
        if ids is None or not all(isinstance(trade_name, str) for trade_name in ids):
            return "this save is corrupt: '%s' should be a set of trade names" % field_name
        strange = [trade_name for trade_name in ids if trade_name not in WAGES]
        if strange:
            return ("this save refers to trade(s) this game does not have: %s"
                    % ", ".join(sorted(strange)[:6]))
    if unknown:
        sample = ", ".join(sorted(unknown)[:6])
        more = "" if len(unknown) <= 6 else " and %d more" % (len(unknown) - 6)
        return ("this save refers to node(s) the current tech tree does not "
                "have: %s%s. The tree has changed since this was saved; it "
                "cannot be loaded against this version of the game."
                % (sample, more))
    return None


def civ_of_save(path):
    """Which civilisation a save file is from, or None if it will not say.

    A save records the game it is; a command line resuming it should not have
    to be told again. A playtester was handed `play --session england_1300.json`
    by the game itself, ran exactly that, and was refused with "this save is
    from a different civilisation" - because the flag defaulted to Rome. The
    file knew the answer the whole time.
    """
    try:
        with open(path) as handle:
            return (json.load(handle) or {}).get("_civ")
    except (OSError, ValueError, AttributeError):
        return None


def goal_of_save(path):
    """Which goal a save file was playing toward, or None if it will not
    say (an older save, or one the file on disk does not match). Same
    reasoning as civ_of_save just above, and used the same way: a resumed
    session should not need --goal repeated any more than it needs --civ
    repeated, and a strategy order picked before the save is even read
    would be picked for the wrong goal.
    """
    try:
        with open(path) as handle:
            return (json.load(handle) or {}).get("_goal")
    except (OSError, ValueError, AttributeError):
        return None


def load_state(s, path):
    """Read a save from `path` and apply it to `s`, or raise ValueError with
    a clear reason and leave `s` completely untouched.

    Validation (see _validate_save) always runs to completion first; nothing
    below it can execute against a file that failed. A half-loaded game is
    worse than a refused one.
    """
    blob = json.load(open(path))
    bad = _validate_save(blob, s)
    if bad:
        raise ValueError(bad)
    # FOG IS A PROPERTY OF THE GAME YOU CHOSE, NOT A FIELD IN A FILE, and this
    # has to be checked BEFORE anything is applied - the fog flag is restored
    # further down, so a check placed after it is checking the value it was
    # about to reject. `load` validated the filename carefully and the contents
    # barely at all, so a hand-edited save with "_fog": false turned the fog
    # off in a running fogged game and `path` began answering, in a game whose
    # own help says there is no way to view the whole tree. A break tester did
    # exactly that. A save may resume the fog it was played with; it may not
    # switch the fog off underneath you.
    if getattr(s, "fog", False) and blob.get("_fog") is False:
        raise ValueError("that save was played without fog of war and this "
                         "game is being played with it. A save cannot turn the "
                         "fog off; start a new game without it if that is what "
                         "you want.")
    for field_name in SAVE_FIELDS:
        value = blob[field_name]
        # NEVER restore a null over a live default. A field that had not been
        # initialised yet when the game was saved, spend_last_year and
        # insolvent_years among them, was written as null and then loaded back
        # OVER the number the constructor had just set, so the next `state`
        # died on round(None). A naive tester hit this on the very first
        # save-and-restart, which is the exact workflow the welcome text tells
        # players is safe, and went back to holding a process open through a
        # FIFO instead. My own round-trip tests missed it because I happened to
        # step the clock first, which initialises those fields.
        if value is None:
            continue
        if isinstance(value, dict) and "__set__" in value:
            value = set(value["__set__"])
        setattr(s, field_name, value)
    # PROMOTE THE ACCUMULATORS BACK, before anything adds to one. JSON has no
    # defaultdict and no Counter, so the loop above has just put plain dicts
    # where projects.py does `self.failed_attempts[k] += 1` and economy.py
    # does `self.shortages[who] += 1`, both of which raise KeyError on a new
    # key in a plain dict. Same shape as economy.py's own _material_stock
    # promotion, done here rather than lazily because these two are written
    # to directly rather than through an accessor.
    s.failed_attempts = collections.defaultdict(
        int, {node_id: int(value) for node_id, value in (getattr(s, "failed_attempts", None) or {}).items()})
    s.shortages = collections.Counter(getattr(s, "shortages", None) or {})
    # `operating` JUST WENT BACK TO BEING A PLAIN SET. The generic setattr
    # above has no idea self.operating is normally an _InvalidatingSet (see
    # economy.py) and replaced it with whatever plain `set(...)` came out of
    # the save - correct in content, but silently unable to invalidate
    # capability_factor()'s cache on any future .add/.discard. That is a
    # real gap, not a theoretical one: `load` reached through the agent/play
    # JSON protocol runs this against the SAME long-lived Sim a session goes
    # on playing in, not a fresh one, and every open/close/mothball after
    # this point mutates .operating directly. Re-wrap it, once, here.
    s._reset_operating()
    # The game this save IS, not whatever the command line happened to say.
    s.fog = bool(blob["_fog"])
    s.cfg["immortal"] = bool(blob["_immortal"])
    s.goal = blob["_goal"]
    rng_version, _keys, rng_gaussian = blob["_rng"]
    s.rng.setstate((rng_version, tuple(int(state_int) for state_int in _keys), rng_gaussian))

    for attr, value in blob["_civ_live"].items():
        if value is not None:
            s.civ[attr] = value
    s.w.update(blob["_weights"])
    s.state_capacity = float(s.civ.get("state_capacity", s.state_capacity))
    s.fog = bool(blob.get("_fog", False))
    return s
