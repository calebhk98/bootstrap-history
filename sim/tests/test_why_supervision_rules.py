"""The supervision block of `why` (Complaint 640): the standing crew `open` enforces is shown as given, on a stub game
that answers only what the block asks."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.tests.ui_stand_in import StandIn
from sim.ui.proto.techtree import _staffing_standing_crew

stub = StandIn(opening_fee=lambda node_id, units=None: (250.0, None), venture_foreman_free=lambda trade, excluding=None: 0.5)


def block(is_venture=True, supervision=(1.234, 2.678), free=(9.0, 9.0), foreman=(None, 0.0)):
    return _staffing_standing_crew(stub, "any_node", is_venture, supervision[0], supervision[1], free[0], free[1],
                                   foreman[0], foreman[1])


check("the supervision figure is the figure given by the crew rule, to two places",
      block()["staff_to_keep_it_open"] == {"scholars": 1.23, "artisans": 2.68}, block()["staff_to_keep_it_open"])
check("the supervision figure is not clamped to any build crew: a large one is shown whole",
      block(supervision=(0.0, 40.0))["staff_to_keep_it_open"]["artisans"] == 40.0)
check("a pure-knowledge node carries no supervision figure", block(is_venture=False)["staff_to_keep_it_open"] is None)
check("...and no charge to open", block(is_venture=False)["charge_to_open"] is None)
check("a concern's charge to open is the opening fee", block()["charge_to_open"] == 250.0)
check("a concern with no specialist foreman names none", block()["specialist_foreman_to_keep_it_open"] is None)
foreman = block(foreman=("glassblower", 0.456))["specialist_foreman_to_keep_it_open"]
check("a specialist foreman is named with the share of his year and how many are free",
      foreman == {"trade": "glassblower", "fte": 0.46, "free_now": 0.5}, foreman)
check("supervision the household can cover raises no warning", block()["more_supervision_than_you_have_free_right_now"] is None)
check("supervision beyond the free scholars raises the warning",
      bool(block(supervision=(3.0, 1.0), free=(2.0, 5.0))["more_supervision_than_you_have_free_right_now"]))
check("supervision beyond the free artisans raises the warning",
      bool(block(supervision=(1.0, 3.0), free=(5.0, 2.0))["more_supervision_than_you_have_free_right_now"]))
check("supervision exactly equal to what is free raises no warning",
      block(supervision=(2.0, 2.0), free=(2.0, 2.0))["more_supervision_than_you_have_free_right_now"] is None)
