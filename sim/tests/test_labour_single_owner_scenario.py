"""Complaint 556 scenario (Complaint 640 audit): in a whole game the labour core, the town-supply estimate and the
founder's hire agree. The book accessors and the wall are rule tests in test_labour_single_owner."""
from sim.labour import legacy_trade_defaults, trade_data

from .harness import *  # noqa: F401,F403

game = sim(capital=5_000_000.0)
labour = game.labour
household = game.state.household
core = labour.core_people_by_trade()

# ---- one count of people by trade: the estimate is a view of the core's headcount ----
SMALL_TOLERANCE = 0.01
staffed = {trade: people for trade, people in core.items() if people > 0.0}
for trade, people in sorted(staffed.items()):
    estimate = labour.national_trade_population(trade)
    if not labour.trade_available(trade) or trade in labour._world.trades_absent:
        continue
    if trade_data.scholar_trade() == trade or trade_data.drawn_from_unskilled_pool(trade) \
            or trade in legacy_trade_defaults.LETTERED_BUT_NOT_LITERATE \
            or trade_data.literate_trades(trade_data.registry_of(game), (trade,)):
        continue   # trades counted off literacy or the draft, not the headcount
    check("the estimate of %s agrees with the core's people" % trade,
          abs(estimate - people) <= SMALL_TOLERANCE * people, (people, estimate))
farm_people = core.get("farmer", 0.0)
check("farm people are farmers in the core: most of the working age", farm_people > 0.5 * game.population.working_age,
      (farm_people, game.population.working_age))
check("the unskilled pool is the people the labourer's own work needs, not the country",
      core.get("labourer", 0.0) < 0.5 * farm_people, (core.get("labourer"), farm_people))
counted = [trade for trade in staffed if abs(labour.national_trade_population(trade) - staffed[trade]) <= SMALL_TOLERANCE * staffed[trade]]
check("national totals are equal over the trades the estimate reads from the core",
      abs(sum(staffed[trade] for trade in counted) - sum(labour.national_trade_population(trade) for trade in counted)) < 1e-6 * sum(staffed.values()))
check("the core holds the working age and the farm people are the biggest trade",
      abs(sum(staffed.values()) - game.population.working_age) < 0.01 * game.population.working_age
      and max(staffed, key=staffed.get) == "farmer", (sum(staffed.values()), game.population.working_age))


# ---- a hire is a reservation under the supply, and the core does not see it yet ----
core_before = dict(core)
hired, reply = labour.hire("labourer", 3)
check("the hire went through", hired, reply)
check("the founder's book holds the hired people", labour.employed("labourer") == 3.0, labour.employed("labourer"))
check("reserved people include the book", labour.reserved_people("labourer") >= 3.0)
check("reserved hours are people times hours a person-year",
      abs(labour.reserved_hours("labourer") - labour.reserved_people("labourer") * game.HOURS_PER_PERSON_YEAR) < 1e-6)
check("the hire is invisible to the core's people (known gap: reservations are not yet taken from the core)",
      labour.core_people_by_trade().get("labourer") == core_before.get("labourer"))
for trade in sorted(labour.employed_by_trade()):
    check("reservations of %s never exceed the supply the owner reports" % trade,
          labour.reserved_people(trade) <= labour.supplied_people(trade) + 1e-9,
          (labour.reserved_people(trade), labour.supplied_people(trade)))
    check("unreserved people of %s are never negative" % trade, labour.unreserved_people(trade) >= 0.0)

