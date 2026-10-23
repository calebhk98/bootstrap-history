"""Complaints/37: the founder-hours budget a screen prints and the one it judges against are one figure, read from one place. The
budget (`founder_budget`, `_founder_lifetime_hours`), the verdict (`path_is_feasible_alone`) and the mortality sweep's spread
(`_sweep_point_cfg`) are called on figures built here; the engine's own defaults are read as data."""

QUICK_TOPIC = True

from .harness import check

from sim.engine.data import DEFAULTS
from sim.ui.cli import _founder_lifetime_hours, _sweep_point_cfg
from sim.ui.founder_budget import founder_budget, path_is_feasible_alone

check("the budget is hours a year times working years, read from the defaults it is given",
      founder_budget({"founder_hours_per_year": 500, "founder_life_mean": 10}) == (500, 10, 5000), None)
check("a game's own config overrides either input", founder_budget({"founder_hours_per_year": 500, "founder_life_mean": 10},
                                                                   {"founder_hours_per_year": 100}) == (100, 10, 1000), None)
check("a config that names neither leaves the defaults", founder_budget({"founder_hours_per_year": 500, "founder_life_mean": 10}, {}) == (500, 10, 5000), None)
check("the screens' lifetime figure is the engine defaults' hours a year times its expected working years",
      _founder_lifetime_hours() == DEFAULTS["founder_hours_per_year"] * DEFAULTS["founder_life_mean"], None)
check("the screens' lifetime figure follows a game's config", _founder_lifetime_hours({"founder_hours_per_year": 500, "founder_life_mean": 10}) == 5000, None)

check("a path demanding fewer hours than a life holds is feasible alone", path_is_feasible_alone(4999, 5000) is True, None)
check("a path demanding as many hours as a life holds is not", path_is_feasible_alone(5000, 5000) is False, None)
check("a path demanding more is not, so shrinking the budget flips the verdict",
      path_is_feasible_alone(53830, founder_budget(DEFAULTS)[2]) is True and path_is_feasible_alone(53830, 5000) is False, None)

mortality_cfg, _life = _sweep_point_cfg("founder_life_mean", 20)
check("the mortality sweep draws founder lifespan at the defaults' own spread", mortality_cfg.get("founder_life_mean") == 20
      and mortality_cfg.get("founder_life_sd") == DEFAULTS["founder_life_sd"] and mortality_cfg["immortal"] is False, mortality_cfg)
