"""How much coin wears in a hidden spin-up year (the rule sets' `spin_up_coin_wear`). The spin-up is closed to trade,
and the metal mined at home does not keep up with the declared wear, so the stock of coin falls in every hidden year,
prices and wages follow it down, and the economy has no rest to find. What kept a country's coin up in history was
metal that came in through trade. Until the opening carries that trade (owner question 13 of
Complaints/reports/473-owner-questions.md), a rule set may let coin wear in a hidden year only as far as the mint
struck coin that year: the stock then rests where the mint cannot keep up, and still grows where it strikes more than
wears. The mint sizes what it strikes on the declared wear (`mint.yearly_monetisation`), so its own demand for metal
is as before. A year of play wears coin at the declared share."""


def as_declared(declared_share: float, _settling: bool, _coin_stock: float, _struck: float) -> float:
    """Coin wears at its declared share a year, in a hidden year as in any other."""
    return declared_share


def no_more_than_struck_while_settling(declared_share: float, settling: bool, coin_stock: float, struck: float) -> float:
    """The share of each holding of coin that wears this year: the declared share, and in a hidden year no more than
    the coin the mint struck this year (net of what it melted) over the stock, nothing where it struck none."""
    if not settling or not coin_stock > 0.0:
        return declared_share
    return min(declared_share, max(0.0, struck) / coin_stock)
