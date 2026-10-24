"""A fixture economy with a state policy, for the scenario tests that open one (test_state_printing_scale_rule)."""
from sim.economy.economy import Economy
from sim.economy.state_policy import StatePolicy
from sim.economy.types import CurrencySpec
from sim.tests import economy_fixture as fixture

COIN = "coin"
STATE = "state:fixture"


def fiat_currency():
    return CurrencySpec(COIN, "fiat", None, 0.0, STATE, 0.0)


def opened(order=None, fiat=True, **policy_changes):
    policy = StatePolicy(financing_order=order or StatePolicy().financing_order, **policy_changes)
    changes = {"state_policy": policy}
    if fiat:
        changes["currency"] = fiat_currency()
    return Economy(fixture.small_setup(**changes))
