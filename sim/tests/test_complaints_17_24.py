"""Regression coverage for playtest complaints 17 through 24: each rule is called with inputs built here; the scenario
that keeps the mortality shock wired to the displayed population is test_complaints_17_24_scenario."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.engine.staff_loss_waves import wave_exposure
from sim.ui.proto import tree_filters

# --- the staff-loss wave exposure over the years left (the rule behind the `risk` reply)
_wave = 0.32
_exposure = wave_exposure(_wave, 0.1, 165, 180, 100)
check("a hazard still ahead is checked once for every year it runs",
      _exposure["remaining_annual_wave_checks"] == 16, _exposure)
check("a hazard under way is checked only for the years left",
      wave_exposure(_wave, 0.1, 165, 180, 170)["remaining_annual_wave_checks"] == 11)
check("a hazard past its last year still counts one check, never zero",
      wave_exposure(_wave, 0.1, 165, 180, 400)["remaining_annual_wave_checks"] == 1)
check("the chance of at least one wave is one minus every year passing, and exceeds a single year's chance",
      abs(_exposure["chance_of_at_least_one_staff_loss_wave"] - round(1.0 - (1.0 - _wave) ** 16, 4)) < 1e-12
      and _exposure["chance_of_at_least_one_staff_loss_wave"] > _wave, _exposure)
check("the expected cumulative loss is one minus every wave sparing, each wave costing its share",
      abs(_exposure["expected_cumulative_staff_loss"] - round(1.0 - (1.0 - _wave * 0.1) ** 16, 4)) < 1e-12, _exposure)
check("a hazard that costs no staff exposes none",
      wave_exposure(_wave, 0.0, 165, 180, 100)["expected_cumulative_staff_loss"] == 0.0)

# --- DUPLICATE: bare rush previews and changes nothing. Held by test_rush_fiscal_controls ("rush preview changes no
# state", "rush preview says nothing was changed").
check("typed rush force is an explicit action", _PT("rush force")[0] ==
      {"cmd": "rush", "force": True}, _PT("rush force"))

# --- phrase search does not require words to be adjacent in the display name
_names = {"prc_lapping_plate": {"name": "Lapping with cast-iron plate and abrasive compound", "cat": "machine_tools",
                                "pre": []},
          "other": {"name": "Weaving with a loom", "cat": "textiles", "pre": []}}
check("a phrase search matches a name that holds its words apart",
      tree_filters.matches_find(_names, "lapping plate", "prc_lapping_plate"))
check("...and not a name that holds neither word", not tree_filters.matches_find(_names, "lapping plate", "other"))
check("...and not a name that holds only one of them",
      not tree_filters.matches_find(_names, "lapping loom", "prc_lapping_plate"))

# --- the two power projects require the capabilities claimed by their prose (data, no game)
_hp_pre = set(NODES["en_high_pressure_engine"]["pre"])
check("high-pressure engine requires the established safe steam chain",
      {"steam_high_pressure", "thermodynamics_theory", "mat_bulk_steel"}
      <= _hp_pre, sorted(_hp_pre))
_gt_pre = set(NODES["en_gas_turbine"]["pre"])
check("Brayton turbine requires theory, compressor concept and hot alloys",
      {"air_jet_engine_concept", "thermodynamics_theory", "mat_nickel",
       "mat_tool_steel_hss"} <= _gt_pre, sorted(_gt_pre))
