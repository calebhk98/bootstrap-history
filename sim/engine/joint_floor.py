"""A lower bound under every output of a joint batch: minus what it costs to dispose of it."""


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
