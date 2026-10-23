"""Complaint 492: a state runs the plants its civilisation declares. The cast carries each civilisation's declared monopolies and
enterprises to its government (`cast_from_civilisations`), every declared enterprise is a node of the tree, and the state opens a plant of
each declared enterprise (`entries_for`), counting the good it makes as its monopoly's. The civilisation files are read as data; no game is built."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check, NODES

from sim.agents import state_enterprises
from sim.agents.cast import cast_from_civilisations
from sim.engine.data import load_civ

CIVILISATIONS = ("rome_100ad", "han_china_100ad", "norse_900ad", "england_1300", "mexica_1500")

# ---- the cast carries the declarations
for civ_id in CIVILISATIONS:
    civ = load_civ(civ_id)
    _home, entries, _profiles = cast_from_civilisations(civ, [])
    government = next(entry for entry in entries if entry.kind == "government")
    check("%s: its government is cast with the monopolies and enterprises the civilisation declares" % civ_id,
          government.params["state_monopolies"] == list(civ.get("state_monopolies") or ())
          and government.params["state_enterprises"] == list(civ.get("state_enterprises") or ()), government.params)
    missing = [node_id for node_id in civ.get("state_enterprises") or () if node_id not in NODES]
    check("%s: every state enterprise it declares is a node of the tree" % civ_id, missing == [], missing)
han = load_civ("han_china_100ad")
check("Han declares a state enterprise", bool(han.get("state_enterprises")), han.get("state_enterprises"))


# ---- the state opens a plant of each declared enterprise
class World:
    def __init__(self, makes):
        self.makes = makes

    def materials_made_by(self, entry_key):
        return self.makes.get(entry_key, [])

    def concerns_making(self, material):
        return {key for key, made in self.makes.items() if material in made}

    def concern_gross(self, entry_key):
        return 1.0


def state(enterprises=(), monopolies=(), operating=()):
    return SimpleNamespace(record=SimpleNamespace(state_enterprises=set(enterprises), state_monopolies=set(monopolies)),
                           business=SimpleNamespace(entry_keys=lambda: list(operating)), knows=lambda entry_key, world: True)


world = World({"blast_furnace": ["cast_iron_kg"], "salt_works": ["salt_kg"]})
check("a declared enterprise is an entry the state runs", state_enterprises.entries_for(state(enterprises=["blast_furnace"]), world) == ["blast_furnace"], None)
check("a monopoly good the declared enterprise makes needs no second plant",
      state_enterprises.entries_for(state(enterprises=["blast_furnace"], monopolies=["cast_iron_kg"]), world) == ["blast_furnace"], None)
check("a monopoly good no declared enterprise makes is run by the first entry that makes it",
      state_enterprises.entries_for(state(enterprises=["blast_furnace"], monopolies=["salt_kg"]), world) == ["blast_furnace", "salt_works"], None)
check("a monopoly good nobody makes opens nothing", state_enterprises.entries_for(state(monopolies=["gold_kg"]), world) == [], None)
