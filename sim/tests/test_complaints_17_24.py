"""Regression coverage for playtest complaints 17 through 24."""
from .harness import *  # noqa: F401,F403


# A mortality shock changes the screens and hiring multiplier immediately.
_plague = sim(civ="rome_100ad")
_plague.pop_deficit = 0.28
_plague._refresh_demographic_indexes(_plague.year)
_population = _plague.population_report()
check("plague mortality immediately lowers displayed current population",
      _population["population"] <
      _population["reference_population_before_simulated_changes"], _population)
check("plague mortality immediately raises wages",
      _plague.wage_index > _plague._wage_index_base, _plague.wage_index)

# The risk response says that staff loss is an independently repeated wave.
_risk = S._agent_dispatch(sim(civ="rome_100ad"), NODES, {"cmd": "risk"})
_antonine = next(h for h in _risk["knowledge_risk"]["known_hazards_ahead"]
                 if "Antonine" in h["name"])
check("plague risk exposes annual wave cadence and cumulative exposure",
      _antonine["staff_loss_wave_chance_per_year"] == 0.32
      and _antonine["remaining_annual_wave_checks"] > 1
      and _antonine["chance_of_at_least_one_staff_loss_wave"] > 0.32,
      _antonine)

# Bare rush is a preview; bounded or explicitly forced forms remain actions.
_rush = sim(capital=1_000_000)
_before = dict(_rush.active)
_preview = S._agent_dispatch(_rush, NODES, {"cmd": "rush"})
check("bare rush previews and does not mutate the portfolio",
      _preview.get("preview") and _preview.get("nothing_changed")
      and _rush.active == _before, _preview)
check("typed rush force is an explicit action", _PT("rush force")[0] ==
      {"cmd": "rush", "force": True}, _PT("rush force"))

# Phrase search does not require words to be adjacent in the display name.
_lap = sim(capital=1_000_000)
_lap.done.update(NODES["prc_lapping_plate"]["pre"])
_lap.done.add("ch2_process_bayer")
_lap.done.add("patron_local")
_lap.operating.add("patron_local")
_found = S._agent_available(_lap, NODES, {"find": "lapping plate", "all": True})
check("available phrase search includes a currently legal lapping plate",
      "prc_lapping_plate" in {r["id"] for r in _found["available"]}, _found)

# The two power projects require the capabilities claimed by their prose.
_hp_pre = set(NODES["en_high_pressure_engine"]["pre"])
check("high-pressure engine requires the established safe steam chain",
      {"steam_high_pressure", "thermodynamics_theory", "mat_bulk_steel"}
      <= _hp_pre, sorted(_hp_pre))
_gt_pre = set(NODES["en_gas_turbine"]["pre"])
check("Brayton turbine requires theory, compressor concept and hot alloys",
      {"air_jet_engine_concept", "thermodynamics_theory", "mat_nickel",
       "mat_tool_steel_hss"} <= _gt_pre, sorted(_gt_pre))
