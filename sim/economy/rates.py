"""The interest rate a plan charges capital at."""


def own_rate(view, currency) -> float:
    """The economy's own currency's rate: the memory holds one from the opening on. A missing one is a defect, so
    this refuses rather than charge nothing for waiting."""
    rate = view.interest_rate(currency)
    if rate is None:
        raise ValueError(f"no interest rate remembered for the economy's own currency {currency!r}")
    return rate

