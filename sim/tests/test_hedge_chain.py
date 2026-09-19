"""hedge_chain: regression checks, run individually with `--only hedge_chain`."""
from .harness import *  # noqa: F401,F403

# =============================================================================
# A HEDGE ANNOUNCED FIVE YEARS OUT AND TWENTY-TO-THIRTY YEARS DEEP. Two
# playtesters (Han, Rome) were told from turn one that the hedge against
# being sacked was "walls, firearms, powerful friends, and copies of your
# work kept somewhere else", acted on it the moment it was said, and were
# still sacked - because the strongest of those hedges,
# HAZARD_COUNTERS["sack_chance"]'s biggest single share, sits behind a
# scientific_method -> corpus_written -> corpus_dispersed -> academy_network
# chain whose own `yrs` fields (already shown per-node, already the basis
# of `path`'s "Longest serial chain" line) sum to a real, un-buyable-down
# floor, and nothing before this said the chain had a length at all.
# =============================================================================
_haz = sim(civ="han_china_100ad")
_floor_academy = _haz._calendar_floor_remaining("academy_network")
check("the strongest sack_chance hedge (academy_network, the 'copies of "
      "your work kept somewhere else' hedge) has a real calendar floor in "
      "the 20-30 year range from a standing start, matching what actually "
      "broke two playtesters, not a number invented for this fix",
      20.0 <= _floor_academy <= 30.0, _floor_academy)

_adv0 = _haz.hazard_advice("sack_chance")
check("hazard_advice carries that lead time from turn one, alongside the "
      "same words a playtester was actually given",
      "even_started_today_the_real_hedges_here_take_years" in _adv0
      and _adv0["what_would_help"] == ("walls, firearms, powerful friends, "
                                       "and copies of your work kept "
                                       "somewhere else"),
      _adv0.get("even_started_today_the_real_hedges_here_take_years"))
_range0 = _adv0["even_started_today_the_real_hedges_here_take_years"]
check("...and the slowest figure in that range is academy_network's own "
      "floor - the warning is not silently a different, easier hedge",
      (_range0["slowest"] if isinstance(_range0, dict) else _range0)
      == _floor_academy, (_range0, _floor_academy))

_steps0 = _haz.hedge_first_steps("sack_chance")
_academy_step = next((step for step in _steps0 if step["id"] == "academy_network"), None)
check("hedge_first_steps names academy_network's own total years, not just "
      "its own last, short leg (build_yrs 10 of a 30-year chain)",
      _academy_step is not None
      and _academy_step.get("years_even_if_you_start_today") == _floor_academy,
      _academy_step)

# THE FLOOR SHRINKS AS THE CHAIN IS ACTUALLY BUILT, and only by what is
# actually done - a player partway through sees what is left, not the whole
# chain re-quoted from scratch.
_haz2 = sim(civ="han_china_100ad")
_haz2.done.add("scientific_method"); _haz2.done.add("corpus_written")
_haz2._done_changed()
_floor_partial = _haz2._calendar_floor_remaining("academy_network")
check("...and once scientific_method and corpus_written are actually done, "
      "the remaining floor is smaller by exactly their own years, not "
      "recomputed from a standing start",
      abs(_floor_partial - (_floor_academy - NODES["scientific_method"]["yrs"]
                            - NODES["corpus_written"]["yrs"])) < 1e-6,
      (_floor_partial, _floor_academy))
check("...and once academy_network is done outright, nothing is left to "
      "wait for at all",
      "academy_network" not in {step["id"] for step in
                                run_it(sim(civ="han_china_100ad"),
                                       "scientific_method", "corpus_written",
                                       "corpus_dispersed", "endowment_land",
                                       "academy_network")
                                .hedge_first_steps("sack_chance")},
      None)

