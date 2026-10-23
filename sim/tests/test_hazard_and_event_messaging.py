"""What a hazard tells the player and how a patron's death is rolled: no internal jargon in hazard notes, and a patron
cannot die twice inside the cooling-off period (the debasement telling is in test_shock_real_erosion)."""
from .harness import *  # noqa: F401,F403

from sim.engine.patron_death import patron_dies
from sim.engine.society_hazards import HazardsMixin

QUICK_TOPIC = True

# --- player-facing hazard notes quoted the values vector by its internal names ("raises w_magic_fear"), which a player
# cannot read. Nothing shown to a player may name a values-vector key.
_JARGON = ("w_magic_fear", "w_eminence_danger", "w_religious_rigidity",
           "w_labour_saving", "w_commerce", "w_information", "w_novelty",
           "w_military", "adaptation_rate", "patronage_weight", "bribability")
_dirty = []
for _f in sorted(os.listdir(os.path.join(ROOT, "data/civilizations"))):
    if not _f.endswith(".json") or _f.startswith("_"):
        continue
    _civ = json.load(open(os.path.join(ROOT, "data/civilizations", _f)))
    for _h in _civ.get("hazards", []):
        _txt = " ".join(str(_h.get(x, "")) for x in ("name", "note"))
        _dirty += [(_f, _h.get("name"), _jargon_term) for _jargon_term in _JARGON if _jargon_term in _txt]
check("no hazard a player reads names an internal values-vector key", not _dirty, _dirty[:3])

# --- the cooling-off guard read one name and the body set another, so the roll fired every year for ever.
CHANCE, COOLDOWN = HazardsMixin.PATRON_DEATH_ANNUAL_CHANCE, HazardsMixin.PATRON_DEATH_COOLDOWN_YEARS
MORTAL = lambda: True
check("a roll under the chance kills a mortal patron who has not died before",
      patron_dies(0.0, CHANCE, MORTAL, None, 100, COOLDOWN))
check("a roll over the chance kills nobody", not patron_dies(1.0, CHANCE, MORTAL, None, 100, COOLDOWN))
check("a patron who is not mortal is not asked about when the roll is over the chance",
      not patron_dies(1.0, CHANCE, lambda: 1 / 0, None, 100, COOLDOWN))
check("a patron who is not mortal does not die", not patron_dies(0.0, CHANCE, lambda: False, None, 100, COOLDOWN))
check("a patron cannot die again inside the cooling-off period",
      not patron_dies(0.0, CHANCE, MORTAL, 100, 100 + COOLDOWN, COOLDOWN))
check("...but can the year after it", patron_dies(0.0, CHANCE, MORTAL, 100, 100 + COOLDOWN + 1, COOLDOWN))

rolls = random.Random(4)
deaths, last = [], None
for year in range(100, 400):
    if patron_dies(rolls.random(), CHANCE, MORTAL, last, year, COOLDOWN):
        deaths.append(year)
        last = year
check("over three centuries of rolls the deaths are at least the cooling-off period apart",
      all(later - earlier > COOLDOWN for earlier, later in zip(deaths, deaths[1:])), deaths)
check("...so there are at most one per cooling-off period", len(deaths) <= 300 // COOLDOWN + 1, deaths)
