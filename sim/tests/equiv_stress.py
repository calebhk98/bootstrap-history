"""The stress tier of the equivalence tool: a game with hazards of every kind written into its civilisation and the
rare events made likely, so the paths the ordinary tiers almost never reach (a sack, a plague's staff loss, a
debasement, an unmet condition, fire, banditry, a patron's death, a second seat) run every few years.

Works on the base checkout as on the current one: the hazards are data, and the event chances are set on whichever
holder the checkout keeps them on."""
import contextlib
import importlib

STRESS_HAZARDS = [
    {"name": "Stress plague", "years": [101, 108], "staff_loss": 0.3, "note": "stress tier"},
    {"name": "Stress war", "years": [102, 106], "output_factor": 0.6, "sack_chance": 0.5,
     "values": {"w_novelty": -0.1, "w_commerce": 0.05}},
    {"name": "Stress debasement", "years": [103, 104], "real_erosion": 0.15},
    {"name": "Stress fleet", "years": [105, 106], "output_factor": 0.8,
     "condition": {"field": "output_factor", "requires_all": ["no_such_tech"], "outcome": "alter", "alter_scale": 0.5,
                   "unmet_message": "no", "met_message": "yes"}},
    {"name": "Stress causes", "years": [107, 109], "staff_loss": 0.2,
     "causes": [{"quantity": "population", "op": ">=", "value": 1e13, "why": "too few people"}]},
    {"name": "Stress siege", "years": [109, 111], "sack_chance": 0.9},
]
LIKELY_EVENTS = {"FIRE_ANNUAL_CHANCE": 0.5, "BANDITRY_ANNUAL_CHANCE": 0.5, "PATRON_DEATH_ANNUAL_CHANCE": 0.5,
                 "PATRON_DEATH_COOLDOWN_YEARS": 2}
# where a checkout keeps the event chances: the hazards module now, the hazards mixin on the base
CHANCE_HOLDERS = (("sim.hazards.constants", None), ("sim.engine.society_hazards", "HazardsMixin"))
PATRON = "patron_local"
SECOND_SEAT = ("second", {"capital": 800.0, "starting_techs": [], "scholars": 2, "artisans": 2})


def _chance_holder():
    for module_name, attribute in CHANCE_HOLDERS:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        return getattr(module, attribute) if attribute else module
    raise SystemExit("the stress tier found no holder of the event chances in this checkout")


@contextlib.contextmanager
def stressed_civilisations(fingerprint):
    """While building: every civilisation the game loads carries the stress hazards."""
    original = fingerprint.S.load_civ

    def load_civ(name):
        civ = original(name)
        return dict(civ, hazards=list(civ.get("hazards", [])) + STRESS_HAZARDS)
    fingerprint.S.load_civ = load_civ
    try:
        yield
    finally:
        fingerprint.S.load_civ = original


def build(scenario):
    """The scenario's game with the stress hazards, likely events, a running patron and, if asked, a second seat."""
    from sim.tests import fingerprint
    holder = _chance_holder()
    for name, value in LIKELY_EVENTS.items():
        setattr(holder, name, value)
    with stressed_civilisations(fingerprint):
        sim = fingerprint.build(scenario)
    if PATRON in sim.nodes:
        sim.state.projects.done.add(PATRON)
        sim.state.projects.operating.add(PATRON)
    if scenario.get("seats", 1) > 1:
        sim.join_seat(*SECOND_SEAT)
    return sim
