"""A floor under every output of a joint batch, so a by-product nobody wants is not priced to zero."""
from sim.constants import declare

JOINT_BYPRODUCT_FLOOR_SHARE = declare(
    "JOINT_BYPRODUCT_FLOOR_SHARE", 0.01,
    kind="temporary_heuristic",
    unit="fraction of the batch's standalone cost per kg",
    source=None,
    confidence="D",
    why="A by-product in glut is cleared by demand to nothing, and the damped solve then decays its "
        "price to a denormal that downstream costs cannot use. The floor stands in for the handling "
        "and disposal cost a real by-product carries; it should come from a handling labour term "
        "in the recipe data.")


def lift_to_floor(prices, outputs, kilograms_per_unit, total_cost):
    """`prices` with every output at or above the floor, the batch still recovering `total_cost`.

    The lift is paid for by the outputs already above their floor, in proportion to their revenue."""
    total_kilograms = sum(kilograms_per_unit[name] * outputs[name] for name in outputs)
    if total_kilograms <= 0 or total_cost <= 0:
        return prices
    standalone_per_kg = total_cost / total_kilograms
    floor = {name: JOINT_BYPRODUCT_FLOOR_SHARE * standalone_per_kg * kilograms_per_unit[name]
             for name in outputs}
    low = {name for name in outputs if prices[name] < floor[name]}
    if not low:
        return prices
    lifted = {name: floor[name] if name in low else prices[name] for name in outputs}
    excess = sum((lifted[name] - prices[name]) * outputs[name] for name in low)
    payers = {name: prices[name] * outputs[name] for name in outputs if name not in low}
    payer_revenue = sum(payers.values())
    if payer_revenue <= excess:
        return prices
    for name, revenue in payers.items():
        lifted[name] = prices[name] * (1.0 - excess / payer_revenue)
    return lifted
