"""Facts that must hold about the tree and the civilisation files
themselves: a reference-only civilisation cannot be played, every gate a
civilisation sets names a real, liftable node, one civilisation is never
handed another's flavour text, a priced material is gated by its own
prerequisite rather than sentinel-priced, and no civilisation's dated events
leave a long silent stretch or hand out a free technology on turn one.

Regrouped from test_round8_fixes.py, test_round9.py and test_round10.py -
see CLAUDE.md's test-file reorganisation note. Checks moved verbatim; each
one's own comment explains the break it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: `_TECH_EFFECTS` offered as a playable civilisation.
_civerr = ""
try:
    S.load_civ("rome")
except SystemExit as e:
    _civerr = str(e)
check("the reference data files are not offered as civilisations to play",
      "_TECH_EFFECTS" not in _civerr and "rome_100ad" in _civerr, _civerr)

# --- BREAK: the Mexica menu says "no draught animals, no iron, no wheel in
# practical use" and horse_collar was startable on arrival in the Valley of
# Mexico in 1500, with `why` still calling it a collar for a draught horse.
_mex = sim(civ="mexica_1500")
_HORSE = "horse_collar"
_ok_h, _why_h = _mex.start_reason(_HORSE)
check("a society with no draught animal cannot begin draught-animal work",
      not _ok_h and "draught animal" in _why_h, _why_h)
check("...and the refusal names the one thing that would open it",
      "exp_import_draught_animals" in _why_h, _why_h)
check("...and it is not in what you could begin today",
      not any(entry["id"] == _HORSE
              for entry in S._agent_available(_mex, NODES, {"all": True})["available"]),
      _HORSE)
_mex.done.add("exp_import_draught_animals"); _mex._done_changed()
check("...and bringing the animals across opens all of it at once",
      _mex.needs_first(_HORSE)[0] is None, _mex.needs_first(_HORSE))
_rom = sim(civ="rome_100ad")
check("a society that HAS horses is not gated at all (the control case)",
      _rom.needs_first(_HORSE)[0] is None, _rom.needs_first(_HORSE))
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

# --- BREAK: Han China was told it writes its corpus "in plain quantitative
# Greek and Latin" and seeks "Senatorial patronage".
for _cid, _bad in (("han_china_100ad", "Greek and Latin"),
                   ("norse_900ad", "Senatorial patronage"),
                   ("mexica_1500", "Greek and Latin"),
                   ("england_1300", "Senatorial patronage")):
    _rl, _, _ = proto([{"cmd": "why", "id": "corpus_written"},
                       {"cmd": "why", "id": "patron_senatorial"}], civ=_cid)
    check("%s is not handed Rome's own words" % _cid,
          _bad not in json.dumps(_rl), _bad)
_rr, _, _ = proto([{"cmd": "why", "id": "corpus_written"}], civ="rome_100ad")
check("...and Rome, which the tree is written from, is left alone",
      "Greek and Latin" in json.dumps(_rr), json.dumps(_rr)[:120])

# --- BREAK: the advertised price index touched nothing a player feels.
# Revenue ~233 and living costs 230.0 TO THE DECIMAL in all five civs, against
# a selection screen advertising "prices 0.75x to 1.40x Rome" - while project
# costs, wages, the workshop's output and state funding all did scale, so an
# expensive society paid 1.4x to build and ate at Roman prices.
_lc, _rv = {}, {}
for _cid in ("rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500",
             "england_1300"):
    _s = sim(civ=_cid)
    _lc[_cid] = round(_s.living_cost(), 2)
    _rv[_cid] = round(_s.revenue(), 2)
check("living costs follow this society's price level",
      len(set(_lc.values())) == 5, _lc)
check("...and so does what your practice pays",
      len(set(_rv.values())) == 5, _rv)
check("...and the dearest society really is the dearest",
      max(_lc, key=lambda c: _lc[c]) == "norse_900ad", _lc)
check("...and the cheapest really is the cheapest",
      min(_lc, key=lambda c: _lc[c]) == "han_china_100ad", _lc)

# --- BREAK: rubber was priced at 99,999 a kilo, a sentinel left over from the
# abolished "unobtainable" tier, and it survived the abolition of the concept
# that justified it. A play tester worked out that one kilo was four hundred
# artisan-years, that a rubber eraser cost 3,001,105 against 5 for a
# breadcrumb, and that securing a rubber supply did not change the price by a
# denarius. It was also over half of the whole tree's capital cost.
_RUB = ("rubber_kg", "rubber_tubing_kg")
for _r in _RUB:
    check("%s is priced like a distant import, not like a sentinel" % _r,
          0 < PRICES["purchase_prices_denarii"][_r]["p"] < 1000,
          PRICES["purchase_prices_denarii"][_r]["p"])
# ...and the reason the sentinel existed - that nothing stopped you buying it -
# is answered where it belongs, in the tree: you cannot use rubber until you
# have gone and got some.
def _anc_of(k, seen=None):
    seen = seen if seen is not None else set()
    for prereq_id in NODES[k]["pre"]:
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

# --- BREAK: grant_ambient ran BEFORE the civ's named starting_techs were
# added, so anything they unlocked was credited on the player's first `step`
# and printed as "COMPLETED 100: Amphitheatre with tiered seating" - a
# completion for something they had never started, in the same words as their
# own work. Nothing free may arrive after the game begins.
for _civ_ga in ("rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500",
                "england_1300"):
    _s_ga = sim(civ=_civ_ga)
    _before_ga = set(_s_ga.done)
    _s_ga.step()
    check("%s hands you nothing free on turn one" % _civ_ga,
          not (_s_ga.done - _before_ga), sorted(_s_ga.done - _before_ga))

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
