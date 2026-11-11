"""The yield the home state's bonds offer a lender, handed to the economy as a rate. Part of the port."""


def bond_yield_above_coupon(sim):
    """The yield the home state's bonds sell at when it exceeds their coupon (the going rate they are issued at), else None.
    At the coupon the yield is the going rate itself, which a lender already has as its own market; above it the state's
    default record has made it pay more, which is a return a lender can weigh. None without a government or bonds."""
    government = sim.scenario.actors.countries.government_of(None)
    if government is None:
        return None
    bonds = government.purses.bonds
    if not bonds.issues(government.account_id):
        return None
    coupon, yield_rate = bonds.terms[government.account_id]
    return yield_rate if yield_rate > coupon else None
