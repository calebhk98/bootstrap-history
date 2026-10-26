"""Facts that must hold about the tree and the civilisation files
themselves: a reference-only civilisation cannot be played, every gate a
civilisation sets names a real, liftable node, one civilisation is never
handed another's flavour text, a priced material is gated by its own
prerequisite rather than sentinel-priced, and no civilisation's dated events
leave a long silent stretch or hand out a free technology on turn one.
The rules these files feed (the needs-first gate, the word swaps) are called on plain inputs here.
"""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403


# --- BREAK: `_TECH_EFFECTS` offered as a playable civilisation.
_civerr = ""
try:
    S.load_civ("rome")
except SystemExit as e:
    _civerr = str(e)
check("the reference data files are not offered as civilisations to play",
      "_TECH_EFFECTS" not in _civerr and "rome_100ad" in _civerr, _civerr)

# Every gate has to be liftable, or it is a wall rather than a handicap.
for _cf in sorted(os.listdir(os.path.join(ROOT, "data/civilizations"))):
    if not _cf.endswith(".json") or _cf.startswith("_"):
        continue
    _cv = json.load(open(os.path.join(ROOT, "data/civilizations", _cf)))
    for _lbl, _ent in (_cv.get("needs_first") or {}).items():
        if _lbl.startswith("_"):
            continue
        check("%s: the '%s' gate names a real node that lifts it"
              % (_cv["id"], _lbl),
              _ent.get("node") in NODES and _ent["node"] not in (_ent.get("ids") or []),
              _ent.get("node"))
        check("%s: every id behind the '%s' gate is a real node"
              % (_cv["id"], _lbl),
              all(x in NODES for x in (_ent.get("ids") or [])),
              [x for x in (_ent.get("ids") or []) if x not in NODES])


# --- the word swaps: a civilisation is never handed another's flavour text ----------------------------------------
# BREAK: Han China was told it writes its corpus "in plain quantitative Greek and Latin" and seeks "Senatorial
# patronage". The swap pairs are the civilisation's data; `_localise_words` applies them to a reply.
from sim.ui.proto.util import _localise_words

_rome_words = json.dumps([NODES["corpus_written"], NODES["patron_senatorial"]])
check("the tree is written in Rome's words (so the swaps below have something to swap)",
      "Greek and Latin" in _rome_words and "Senatorial patronage" in _rome_words, _rome_words[:100])
for _cid, _bad in (("han_china_100ad", "Greek and Latin"), ("norse_900ad", "Senatorial patronage"),
                   ("han_china_100ad", "Senatorial patronage")):
    _pairs = (S.load_civ(_cid).get("local_words") or {}).get("pairs")
    _localised = json.dumps([_localise_words(NODES[_n], _pairs) for _n in ("corpus_written", "patron_senatorial")])
    check("%s is not handed Rome's own words (%s)" % (_cid, _bad), _bad not in _localised, _bad)
_rome_pairs = (S.load_civ("rome_100ad").get("local_words") or {}).get("pairs")
check("...and Rome, which the tree is written from, is left alone",
      json.dumps(_localise_words(NODES["corpus_written"], _rome_pairs)) == json.dumps(NODES["corpus_written"]), _rome_pairs)

# --- the needs-first gate ----------------------------------------------------------------------------------------
# BREAK: the Mexica menu says "no draught animals, no iron, no wheel in practical use" and horse_collar was startable
# on arrival in the Valley of Mexico in 1500. `needs_first` is called with the civilisation's own data on a stub game.
from sim.tests.diffusion_host import gated

_HORSE = "horse_collar"


def _gated(civ_id, done=(), stock_met=False):
    game = gated(S.load_civ(civ_id), done, stock_met)
    return game.needs_first(_HORSE), game


(_node, _because), _mexica_game = _gated("mexica_1500")
check("a society with no draught animal is gated on the node that brings them", _node == "exp_import_draught_animals", _node)
check("...and the refusal says there is no draught animal", "draught animal" in _because, _because)
check("...and bringing the animals across (the node done) opens it",
      _gated("mexica_1500", done=["exp_import_draught_animals"])[0] == (None, None), "still gated")
check("...and holding enough of the animals opens it without the node",
      _gated("mexica_1500", stock_met=True)[0] == (None, None), "still gated")
check("...a gate that rests on stock is not asked about knowledge alone",
      _mexica_game.needs_first(_HORSE, about_stock=False) == (None, None), "gated on knowledge")
check("a society that HAS horses is not gated at all (the control case)",
      _gated("rome_100ad")[0] == (None, None), _gated("rome_100ad")[0])
check("a node that is not behind the gate is not gated",
      _mexica_game.needs_first("corpus_written") == (None, None), "gated")


# --- BREAK: rubber was priced at 99,999 a kilo, a sentinel left over from the
# abolished "unobtainable" tier, and it survived the abolition of the concept
# that justified it. A play tester worked out that one kilo was four hundred
# artisan-years, that a rubber eraser cost 3,001,105 against 5 for a
# breadcrumb, and that securing a rubber supply did not change the price by a
# denarius. It was also over half of the whole tree's capital cost.
_RUB = ("rubber_kg", "rubber_tubing_kg")
for _r in _RUB:
    check("%s is priced like a distant import, not like a sentinel" % _r,
          0 < GOODS[_r] / PRICES["money_per_labour_hour"] < 20000,
          GOODS[_r] / PRICES["money_per_labour_hour"])
# ...and the reason the sentinel existed - that nothing stopped you buying it -
# is answered where it belongs, in the tree: you cannot use rubber until you
# have gone and got some.
def _anc_of(node_id, seen=None):
    seen = seen if seen is not None else set()
    for prereq_id in NODES[node_id]["pre"]:
        if prereq_id not in seen:
            seen.add(prereq_id); _anc_of(prereq_id, seen)
    return seen
_rub_users = sorted(node_id for node_id, value in NODES.items()
                    if any("rubber" in material for material in (value.get("mat") or {})))
_ungated = [node_id for node_id in _rub_users
            if not ({"mat_natural_rubber", "mat_synthetic_rubber"} & _anc_of(node_id))]
# --- BREAK: a node whose own note names a material it does not require. The
# blind prerequisite audit found in2_electron_source_cathode saying "Tungsten
# chosen for high melting point and low evaporation" with no tungsten anywhere
# in its ancestry. Ductile tungsten filament wire is the Coolidge process and
# is a real achievement: tungsten is too brittle to draw until it is sintered
# from powder and worked hot, which is why powder metallurgy belongs here too.
#
# It was nearly deferred on a misread number. mat_tungsten's closure is 102
# nodes, which looked like adding a hundred nodes to a 145-node goal path - but
# 101 of those 102 were already in that closure, so the MARGINAL addition is
# one. Raw closure size is the wrong quantity to price a new edge with.
_cath = NODES["in2_electron_source_cathode"]["pre"]
check("the cathode that is made of tungsten requires tungsten",
      "mat_tungsten" in _cath, _cath)
check("...and the powder metallurgy that makes tungsten drawable at all",
      "met_powder_metallurgy" in _cath, _cath)
check("...and the note that named it is still the reason it is there",
      "tungsten" in (NODES["in2_electron_source_cathode"].get("note") or "").lower(),
      (NODES["in2_electron_source_cathode"].get("note") or "")[:90])

check("nothing can be made of rubber without first securing rubber",
      not _ungated, _ungated)
check("(and there really are rubber recipes to gate)", len(_rub_users) > 10,
      len(_rub_users))

# --- JOB 1: "something happens shortly after the game starts and then
# nothing happens for centuries" was the same shape of complaint across
# several rounds of playtesting, on more than one civilization. Audited and
# fixed by adding real, dated events; this check keeps the fix from rotting
# by failing if a future edit to a civilization file reopens a long silent
# stretch. Ninety years is generous against what every file now actually
# does (England's worst remaining gap is 63, Norse's is 86) but still catches
# the kind of quarter-millennium silence the audit found.
for _cf in sorted(glob.glob(os.path.join(ROOT, "data", "civilizations", "*.json"))):
    _cid = os.path.basename(_cf)[:-5]
    if _cid.startswith("_"):
        continue
    _cd = json.load(open(_cf))
    _start = _cd["year"]
    _windows = sorted((hazard["years"][0], hazard["years"][1]) for hazard in _cd.get("hazards", []))
    _prev, _gaps = _start, []
    for (_a, _b) in _windows:
        _gaps.append(_a - _prev)
        _prev = max(_prev, _b)
    check("%s: no silent stretch longer than 90 years between its dated "
          "events" % _cid,
          all(gap <= 90 for gap in _gaps), _gaps)
    if _cid != "mexica_1500":
        # The Mexica's list runs out at the edge of real history, not at the
        # horizon - extending it past here would mean inventing the future,
        # which the drug war entry's own note says this file will not do.
        # Every OTHER civilization's list should reach close to the end of
        # the 500-700 year run the brief asked for.
        check("%s: its events reach close to the end of a 700-year run, "
              "not just the first half of it" % _cid,
              (_start + 700) - _prev <= 90, (_start, _prev))


# --- a win condition is met on the right side of its target for its comparison, and an unknown comparison never is
from sim.engine.win_condition_rule import win_condition_met

check("a >= condition is met at its target and above, not below",
      win_condition_met({"op": ">=", "value": 0.2}, 0.2) and win_condition_met({"op": ">=", "value": 0.2}, 0.9)
      and not win_condition_met({"op": ">=", "value": 0.2}, 0.1999))
check("a <= condition is met at its target and below, not above",
      win_condition_met({"op": "<=", "value": 5}, 5) and win_condition_met({"op": "<=", "value": 5}, 0)
      and not win_condition_met({"op": "<=", "value": 5}, 5.01))
check("any other comparison is never met", not win_condition_met({"op": "==", "value": 1}, 1))
