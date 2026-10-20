"""Complaint 585: staff paid the going wage leave only at the rate the market moves workers; underpaid staff may go."""
import random

from .harness import *  # noqa: F401,F403
from sim.engine.staff_replacement import REPLACE_ONLY
from sim.refusal import facts_of
from sim.labour.market.clearing import on_the_job_loss_share


# a trade whose national pool is large, so a replacement search is not limited by the pool (the generic artisan trade is a remnant)
STAFF_TRADE = "labourer"


def staffed_game(head=40):
    game = sim(capital=5_000_000.0)
    game.state.household.employees.update({STAFF_TRADE: float(head)})
    game.labour.resync_pools()
    game.state.household.log.clear()
    return game


# the market's own rule: nothing leaves a payer that pays as much as the rival, something leaves one that pays less
check("the market moves nobody off an employer paying the going wage", on_the_job_loss_share(100.0, 100.0) == 0.0)
check("...or paying more", on_the_job_loss_share(120.0, 100.0) == 0.0)
check("...but moves some off one paying less", 0.0 < on_the_job_loss_share(80.0, 100.0) <= 1.0)

# paid the going wage: nobody takes a better offer, whatever the market's wage does
paid = staffed_game()
market = paid.labour.labour_market.quote_annual(STAFF_TRADE)
check("pay kept at the market is the default policy", paid.state.founder.policy["keep_pay_at_market"] is True)
check("staff paid at the going wage have no chance of a better offer", paid.labour.offer_loss_share(STAFF_TRADE) == 0.0)
_died, _left = paid.labour.roll_staff_year(random.Random(5))
check("...and none leave for one in a year", not _left, _left)
paid.labour.labour_market.quote_annual = lambda trade, *args, **kwargs: market * 3.0    # the market's wage trebles
check("with the keep-pay policy on, the wage bill follows the market up",
      paid.labour.labour_market.quote_annual(STAFF_TRADE) > market * 2.0
      and abs(paid.labour.wage_bill() - paid.state.household.employees.get(STAFF_TRADE, 0.0)
              * paid.labour.labour_market.quote_annual(STAFF_TRADE)) < 1e-6)
check("...and staff still have no better offer", paid.labour.offer_loss_share(STAFF_TRADE) == 0.0)

# pay left at the hire-time figure while the market rises: the staff may go
frozen = staffed_game()
frozen.labour.settle_staff_pay()
frozen.state.founder.policy["keep_pay_at_market"] = False
_hire_time_wage = frozen.labour.labour_market.quote_annual(STAFF_TRADE)
frozen.labour.labour_market.quote_annual = lambda trade, *args, **kwargs: _hire_time_wage * 3.0
check("with the policy off, pay stays at the settled figure while the market rises",
      frozen.labour.staff_pay(STAFF_TRADE) < frozen.labour.labour_market.quote_annual(STAFF_TRADE) / 2.0)
check("...and staff paid below the market may take better offers", frozen.labour.offer_loss_share(STAFF_TRADE) > 0.0)
_died, _left = frozen.labour.roll_staff_year(random.Random(5))
check("...some of them do", sum(_left.values()) > 0, (_died, _left))

# deaths and offers are logged apart, the offers with the cause better_offers
leaving = staffed_game(10)
leaving.state.founder.policy["keep_pay_at_market"] = False
leaving.state.household.staff_pay_held[STAFF_TRADE] = 1.0
leaving._step_staff()
_loss_facts = [facts_of(line) for _year, line in leaving.state.household.log
               if str(getattr(line, "kind", "")).startswith("staff_lost")]
check("underpaid staff who leave are logged as better offers",
      any(("reason", "better_offers") in facts.items() for facts in _loss_facts), _loss_facts)

# lost staff are replaced when the policy says so
dying = staffed_game(10)
dying.state.founder.policy["auto_hire"] = REPLACE_ONLY
dying.state.founder.policy["keep_pay_at_market"] = False
dying.state.household.staff_pay_held[STAFF_TRADE] = 1.0
dying._step_staff()
check("replace-only auto_hire brings the staff back to the head it lost",
      dying.state.household.employees.get(STAFF_TRADE, 0.0) >= 9.0, dying.state.household.employees)
