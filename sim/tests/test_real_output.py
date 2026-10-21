"""Complaints 101, 112, 354, 640: output is the quantity of goods the market clears, valued at fixed opening prices.

Rules are tested on plain values: the arithmetic in test_real_output_measure (the sum of quantities times opening
prices, the baseline year worth the opening basket, new goods at their introduction price), the gate rule in
test_engine_prices (a technology gates a production entry or it changes no recipe), a cheaper entry's price and
quantity in test_cheaper_entry_lowers_price. This file is the whole-game scenario that the wiring joins them: the
Sim reads the economy's own basket and baseline, society output is that less those under arms, and a population
that falls without a technique leaves output per head near where it would have been undisturbed (a relationship, with a stated band)."""
from .harness import *  # noqa: F401,F403
from .real_output_helpers import close_years

from sim.economy import api as economy_api
from sim.engine.agents_port import SimWorld

# --- the Sim reads the economy's own basket and baseline.
game = sim(civ="rome_100ad", capital=1e9)
check("output per head is one before any year has run", game.real_output_per_head() == 1.0, game.real_output_per_head())
close_years(game, 1)
economy = game.economy.agent.economy()
check("...and at the baseline, the first settled year",
      abs(game.real_output_per_head() - 1.0) <= 1e-9, game.real_output_per_head())
basket = game.base_basket()
opening = economy_api.opening_quantities(economy)
check("the opening basket is the economy's own, every good in it",
      all(abs(basket["units"][good] - opening[good]) <= 1e-12 * opening[good] for good in basket["units"])
      and set(basket["units"]) <= set(opening) and bool(basket["units"]))
baseline = game.economy.agent.stored["volume_baseline"]
check("the baseline holds every good the economy traded in its first year",
      all(baseline.get(good, 0.0) > 0.0 for good in basket["units"] if economy_api.traded_volumes(economy).get(good, 0.0) > 0.0))
check("the engine keeps no volume of its own: no follower of the economy's cleared volumes, no reference tonnes split",
      not hasattr(game, "_follow_cleared_volumes") and not hasattr(game, "traded_ratio"))

# --- society output is the real output less the share of working people under arms, in this civilisation's money.
_world = SimWorld(game)
_producing = max(0.0, game.population.working_age - _world.soldiers_under_arms()) / game.population.working_age
_expected = (game.real_output_hours() * _producing * game.labour.money_per_labour_hour()
             * game.state.economy.output_factor)
check("society output is the real output, less the share of working people under arms, in this civilisation's money",
      abs(_world.society_output() - _expected) <= 1e-9 * _expected, (_world.society_output(), _expected))

# --- BASELINE VALIDATION (CLAUDE.md 4.2): a population that falls without a technique lowers output with the people
# and leaves output per head within a quarter of where it would have been. The quarter is a declared band, not a
# sourced figure. The reference is a run of the same game with no fall, closed the same number of years: the first
# settled year is a ramp (the economy's plants and stocks are still settling), so it is no stand-in for "where it was".
PER_HEAD_BAND = 0.25
YEARS_AFTER_FALL = 2
undisturbed = sim(civ="rome_100ad", capital=1e9)
close_years(undisturbed, 1 + YEARS_AFTER_FALL)
fallen = sim(civ="rome_100ad", capital=1e9)
close_years(fallen, 1)
people_before = fallen.population.total
fallen._apply_population_mortality_shock(0.4)
close_years(fallen, YEARS_AFTER_FALL)
check("validation: a population fall without a technique lowers real output against the same years undisturbed",
      fallen.real_output_hours() < undisturbed.real_output_hours(),
      (undisturbed.real_output_hours(), fallen.real_output_hours()))
check("validation: ...but not output per head, which stays near where it would have been",
      abs(fallen.real_output_per_head() / undisturbed.real_output_per_head() - 1.0) <= PER_HEAD_BAND,
      (undisturbed.real_output_per_head(), fallen.real_output_per_head(), people_before, fallen.population.total))
