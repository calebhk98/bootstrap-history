"""Complaints/532: the engine's opening herds are the head the agent economy's herd producers keep (one figure). The
arithmetic is called on producers and pasture the test states; the credit to the ledger is in
test_opening_herds_grant."""
import json
import os

from .harness import *  # noqa: F401,F403

from sim.engine.data import ROOT
from sim.engine.opening_herd_rules import herd_units_kept, opening_herds

QUICK_TOPIC = True

HERD_STOCKS = ("sheep_kg", "goat_kg", "cattle_kg")
PRODUCTION = {"keep_sheep": {"herd_stock": {"sheep_kg": 2.0}}, "keep_sheep_hill": {"herd_stock": {"sheep_kg": 3.0}},
              "keep_cattle": {"herd_stock": {"cattle_kg": 1.0}}, "weave": {"outputs": {"cloth": 1.0}}}
WEIGHT_KG = {"sheep_kg": 10.0, "cattle_kg": 100.0}.get
FULL = lambda material: 1.0

kept = herd_units_kept([("keep_sheep", 10.0), ("keep_sheep_hill", 4.0), ("keep_cattle", 5.0), ("weave", 99.0), ("unknown", 7.0)],
                       PRODUCTION)
check("the head kept is each producer's runs times the stock one run holds, summed by species",
      kept == {"sheep_kg": 32.0, "cattle_kg": 5.0}, kept)
check("a producer whose recipe keeps no herd adds none", "cloth" not in kept and len(kept) == 2, kept)

roomy = opening_herds(kept, 1e12, WEIGHT_KG, FULL)
check("where the pasture is ample the opening herds are the producers' head", roomy == kept, roomy)

weight = 32.0 * 10.0 + 5.0 * 100.0
tight = opening_herds(kept, weight / 2.0, WEIGHT_KG, FULL)
check("a pasture that carries half the weight holds every herd down by half together",
      all(abs(tight[material] - kept[material] / 2.0) < 1e-9 for material in kept), tight)
check("the herds held stand within the pasture the held tiles carry",
      sum(units * WEIGHT_KG(material) for material, units in tight.items()) <= weight / 2.0 + 1e-9, tight)
diseased = opening_herds(kept, 1e12, WEIGHT_KG, {"sheep_kg": 0.25, "cattle_kg": 1.0}.get)
check("disease at the place leaves only the share of a herd that can stand there",
      diseased == {"cattle_kg": 5.0, "sheep_kg": 8.0}, diseased)
check("no herd producers hold no herds", opening_herds({}, 100.0, WEIGHT_KG, FULL) == {})

for name in ("rome_100ad", "han_china_100ad", "england_1300", "norse_900ad"):
    with open(os.path.join(ROOT, "data", "civilizations", name + ".json"), encoding="utf-8") as handle:
        opening = json.load(handle).get("opening_stock") or {}
    check("%s states no herd in opening_stock" % name, not set(opening) & set(HERD_STOCKS), opening)
