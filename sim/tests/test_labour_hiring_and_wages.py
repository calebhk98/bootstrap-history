"""Hiring, training and commissioning a trade; wage pricing and its
forecast; the founder's own practice income; and a dead founder's effect on
all of it.
"""
from .harness import *  # noqa: F401,F403


def _ask(household, command, **arguments):
    return S._agent_dispatch(household, NODES, dict(cmd=command, **arguments))


# One game serves the practice, training, hiring, commissioning and death checks.
household = sim(capital=5000000.0)

# --- The practice paid a third of the quoted figure with nothing saying so.
_practice = sorted(household._practice_set())
_expected_revenue = sum(NODES[node_id]["rev"] for node_id in _practice) * household.PRACTICE_SHARE
check("the practice pays its share of the quoted figure, not a ramp step",
      abs(household.revenue() - _expected_revenue) < 1e-3 * _expected_revenue,
      (household.revenue(), _expected_revenue))
check("a concern you opened is NOT described as your practice",
      all(node_id in household.granted for node_id in _practice), _practice[:3])

# --- `work` silently took the hours out of the practice.
_work = _ask(household, "work", trade="scribe", hours=500)
check("selling your hours says what it cost your own practice",
      _work.get("it_cost_your_own_practice", 0) > 0.5, _work)
check("...and says what you are actually up on the trade",
      abs((_work["earned"] - _work["it_cost_your_own_practice"]) - _work["so_you_are_up"]) < 0.11, _work)

# --- Dismissing a trade you are teaching must cancel the apprenticeship.
_trained, _ = household.labour.train("machinist", 3)
check("teaching a trade puts people in training", _trained and household.training, household.training)
_fired, _fire_note = household.labour.fire("machinist", 3)
check("dismissing a trade you are teaching cancels the apprenticeship",
      _fired and not [record for record in household.training if len(record) > 3 and record[2] == "machinist"],
      (_fire_note, household.training))
check("firing a trade you neither employ nor teach is still refused",
      household.labour.fire("machinist", 1)[0] is False, household.labour.fire("machinist", 1)[1])

# --- Leaning on a scarce trade must show in its quoted price. Millwright is
# the scarcest useful trade; a common trade has a town's worth of pool.
_base_quote = _ask(household, "labour", trade="millwright")["trade"]["a_year_of_one"]
for _ in range(6):
    household.labour.hire("millwright", 3)
_dear = _ask(household, "labour", trade="millwright")["trade"]
check("leaning on a trade shows up in its quoted price, not only in the bill",
      _dear["a_year_of_one"] > _base_quote, (_base_quote, _dear["a_year_of_one"]))
check("...and says why, and what brings it back down",
      _dear.get("dearer_than_usual_by") and "supply" in (_dear.get("because") or ""), _dear.get("because"))

# --- An abundant trade is not flagged as price-moving from one hire.
_abundant = _ask(household, "labour", trade="labourer")["trade"]
check("an abundant trade's quote is not flagged as price-moving from one hire",
      not _abundant.get("hiring_moves_the_price"), _abundant)

# --- Engineers count as scholars and cannot supervise a workshop.
check("a trade says whether it is scholar or craftsman",
      _ask(household, "labour", trade="engineer")["trade"].get("kind") == "scholar")

# --- Commissioning: two bounded channels.
_ceiling = household.labour.market_supply("scribe")
_pool_before = household.labour.market_supply_split("scribe")[0]
household.labour.commission("scribe", _ceiling * 0.9)
check("commissioning does not raise how many of a trade LIVE here",
      abs(household.labour.market_supply_split("scribe")[0] - _pool_before) < 1e-6,
      household.labour.market_supply_split("scribe")[0])
check("...and it does add hours you can actually call on",
      household.labour.hours_you_can_call_on("scribe") > _ceiling, (_ceiling, household.labour.hours_you_can_call_on("scribe")))
check("...and you cannot commission past what the trade here can spare",
      household.labour.commission("scribe", _ceiling)[0] is False, household.labour.commission("scribe", _ceiling)[1])
_scribe_trade = _ask(household, "labour", trade="scribe")["trade"]
check("...and `labour` names both channels, not one ceiling",
      _scribe_trade.get("hours_you_could_still_commission") is not None
      and _scribe_trade.get("hours_available_to_you_in_all") >= _scribe_trade.get("hours_the_market_can_supply"),
      _scribe_trade)

# --- A dead founder kept playing: practice fees, hiring and selling hours.
_alive_revenue = household.revenue()
household.founder_alive = False
check("a dead physician has no practice",
      _alive_revenue > 0 and household.revenue() == 0.0, (_alive_revenue, household.revenue()))
check("...and cannot sell hours he does not have",
      household.labour.work_for_wages("scholar", 100)[0] == 0.0, household.labour.work_for_wages("scholar", 100)[1])
check("...and cannot take anyone on with no deputy to direct them",
      _ask(household, "hire", trade="smith", n=1).get("ok") is False,
      _ask(household, "hire", trade="smith", n=1))

# --- A scarce trade's quote forecasts what hiring one now would do to every one of that trade.
household_forecast = sim(civ="norse_900ad", capital=None)
household_forecast.capital = 560.0
_before_hire = _ask(household_forecast, "labour", trade="scholar")["trade"]
check("the quote for a scarce trade forecasts what hiring one now would "
      "make EVERY one of that trade cost - not just today's market price",
      _before_hire.get("hiring_moves_the_price") is True
      and _before_hire["a_year_of_one_after_you_hire_one"] > _before_hire["a_year_of_one"],
      (_before_hire.get("a_year_of_one"), _before_hire.get("a_year_of_one_after_you_hire_one")))
household_forecast.capital = 1.2 * _before_hire["a_year_of_one_after_you_hire_one"]
check("...and it is the real forecast: hiring one for real lands on the number quoted",
      abs(_ask(household_forecast, "hire", trade="scholar", n=1)["annual_wage_bill"]
          - _before_hire["a_year_of_one_after_you_hire_one"]) < 1.0,
      _before_hire["a_year_of_one_after_you_hire_one"])

# --- Trained apprentices join the staff by the year named, and the practice
# does not ramp up over those years.
household_training = sim(capital=100000.0)
_practice_expected = sum(NODES[node_id]["rev"] for node_id in sorted(household_training._practice_set())) \
    * household_training.PRACTICE_SHARE
_trained, _train_message = household_training.labour.train("machinist", 2, None)
for _ in range(3):
    household_training.step()
check("trained apprentices are really on the books, unprompted, by the year named",
      _trained and household_training.employees.get("machinist", 0.0) >= 1.999,
      (_train_message, household_training.employees.get("machinist")))
check("...and the practice does not grow into the full figure over the ramp years",
      abs(household_training.revenue() - _practice_expected) < 1e-3 * _practice_expected,
      (household_training.revenue(), _practice_expected))

# --- A trade you taught counts as gone once the last one died, and is taught
# again; but not every year (the cooldown is per trade).
household_lost = sim(capital=2000000.0, manual=False)
household_lost.trades_created.add("machinist")          # taught once, long ago
household_lost.employees.pop("machinist", None)
household_lost.labour._resync_pools()
household_lost.initialize_project("air_artificial_horizon")
check("a trade taught and then lost counts as gone, not as available",
      household_lost.labour.trade_available("machinist") and household_lost.labour.market_supply("machinist") <= 0.0,
      (household_lost.labour.trade_available("machinist"), household_lost.labour.market_supply("machinist")))
for _ in range(6):
    if "air_artificial_horizon" not in household_lost.active:
        household_lost.initialize_project("air_artificial_horizon")
    household_lost.step()
    if household_lost.labour.market_supply("machinist") > 0 or household_lost.labour._trade_headcount_pending("machinist") > 0:
        break
check("...and the engine teaches it again rather than skipping every node that needs it",
      household_lost.labour.market_supply("machinist") > 0 or household_lost.labour._trade_headcount_pending("machinist") > 0,
      (household_lost.labour.market_supply("machinist"), household_lost.labour._trade_headcount_pending("machinist")))


def _lose_machinists_again(household_to_reset):
    household_to_reset.employees.pop("machinist", None)
    household_to_reset.training = [record for record in household_to_reset.training
                                   if not (len(record) > 3 and record[2] == "machinist")]
    household_to_reset.labour._resync_pools()
    if "air_artificial_horizon" not in household_to_reset.active:
        household_to_reset.initialize_project("air_artificial_horizon")


# The re-teach pass itself: a lost trade a project in hand needs is taught
# again, but not within a generation of the last time it was taught.
household_lost.last_taught["machinist"] = household_lost.year - 1
_lose_machinists_again(household_lost)
household_lost._step_teach_trades()
check("...and does not teach the same trade again inside the cooldown",
      household_lost.last_taught["machinist"] == household_lost.year - 1,
      (household_lost.year, household_lost.last_taught["machinist"]))
household_lost.last_taught["machinist"] = household_lost.year - household_lost.RETEACH_EVERY
_lose_machinists_again(household_lost)
household_lost._step_teach_trades()
check("...but teaches it again once the cooldown has passed",
      household_lost.last_taught["machinist"] == household_lost.year,
      (household_lost.year, household_lost.last_taught["machinist"]))
