"""The names a data file's state path may start with: figures, `read` commands and policy conditions in data/ui and in mods.
Each declared name answers from a view; any other name is read off the `Sim` as an attribute, as before. A path reads only: no step starts with `_`."""

# name -> (view, key): `view()` or, with a key, `view()[key]`
ROOTS = {
    "capital": ("acting_balance", None), "year": ("year", None), "cfg": ("game_config", None), "civ": ("civilisation", None),
    "end_year": ("horizon_end_year", None), "price_index": ("price_index", None), "wage_index": ("wage_index", None),
    "population": ("population", None), "pop_scale": ("pop_scale", None), "money_real": ("money_real", None),
    "done": ("techniques_held", None), "granted": ("techniques_granted", None), "revealed": ("techniques_revealed", None),
    "forgotten": ("techniques_forgotten", None), "done_year": ("done_year", None), "active": ("active_projects", None),
    "operating": ("operating", None), "mothballed": ("mothballed", None), "bountied": ("bountied", None),
    "bounties_paid": ("bounties_paid", None), "failed_attempts": ("failed_attempts", None),
    "paid_towards": ("paid_towards", None), "shut_for_staff": ("shut_for_staff", None),
    "fog": ("legacy_fog", None), "fuzzy_estimates": ("legacy_fuzzy_estimates", None),
    "goal": ("goal", "node"), "goal_year": ("goal", "year"), "policy": ("founder", "policy"),
    "dead_reason": ("founder", "dead_reason"), "founder_alive": ("founder", "alive"), "life_left": ("founder", "life_left"),
    "reputation": ("standing", "reputation"), "scandal": ("standing", "scandal"), "protection": ("standing", "protection"),
    "familiarity": ("standing", "familiarity"), "scandal_last_year": ("standing", "scandal_last_year"),
    "eminence": ("eminence", None),
    "insolvent_years": ("debt_status", "insolvent_years"), "credit_frozen_until": ("debt_status", "credit_frozen_until"),
    "bondage_debt": ("debt_status", "bondage_debt"), "bondage_years_left": ("debt_status", "bondage_years_left"),
    "interest_paid": ("debt_status", "interest_paid"),
    "revenue": ("revenue_estimate", None), "revenue_sources": ("revenue_sources", None), "upkeep": ("upkeep", None),
    "upkeep_by_concern": ("upkeep_by_concern", None),
}


def declared(name):
    return name in ROOTS


def root_value(sim, name):
    """What the declared name `name` holds now."""
    view, key = ROOTS[name]
    value = sim.view(view)()
    return value if key is None else value[key]

