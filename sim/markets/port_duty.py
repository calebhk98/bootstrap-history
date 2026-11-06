"""The home state's tariff on the goods the economy's own merchants carry in from another country of the economy.

Part of the port. A state's tariff toward a country is a share of the goods' value at their source (sim/markets/trade_duty.py); those goods are
charged it on their value at the source (`carried_tariffs`, by source country), and no embargo stops those flows. A cargo a trader lands
from abroad pays its tariff in the cargo leg (foreign_trade/cargo.py), not here."""


def carried_tariffs(countries, home, tariff_toward):
    """{source country: the tariff share of the value at the source} the home state holds toward goods the economy's own merchants carry
    in from each other country of the economy; a country with no tariff on it is left out."""
    return {country: tariff_toward(country) for country in sorted(countries) if country != home and tariff_toward(country) > 0.0}
