"""Each civilisation file carries its own names and notes for the state's requisition, office, military demand and confiscation
(Complaint 658's notice mechanic reads them); data only, no game."""
from sim.engine.data import load_civ

from .harness import check

QUICK_TOPIC = True

_ALL_CIVS = ("rome_100ad", "han_china_100ad", "england_1300", "norse_900ad", "mexica_1500")

for _cv in _ALL_CIVS:
    _sp = load_civ(_cv).get("state_pressure") or {}
    check("%s: its civilization file carries its OWN requisition/office/"
          "military/confiscation names and notes, not a shared generic one"
          % _cv,
          all(_sp.get(field_name) for field_name in (
              "requisition_name", "requisition_note",
              "office_name", "office_note",
              "military_name", "military_note",
              "confiscation_name", "confiscation_note")),
          _sp)


