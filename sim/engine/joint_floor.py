"""A lower bound under every output of a joint batch: minus what it costs to dispose of it."""
from sim.constants import declare

DEMAND_GLUT_SHARE_OF_DISPOSAL_COST = declare(
    "DEMAND_GLUT_SHARE_OF_DISPOSAL_COST", 0.01,
    kind="temporary_heuristic",
    unit="fraction of the disposal cost per unit",
    source=None,
    confidence="D",
    why="An output whose market clears at no more than this share of what disposing of it costs is in "
        "glut: the clearing search bottoms out at its lowest price instead of finding a root, so the "
        "price is the disposal cost, not the near-zero anchor. Should come from the clearing search "
        "reporting that supply exceeds demand at every price.")


def is_glutted(anchor_price, disposal_cost):
    return disposal_cost > 0.0 and anchor_price <= DEMAND_GLUT_SHARE_OF_DISPOSAL_COST * disposal_cost


def bound_to_disposal_cost(prices, outputs, disposal_cost_by_material):
    """`prices` with every output at or above minus its disposal cost, the batch still recovering its cost.

    The lift is paid for by the outputs already above their bound, in proportion to their revenue."""
    bound = {name: -disposal_cost_by_material.get(name, 0.0) for name in outputs}
    low = {name for name in outputs if prices[name] < bound[name]}
    if not low:
        return prices
    lifted = {name: bound[name] if name in low else prices[name] for name in outputs}
    excess = sum((lifted[name] - prices[name]) * outputs[name] for name in low)
    payers = {name: prices[name] * outputs[name] for name in outputs
              if name not in low and prices[name] > 0.0}
    payer_revenue = sum(payers.values())
    if payer_revenue <= excess:
        return prices
    for name, revenue in payers.items():
        lifted[name] = prices[name] * (1.0 - excess / payer_revenue)
    return lifted
