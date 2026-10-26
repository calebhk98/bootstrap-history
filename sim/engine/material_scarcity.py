"""The scarcity factor of a bought material, as a plain function: how hard demand leans on the supply."""


def scarcity_factor(needs_and_own_supplies, market_tonnes, share_cap, pressure_scale):
    """The dearest pressure among a material's demands. Each demand is (need, own supply) in tonnes; its share
    of the supply (own plus market) is capped, and the price rises by the pressure scale times the share squared.
    One when nothing is needed."""
    worst = 1.0
    for need, own_supply in needs_and_own_supplies:
        if need <= 0:
            continue
        supply = max(1e-9, own_supply + market_tonnes)
        share = min(share_cap, need / supply)
        worst = max(worst, 1.0 + pressure_scale * share * share)
    return worst
