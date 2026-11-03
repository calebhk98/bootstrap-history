"""The home state's tariff on the goods landed from abroad, as the share of each good's landed price the economy taxes.

Part of the port. A state's tariff toward a country is a share of the goods' value at their source (sim/markets/trade_duty.py), so a
good landed at that value plus the tariff has the share `tariff / (1 + tariff)` of its landed price as duty. The economy
(sim/economy/tariffs.py) takes that share of what buyers pay a foreign edge for the good, for the home state."""
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
        duty[good] = duty.get(good, 0.0) + leg["tonnes"] * tariff / (1.0 + tariff)
    return {good: duty[good] / tonnes[good] for good in sorted(tonnes) if duty[good] > 0.0}
