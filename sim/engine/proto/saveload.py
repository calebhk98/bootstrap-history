"""Reading and writing a save file, and validating one before it is trusted."""

import collections, json, os, random

from ..data import WAGES
from sim.engine.state import (
    SAVE_FIELDS,
    get_save_fields,
    serialize_state,
    deserialize_state,
    extract_simulation_state,
    apply_simulation_state,
)

SAVE_VERSION = 3


def save_state(sim, path):
	"""Write the whole game to a file using automatic state serialization from live sim.state."""
	sim.state._civ = sim.civ.get("id")
	sim.state._goal = sim.goal
	sim.state._civ_live = {attr: sim.civ.get(attr) for attr in ("literacy_general", "literacy_elite", "state_capacity")}
	sim.state._weights = dict(sim.value_weights)
	sim.state._fog = sim.fog
	sim.state._immortal = bool(sim.cfg.get("immortal", True))
	try:
		rng_state = sim.rng.getstate()
		sim.state._rng = [rng_state[0], list(rng_state[1]), rng_state[2]]
	except Exception:
		sim.state._rng = None
	if hasattr(sim, "population") and getattr(sim, "state", None) is not None and sim.state.population is not None:
		sim.state.population.pop_children = float(sim.population.children)
		sim.state.population.pop_working_age = float(sim.population.working_age)
		sim.state.population.pop_elderly = float(sim.population.elderly)
	sim.state._version = 3

	blob = serialize_state(sim.state)
	tmp = path + ".tmp"
	parent = os.path.dirname(os.path.abspath(path))
	if parent and not os.path.isdir(parent):
		os.makedirs(parent, exist_ok=True)
	with open(tmp, "w") as handle:
		json.dump(blob, handle, indent=1, sort_keys=True, default=str)
	os.replace(tmp, path)          # atomic: a crash mid-save cannot eat the game
	return path


REQUIRED_V3_SECTIONS = (
    "household", "projects", "economy", "governance", "founder", "scenario",
    "population",
)

REQUIRED_METADATA_FIELDS = (
    "_civ", "_goal", "_civ_live", "_weights", "_fog", "_immortal", "_rng",
    "_version",
)

REQUIRED_SAVE_FIELDS = REQUIRED_V3_SECTIONS + REQUIRED_METADATA_FIELDS

# Fields that hold a SET of node ids (see save_state's {"__set__": [...]}
# encoding). Anything named here is checked against the currently loaded
# tree, because the tree is data and does get edited: a node can be renamed
# or removed between when a save was written and when it is read back.
_SET_FIELDS_OF_NODE_IDS = ("done", "granted", "mothballed", "operating",
                           "bountied", "revealed")
# Checked against the wage table instead, which is what they actually are.
_SET_FIELDS_OF_TRADE_NAMES = ("trades_created", "trades_endemic")


def _get_field(blob, field_name):
    """Retrieve field from root or subsystem state sections."""
    if not isinstance(blob, dict):
        return None
    if field_name in blob:
        return blob[field_name]
    for section in ("household", "projects", "economy", "governance", "founder", "scenario", "population"):
        sec = blob.get(section)
        if isinstance(sec, dict) and field_name in sec:
            return sec[field_name]
    return None



def _check_save_shape(blob):
    """None if `blob` is a JSON object carrying every required v3 section and
    metadata field this build requires; otherwise the refusal message.
    """
    if not isinstance(blob, dict):
        return ("this is not a save from this game: expected a JSON object, "
                "got %s" % type(blob).__name__)
    if "_version" not in blob:
        return "this is not a save from this game: missing '_version'"

    required = REQUIRED_V3_SECTIONS + REQUIRED_METADATA_FIELDS
    missing = [f for f in required if f not in blob]
    if missing:
        shown = ", ".join(missing[:8])
        if len(missing) > 8:
            shown += ", and %d more required fields" % (len(missing) - 8)
        return "this is not a save from this game: missing %s" % shown

    for section in REQUIRED_V3_SECTIONS:
        if not isinstance(blob.get(section), dict):
            return "this save is corrupt: section '%s' should be an object" % section

    return None


def _check_save_version(blob):
    """None if `blob`'s version stamp is a whole number matching the one this
    build writes; otherwise the refusal message.
    """
    if not isinstance(blob.get("_version"), int):
        return "this save is corrupt: '_version' should be a whole number"
    if blob["_version"] != SAVE_VERSION:
        return ("this save uses format version %s; this build requires version %s. "
                "Saved runs are not migrated; start a new run."
                % (blob["_version"], SAVE_VERSION))
    return None


def _check_save_scalars(blob, sim):
    """None if the save's simple top-level fields are valid; otherwise the refusal message."""
    if blob.get("_goal") not in sim.nodes:
        return "this save's goal is not in the current technology tree"
    if not isinstance(blob.get("_civ_live"), dict) or not isinstance(blob.get("_weights"), dict):
        return "this save is corrupt: civilization state should be objects"
    try:
        rng_version, rng_keys, rng_gaussian = blob["_rng"]
        probe = random.Random()
        probe.setstate((rng_version, tuple(int(state_int) for state_int in rng_keys), rng_gaussian))
    except (TypeError, ValueError):
        return "this save has an invalid random-number state"
    for field_name in ("year", "capital"):
        value = _get_field(blob, field_name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "this save is corrupt: '%s' should be a number, got %r" % (field_name, value)

    civ_id = blob.get("_civ")
    have_civ = sim.civ.get("id")
    if civ_id != have_civ:
        return ("this save is from a different civilisation (%r); this game "
                "is running %r. Start the agent with --civ %s to load it."
                % (civ_id, have_civ, civ_id))
    return None


def _check_save_active(blob):
    """None if active is a well-formed mapping; otherwise the refusal message."""
    active = _get_field(blob, "active")
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
    return None


def _check_save_done(blob):
    """None if done is shaped like a saved set; otherwise the refusal message."""
    done = _get_field(blob, "done")
    if not (isinstance(done, dict) and isinstance(done.get("__set__"), list)):
        return "this save is corrupt: 'done' should be a set of ids"
    return None


def _check_save_node_id_references(blob, sim):
    """The refusal message if any node ID field is shaped wrong; otherwise (None, unknown)."""
    unknown = set()
    for field_name in _SET_FIELDS_OF_NODE_IDS:
        value = _get_field(blob, field_name)
        if value is None:
            continue
        ids = value.get("__set__") if isinstance(value, dict) else None
        if ids is None or not all(isinstance(node_id, str) for node_id in ids):
            return "this save is corrupt: '%s' should be a set of id strings" % field_name, None
        unknown |= {node_id for node_id in ids if node_id not in sim.nodes}
    active = _get_field(blob, "active") or {}
    unknown |= {node_id for node_id in active if node_id not in sim.nodes}
    return None, unknown


def _check_save_trade_name_sets(blob):
    """None if trade name sets contain only known trades; otherwise the refusal message."""
    for field_name in _SET_FIELDS_OF_TRADE_NAMES:
        value = _get_field(blob, field_name)
        if value is None:
            continue
        ids = value.get("__set__") if isinstance(value, dict) else None
        if ids is None or not all(isinstance(trade_name, str) for trade_name in ids):
            return "this save is corrupt: '%s' should be a set of trade names" % field_name
        strange = [trade_name for trade_name in ids if trade_name not in WAGES]
        if strange:
            return ("this save refers to trade(s) this game does not have: %s"
                    % ", ".join(sorted(strange)[:6]))
    return None


def _validate_save(blob, sim):
	"""Validate save file format and contents before mutating simulation."""
	message = _check_save_shape(blob)
	if message:
		return message
	message = _check_save_version(blob)
	if message:
		return message
	message = _check_save_scalars(blob, sim)
	if message:
		return message
	message = _check_save_active(blob)
	if message:
		return message
	message = _check_save_done(blob)
	if message:
		return message
	message, unknown = _check_save_node_id_references(blob, sim)
	if message:
		return message
	message = _check_save_trade_name_sets(blob)
	if message:
		return message
	if unknown:
		sample = ", ".join(sorted(unknown)[:6])
		more = "" if len(unknown) <= 6 else " and %d more" % (len(unknown) - 6)
		return ("this save refers to node(s) the current tech tree does not "
				"have: %s%s. The tree has changed since this was saved; it "
				"cannot be loaded against this version of the game."
				% (sample, more))
	return None


def civ_of_save(path):
    """Which civilisation a save file is from, or None if it will not say."""
    try:
        with open(path) as handle:
            return (json.load(handle) or {}).get("_civ")
    except (OSError, ValueError, AttributeError):
        return None


def goal_of_save(path):
    """Which goal a save file was playing toward, or None if it will not say."""
    try:
        with open(path) as handle:
            return (json.load(handle) or {}).get("_goal")
    except (OSError, ValueError, AttributeError):
        return None


def load_state(sim, path):
	"""Read a save from `path` and apply it to `sim`, or raise ValueError with
	a clear reason and leave `sim` completely untouched.
	"""
	with open(path) as f:
		blob = json.load(f)
	bad = _validate_save(blob, sim)
	if bad:
		raise ValueError(bad)

	if sim.fog and blob.get("_fog") is False:
		raise ValueError("that save was played without fog of war and this "
						 "game is being played with it. A save cannot turn the "
						 "fog off; start a new game without it if that is what "
						 "you want.")

	old_revealed = set(sim.state.projects.revealed) if getattr(sim, "state", None) and getattr(sim.state, "projects", None) and sim.state.projects.revealed else set()
	state = deserialize_state(blob)
	if old_revealed and getattr(state, "projects", None):
		state.projects.revealed = set(state.projects.revealed or set()) | old_revealed
	sim.state = state
	sim._reconnect_state_hooks()
	return sim

