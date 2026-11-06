"""The interest rate a plan charges capital at."""


def own_rate(view, currency) -> float:
    """The economy's own currency's rate. A missing one is impossible by construction: the opening memory is seeded with
    one (`opening._opening_memory`) and nothing removes it afterwards (`MarketMemory.set_rate` only replaces it). A
    missing one would be a defect, so this raises rather than charge nothing for waiting."""
    rate = view.interest_rate(currency)
    if rate is None:
        raise ValueError(f"no interest rate remembered for the economy's own currency {currency!r}")
    return rate

