"""The home state's tariff on the goods landed from abroad, as the share of each good's landed price the economy taxes.

Part of the port. A state's tariff toward a country is a share of the goods' value at their source (sim/markets/trade_duty.py), so a
good landed at that value plus the tariff has the share `tariff / (1 + tariff)` of its landed price as duty. The economy
(sim/economy/tariffs.py) takes that share of what buyers pay a foreign edge for the good, for the home state.

APPROXIMATION (no complaint covers it yet): the share is taken of the landed price as if that price were source value plus
tariff only. The landed price also carries carriage from the source, and the tariff is on the value at the source, so with
carriage the true duty share is smaller than `tariff / (1 + tariff)`; the economy's duty is overstated by that carriage.

Goods the economy's own merchants carry in from another country of the economy are charged the tariff toward that country on their
value at the source (`carried_tariffs`, by source country); no embargo stops those flows."""
from .port_cargo import LANDING


def import_duty_shares(legs, tariff_toward):
    """{good: share of its landed price that is the home state's tariff} for the goods the cargo `legs` land this year. A good
    landed from several countries has the mean of their shares weighted by the tonnes each landed; `tariff_toward(country)` is the
    tariff share the home state holds toward goods from that country. A good with no tariff on it is left out."""
    tonnes, duty = {}, {}
    for leg in sorted(legs, key=lambda each: each["id"]):
        if leg["kind"] != LANDING or leg["tonnes"] <= 0.0:
            continue
        tariff = tariff_toward(leg["partner"])
        good = leg["material"]
        tonnes[good] = tonnes.get(good, 0.0) + leg["tonnes"]
        duty[good] = duty.get(good, 0.0) + leg["tonnes"] * tariff / (1.0 + tariff)   # approximation: ignores carriage in the landed price (module docstring)
    return {good: duty[good] / tonnes[good] for good in sorted(tonnes) if duty[good] > 0.0}


def carried_tariffs(countries, home, tariff_toward):
    """{source country: the tariff share of the value at the source} the home state holds toward goods the economy's own merchants carry
    in from each other country of the economy; a country with no tariff on it is left out."""
    return {country: tariff_toward(country) for country in sorted(countries) if country != home and tariff_toward(country) > 0.0}
