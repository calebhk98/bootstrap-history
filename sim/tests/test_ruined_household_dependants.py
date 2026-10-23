"""Complaint 524: a household in arrears whose income does not cover its costs cannot keep every dependant, so
debt stops growing past the credit limit. The rule is called on inputs the test builds; the money phase is in the scenario."""

from .harness import *  # noqa: F401,F403

from sim.engine.economy_debt_service import dependants_beyond_means_of

QUICK_TOPIC = True

DEPENDANTS = 100.0
LIVING = 400.0
UPKEEP = 50.0
RATE = 0.1
CREDITORS_SHARE = 0.5


def beyond(capital, revenue):
    return dependants_beyond_means_of(capital, DEPENDANTS, LIVING, revenue, UPKEEP, 0.0, RATE, CREDITORS_SHARE)


check("a household with money and an income that covers its costs keeps every dependant", beyond(1000.0, 1.0e9) == 0.0)
check("a household with money but no income sheds all its dependants", abs(beyond(1000.0, 0.0) - DEPENDANTS) < 1e-9)
check("a household in arrears whose income covers its costs keeps every dependant", beyond(-10.0, 1.0e9) == 0.0)
check("a household in arrears with no income sheds all its dependants and no more", abs(beyond(-10.0, 0.0) - DEPENDANTS) < 1e-9)
income_for_half = (LIVING - DEPENDANTS + DEPENDANTS / 2.0 / (1.0 - CREDITORS_SHARE) + UPKEEP + 10.0 * RATE)
check("a household in arrears keeps the dependants its surplus carries once the creditors have their share",
      abs(beyond(-10.0, income_for_half) - DEPENDANTS / 2.0) < 1e-6, beyond(-10.0, income_for_half))
check("the same income in credit keeps more dependants than in arrears: no creditors' share and no interest",
      beyond(1000.0, income_for_half) < beyond(-10.0, income_for_half))
