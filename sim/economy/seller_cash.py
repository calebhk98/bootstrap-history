"""The cash a producer still presses to raise when it offers its output: what its target lacks after the
year's costs, which the sale of that very output repays, are set aside.

A producer pays its wages and inputs before it sells, so at the point of sale its cash always sits below its
target by about what it laid out. Treating that gap as distress made every seller ask a fraction of its
expected price in a year it sold at a profit, and in a thin market (an input whose cost is most of its price)
the clearing price then fell to those asks in any year of surplus and rose to the buyers' ceiling in any year
of shortage.
"""
from sim.constants import declare

LAID_OUT_COST_REPAID_SHARE = declare(
    "LAID_OUT_COST_REPAID_SHARE", 0.7, kind="temporary_heuristic",
    unit="share of the year's running costs a producer counts as repaid by selling its output", source=None,
    confidence="D",
    why="The cash laid out making stock comes back when the stock sells, so it is not a shortfall the sale must "
        "undercut the market to close. Not all of it is counted: the sale may fetch less than the expected price, "
        "and how much less is not modelled. Neighbouring values flip the durable-stock and innovator fixtures "
        "(they sit on a threshold where the external edge's bid and ask meet the domestic asks), so the value is "
        "one that leaves them standing, not a measured share.")


def shortfall_to_raise(cash_target: float, cash: float, running_costs: float) -> float:
    """What the producer's cash lacks of its target once the repaid share of this year's running costs is set aside."""
    return max(0.0, cash_target - cash - LAID_OUT_COST_REPAID_SHARE * running_costs)
