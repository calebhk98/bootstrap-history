"""need_basket.with_quality_reach on the shipped needs data: with the light goods at one price, light spending moves from tallow to the
cleaner goods as the buyer's quality reach rises. The rule on hand data is test_need_quality."""
import json
import os

from sim.labour.api import production_data
from sim.world import need_basket

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

with open(os.path.join(ROOT, "data", "world", "needs.json"), encoding="utf-8") as handle:
    basket = need_basket.make_basket(json.load(handle), production_data())
light_goods = [good for need in basket.needs if need.need_id == "light" for good, _effect in need.goods]
base = need_basket.need_prices(basket, {good: 1.0 for good in light_goods}.get)
tallow = {good for good in light_goods if "tallow" in good}


def tallow_share(reach):
    (light,) = [need for need in need_basket.with_quality_reach(base, basket, reach) if need.spec.need_id == "light"]
    return sum(share for good, _price, _effect, share in light.goods if good in tallow)


check("the shipped light goods include tallow goods", bool(tallow), light_goods)
check("at equal prices a buyer who pays for quality spends a smaller share of light money on tallow than one who does not",
      tallow_share(1.0) < tallow_share(0.0), (tallow_share(0.0), tallow_share(1.0)))
