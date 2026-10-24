"""_score_achievements on a stand-in sim: each achievement is a plain condition on saved fields; closing a concern for want of
staff costs never_understaffed for good, closing by choice does not."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.ui.proto.score import _score_achievements


def stand_in(ever_closed_for_staff=(), shut_for_staff=None, forgotten=None, insolvent_years=0, slaves=0):
    return SimpleNamespace(
        goal="goal", goal_year=150, cfg={"start_year": 100}, forgotten=forgotten, shut_for_staff=shut_for_staff,
        state=SimpleNamespace(projects=SimpleNamespace(ever_closed_for_staff=set(ever_closed_for_staff))),
        insolvent_years=insolvent_years, interest_paid=0.0, slaves=slaves, manumitted_total=0)


def won(sim, name):
    return _score_achievements(sim, {})[name]["won"]


check("with nothing closed for staff the achievement is held", won(stand_in(), "never_understaffed"))
check("a concern that closed for staff and has since reopened still costs it",
      not won(stand_in(ever_closed_for_staff={"school_founded"}), "never_understaffed"))
check("a concern shut for staff now costs it", not won(stand_in(shut_for_staff={"school_founded"}), "never_understaffed"))
check("a sacked corpus costs corpus_intact", not won(stand_in(forgotten={"x": 1}), "corpus_intact") and won(stand_in(), "corpus_intact"))
check("a year of insolvency costs clean_ledger", not won(stand_in(insolvent_years=1), "clean_ledger") and won(stand_in(), "clean_ledger"))
check("owning a slave costs free_hands_only", not won(stand_in(slaves=1), "free_hands_only") and won(stand_in(), "free_hands_only"))
check("a run with no goal reached has no achievements",
      _score_achievements(SimpleNamespace(goal=None, goal_year=None), {}) == {})
