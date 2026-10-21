"""Scenario (Complaint 640): a Han game announces the hedge against being sacked with the lead time it really takes.

Two playtesters were told from turn one that the hedge was "walls, firearms, powerful friends, and copies of your work
kept somewhere else", acted on it, and were still sacked: the strongest of those hedges sits behind a chain decades
long, and nothing said the chain had a length. The floor arithmetic is in test_hedge_chain.py; this holds the advice
a running game builds from it."""
from .harness import *  # noqa: F401,F403

_haz = sim(civ="han_china_100ad")
_floor_academy = _haz._calendar_floor_remaining("academy_network")

_adv0 = _haz.hazard_advice("sack_chance")
check("hazard_advice carries that lead time from turn one, alongside the same words a playtester was given",
      "even_started_today_the_real_hedges_here_take_years" in _adv0
      and _adv0["what_would_help"] == ("walls, firearms, powerful friends, and copies of your work kept somewhere else"),
      _adv0.get("even_started_today_the_real_hedges_here_take_years"))
_range0 = _adv0["even_started_today_the_real_hedges_here_take_years"]
check("...and the slowest figure in that range is academy_network's own floor, not a silently easier hedge",
      (_range0["slowest"] if isinstance(_range0, dict) else _range0) == _floor_academy, (_range0, _floor_academy))

_steps0 = _haz.hedge_first_steps("sack_chance")
_academy_step = next((step for step in _steps0 if step["id"] == "academy_network"), None)
check("hedge_first_steps names academy_network's own total years, not just its own last, short leg",
      _academy_step is not None and _academy_step.get("years_even_if_you_start_today") == _floor_academy, _academy_step)

_haz2 = sim(civ="han_china_100ad")
_haz2.done.add("scientific_method")
_haz2.done.add("corpus_written")
_haz2._done_changed()
check("the game's remaining floor follows what is done, as the plain arithmetic does",
      abs(_haz2._calendar_floor_remaining("academy_network") - (_floor_academy - NODES["scientific_method"]["yrs"]
                                                               - NODES["corpus_written"]["yrs"])) < 1e-6,
      (_haz2._calendar_floor_remaining("academy_network"), _floor_academy))
check("...and once academy_network is done outright, it is no longer among the first steps",
      "academy_network" not in {step["id"] for step in
                                run_it(sim(civ="han_china_100ad"), "scientific_method", "corpus_written",
                                       "corpus_dispersed", "endowment_land", "academy_network")
                                .hedge_first_steps("sack_chance")}, None)
