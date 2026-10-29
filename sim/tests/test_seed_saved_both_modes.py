"""Complaint 360: a seed is kept as the game keeps it, a number as the number and a word in lower case, and a saved
state carries it back unchanged. The rules are called on the seed functions and a bare `SimulationState`; the CLI
choice of the seed a sitting starts with is test_resolve_seed."""

QUICK_TOPIC = True

from .harness import check

from sim.engine.settings_table import normal_seed, valid_seed_text
from sim.engine.state import FounderState, HouseholdState, SimulationState, deserialize_state, serialize_state

check("a number seed is kept as the number", normal_seed(7) == 7 and normal_seed("7") == 7 and normal_seed(" 7 ") == 7)
check("a word seed is kept as the word, in lower case", normal_seed("Dragon") == "dragon")
check("a seed that mixes letters and digits is a word", normal_seed("Rome42") == "rome42")
check("a seed is one word of letters, digits, dashes and underscores",
      valid_seed_text("rome-42_b") and not valid_seed_text("two words") and not valid_seed_text(""))

for seed in (7, "dragon"):
    state = SimulationState(household=HouseholdState(capital=1.0), founder=FounderState())
    state._seed = seed
    check("a saved and loaded state reports seed %r" % (seed,), deserialize_state(serialize_state(state))._seed == seed)
