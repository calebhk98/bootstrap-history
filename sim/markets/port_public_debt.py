"""What the home state's bonds pay a lender over the going rate, handed to the economy as a rate. Part of the port."""


def bond_premium_over_coupon(sim):
    """How far the yield the home state's bonds sell at exceeds their coupon (the going rate they are issued at); zero
    where it does not. The going rate is the lender's own market, so only the premium is a return it can add; the
    state's default record is what makes it pay one. None without a government or bonds."""
    government = sim.scenario.actors.countries.government_of(None)
    if government is None:
        return None
    bonds = government.purses.bonds
    if not bonds.issues(government.account_id):
        return None
    coupon, yield_rate = bonds.terms[government.account_id]
    return max(0.0, yield_rate - coupon)
