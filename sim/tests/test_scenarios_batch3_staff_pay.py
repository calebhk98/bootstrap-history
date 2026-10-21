"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario: the household's staff pay follows the policy; underpaid staff leave as logged
better offers and replace-only hiring brings them back. The rules are plain functions with tests of their own:
test_complaint_585_staff_pay_retention (pay, settling, the roll) and test_complaint_579_staff_loss_events (the log line)."""
import random

from .harness import *  # noqa: F401,F403
from sim.engine.staff_replacement import REPLACE_ONLY
from sim.refusal import facts_of

STAFF_TRADE = "labourer"   # a trade whose national pool is large, so a replacement search is not limited by the pool


def staffed_game(head=40):
    game = sim(capital=5_000_000.0)
    game.state.household.employees.update({STAFF_TRADE: float(head)})
    game.labour.resync_pools()
    game.state.household.log.clear()
    return game


_paid = staffed_game()
_market = _paid.labour.labour_market.quote_annual(STAFF_TRADE)
_paid_died, _paid_left = _paid.labour.roll_staff_year(random.Random(5))
_paid.labour.labour_market.quote_annual = lambda trade, *args, **kwargs: _market * 3.0    # the market's wage trebles
check("scenario staff pay: with the keep-pay policy on, the wage bill follows the market up and nobody leaves for a better offer",
      not _paid_left and _paid.labour.offer_loss_share(STAFF_TRADE) == 0.0
      and abs(_paid.labour.wage_bill() - _paid.state.household.employees.get(STAFF_TRADE, 0.0) * _market * 3.0) < 1e-6,
      (_paid_left, _paid.labour.wage_bill()))
_frozen = staffed_game()
_frozen.labour.settle_staff_pay()
_frozen.state.founder.policy["keep_pay_at_market"] = False
_hire_time_wage = _frozen.labour.labour_market.quote_annual(STAFF_TRADE)
_frozen.labour.labour_market.quote_annual = lambda trade, *args, **kwargs: _hire_time_wage * 3.0
_frozen_died, _frozen_left = _frozen.labour.roll_staff_year(random.Random(5))
check("scenario staff pay: with the policy off, pay stays at the settled figure while the market rises, and some staff go",
      _frozen.labour.staff_pay(STAFF_TRADE) < _hire_time_wage * 3.0 / 2.0
      and _frozen.labour.offer_loss_share(STAFF_TRADE) > 0.0 and sum(_frozen_left.values()) > 0, (_frozen_died, _frozen_left))
_leaving = staffed_game(10)
_leaving.state.founder.policy["keep_pay_at_market"] = False
_leaving.state.household.staff_pay_held[STAFF_TRADE] = 1.0
_leaving._step_staff()
_loss_facts = [facts_of(line) for _year, line in _leaving.state.household.log
               if str(getattr(line, "kind", "")).startswith("staff_lost")]
check("scenario staff pay: underpaid staff who leave are logged as better offers",
      any(("reason", "better_offers") in facts.items() for facts in _loss_facts), _loss_facts)
_dying = staffed_game(10)
_dying.state.founder.policy["auto_hire"] = REPLACE_ONLY
_dying.state.founder.policy["keep_pay_at_market"] = False
_dying.state.household.staff_pay_held[STAFF_TRADE] = 1.0
_dying._step_staff()
check("scenario staff pay: replace-only auto_hire brings the staff back to the head it lost",
      _dying.state.household.employees.get(STAFF_TRADE, 0.0) >= 9.0, _dying.state.household.employees)
