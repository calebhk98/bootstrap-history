"""The opening's price solves are replayed at the other interest-rate bands so they ship under the keys a game computes
(`shipped_rate_bands`): `solve_other_bands` makes each recorded call at each banded rate with only the rate changed, and the
recorder keeps the calls made at the starting rate for the game's own catalogue. That a shipped entry stands in for a computation
is test_solve_cache_and_warm_start_rules; which rates are banded is test_shipped_rate_band_range_rule. The solver is replaced by a
recorder."""

QUICK_TOPIC = True

from unittest import mock

from .harness import check

from sim.engine import prices, shipped_rate_bands

STARTING_RATE = 0.12
HELD = frozenset({"node_a"})
RATIOS = {"labourer": 1.0}


def replay(calls, max_bands=3):
    made = []
    with mock.patch.object(prices, "solved_prices_at_wages", side_effect=lambda *arguments, **keywords: made.append((arguments, keywords))):
        shipped_rate_bands.solve_other_bands(calls, STARTING_RATE, max_bands)
    return made


bands = shipped_rate_bands.banded_rates(STARTING_RATE, 3)
positional = ((HELD, RATIOS, None, "rome_100ad", frozenset(), STARTING_RATE), {})
by_keyword = ((HELD, RATIOS), {"civilization_id": "rome_100ad", "interest_rate": STARTING_RATE})

made = replay([positional])
check("each recorded call is made once at each banded rate, nearest first",
      [arguments[5] for arguments, _keywords in made] == bands and len(made) == 3, made)
check("only the rate changes in a call that passed it positionally",
      all(arguments[:5] == positional[0][:5] and keywords == {} for arguments, keywords in made), made)
made = replay([by_keyword])
check("a call that passed the rate by keyword gets it by keyword, and nothing else changes",
      [keywords["interest_rate"] for _arguments, keywords in made] == bands
      and all(arguments == by_keyword[0] and keywords["civilization_id"] == "rome_100ad" for arguments, keywords in made), made)
made = replay([positional, by_keyword], max_bands=2)
check("every call is replayed at a band before the next band", [keywords.get("interest_rate", arguments[5] if len(arguments) > 5 else None)
                                                                for arguments, keywords in made] == [bands[0], bands[0], bands[1], bands[1]], made)
check("with no calls recorded nothing is solved", replay([]) == [])
check("the call itself is left as it was", positional[0][5] == STARTING_RATE and by_keyword[1]["interest_rate"] == STARTING_RATE)

recorder = shipped_rate_bands.SolveRecorder()
recorder.calls = [
    ((HELD, RATIOS, None), {}),                                                     # the game's catalogue, at the starting rate (none given)
    ((HELD, RATIOS, None, "rome_100ad", frozenset(), STARTING_RATE), {}),            # the starting rate given
    ((HELD, RATIOS, None, "rome_100ad", frozenset(), 0.07), {}),                    # another rate
    ((HELD, RATIOS, {"synthetic": {}}), {}),                                         # a catalogue of its own
    ((HELD, RATIOS), {"production_entries": {"synthetic": {}}}),                     # a catalogue of its own, by keyword
]
kept = recorder.at_starting_rate(STARTING_RATE)
check("the calls kept are those at the starting rate, whether or not they name it, on the game's own catalogue",
      kept == recorder.calls[:2], kept)
