"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario: the household's staff pay follows the policy; underpaid staff leave as logged
better offers and replace-only hiring brings them back. The rules are plain functions with tests of their own:
test_complaint_585_staff_pay_retention (pay, settling, the roll), test_complaint_579_staff_loss_events (the log line)
and test_automation_modes (replace-only rehire). What stays here is that the yearly staff step calls them."""
from .harness import *  # noqa: F401,F403
from sim.engine.staff_replacement import REPLACE_ONLY
from sim.refusal import facts_of

STAFF_TRADE = "labourer"   # a trade whose national pool is large, so a replacement search is not limited by the pool


def staffed_game(head=40):
    game = unopened_sim(capital=5_000_000.0)
    game.state.household.employees.update({STAFF_TRADE: float(head)})
    game.labour.resync_pools()
    game.state.household.log.clear()
    return game


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
