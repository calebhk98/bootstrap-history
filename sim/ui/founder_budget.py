"""The founder's lifetime-hours budget the path and why screens print and judge against: one source for the figure and the verdict."""


def founder_budget(defaults, cfg=None):
    """(hours a year, expected working years, hours in a whole working life), each read from `cfg` when it names it and
    otherwise from `defaults`: the same keys the engine's hours ledger and mortality draw read."""
    cfg = cfg or {}
    hours_per_year = cfg.get("founder_hours_per_year", defaults["founder_hours_per_year"])
    working_years = cfg.get("founder_life_mean", defaults["founder_life_mean"])
    return hours_per_year, working_years, hours_per_year * working_years


def path_is_feasible_alone(hours_demanded, lifetime_hours):
    """Whether one founder's whole working life holds the hours a path demands."""
    return hours_demanded < lifetime_hours
