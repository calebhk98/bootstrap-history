"""The cash a producer still presses to raise when it offers its output: what its target lacks after the
year's costs, which the sale of that very output repays, are set aside.

A producer pays its wages and inputs before it sells, so at the point of sale its cash always sits below its
target by about what it laid out. Treating that gap as distress made every seller ask a fraction of its
expected price in a year it sold at a profit, and in a thin market (an input whose cost is most of its price)
the clearing price then fell to those asks in any year of surplus and rose to the buyers' ceiling in any year
of shortage.
"""


def shortfall_to_raise(cash_target: float, cash: float, running_costs: float) -> float:
    """What the producer's cash lacks of its target once this year's running costs are set aside."""
    return max(0.0, cash_target - cash - running_costs)
