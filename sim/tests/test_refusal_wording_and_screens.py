"""refusal_wording_and_screens: regression checks, run individually with `--only refusal_wording_and_screens`."""
from .harness import *  # noqa: F401,F403
from sim.ui import protocol as _PROTO

# THE PATRONAGE REFUSAL LEAKED AN ID, AND HANDED OUT A COMMAND THAT WOULD BE
# REFUSED. A naive Mexica player read "get at least a local patron first:
# 'start patron_local'" in `available`, typed exactly that, and was told by
# the same engine one command later: "you have never heard of any such
# thing." Two faults in one line. Under fog it is a free reveal of an
# undiscovered node, which is the third time this exact filter has been
# skipped by a second caller (start_reason had it, `bounty` skipped it, and
# `why` leaked another node's id through its kb path). And the advice is
# worth nothing in any case when the command it names is refused.
_s_pat = sim(civ="mexica_1500")
_s_pat.fog = True
_s_pat.revealed = set()
_pat_wary = None
for _k in sorted(NODES):
    _ok, _w = _s_pat.start_reason(_k)
    if _w and "state is wary" in _w:
        _pat_wary = _w
        break
check("the patronage refusal fires for a fogged Mexica founder at all, so "
      "the rest of these checks are testing something real",
      _pat_wary is not None, _pat_wary)
check("...and does not name patron_local, which this founder has never "
      "heard of and could not start if they tried",
      _pat_wary is not None and "patron_local" not in _pat_wary, _pat_wary)
check("...and still says what is actually wanted, in words rather than an "
      "id, so the refusal remains useful advice",
      _pat_wary is not None and "patron" in _pat_wary
      and "before anyone here will let you begin" in _pat_wary, _pat_wary)

_s_pat2 = _s_pat      # no fog: the id IS the useful answer
_s_pat2.fog = False
_pat_wary2 = None
for _k in sorted(NODES):
    _ok, _w = _s_pat2.start_reason(_k)
    if _w and "state is wary" in _w:
        _pat_wary2 = _w
        break
# A REFUSAL MAY NEVER RECOMMEND A REFUSAL. That was the whole complaint, and
# the fog was only half of it: patron_local itself wants identity_cover, so
# even with the fog off "get a local patron first: 'start patron_local'" sent
# the player into "missing prerequisites: identity_cover". So the rule is
# conditional, and both branches are checked: name the command only when it
# would actually be accepted, and otherwise name what is standing in the way.
_pat_can2, _ = _s_pat2.start_reason("patron_local")
check("without fog, the refusal names 'start patron_local' only when that "
      "command would actually be accepted, and otherwise says what "
      "patron_local is itself waiting on",
      (("start patron_local" in _pat_wary2) if _pat_can2
       else ("start patron_local" not in _pat_wary2
             and "itself wants" in _pat_wary2)), (_pat_can2, _pat_wary2))

_s_pat4 = _s_pat
_s_pat4.done.add("identity_cover")
_s_pat4._done_changed()
_pat_wary4 = None
for _k in sorted(NODES):
    _ok, _w = _s_pat4.start_reason(_k)
    if _w and "state is wary" in _w:
        _pat_wary4 = _w
        break
_pat_can4, _pat_why4 = _s_pat4.start_reason("patron_local")
check("...and once patron_local IS startable, the refusal hands over the "
      "exact command, and that command is genuinely accepted",
      _pat_can4 and _pat_wary4 is not None
      and "start patron_local" in _pat_wary4, (_pat_why4, _pat_wary4))

# THE SENATORIAL HALF OF THE SAME LINE, which had the identical hardcoded id.
_s_pat3 = sim(civ="rome_100ad")
_s_pat3.fog = True
_s_pat3.revealed = set()
_pat_sen = [_warning for _warning in
            (_s_pat3.start_reason(_node_id)[1] for _node_id in sorted(NODES))
            if _warning and "actively opposes" in _warning]
check("the senatorial-patronage refusal does not leak its id under fog "
      "either",
      not any("patron_senatorial" in _warning for _warning in _pat_sen),
      _pat_sen[:1])

# THE POLICY SCREEN GROUPS BY WHAT IS ACTUALLY RUNNING. An England play
# tester read auto_open's description ("opens concerns that plainly pay for
# themselves"), built a pawnshop that plainly paid for itself, watched
# nothing happen, and reported the policy as not matching its own
# description. The screen was correct - "off" was printed directly above that
# sentence - but every description is in the present indicative, so a reader
# scanning them reads eleven statements of what the game is doing while ten
# of them are hypothetical. Verified separately that auto_open itself is not
# broken: with the policy on, auto_open_ventures does open that pawnshop.
_s_pol = sim(civ="england_1300")
_pol_out = S._agent_dispatch(_s_pol, NODES, {"cmd": "policy"})
_pol_txt = _PROTO.render_policy(_pol_out)
check("the policy screen says which automatic behaviours are running now "
      "and which are only descriptions of what would happen",
      "RUNNING NOW:" in _pol_txt and "NOT RUNNING" in _pol_txt
      and "WOULD do if you turned it on" in _pol_txt, _pol_txt[:300])
check("...with every switch still listed exactly once between the two "
      "groups, none dropped by the grouping",
      all(_node_id in _pol_txt for _node_id in (_pol_out.get("policy") or {}))
      and all(_pol_txt.count("  %-18s " % _node_id) == 1
              for _node_id in (_pol_out.get("policy") or {})),
      sorted(_pol_out.get("policy") or {}))

# AND THE THING THEY THOUGHT WAS BROKEN IS NOT BROKEN.
_s_pol2 = _s_pol
_s_pol2.done.add("fin_restaurant")
_s_pol2._done_changed()
check("auto_open really would open a concern that plainly pays for itself: "
      "the pawnshop's 144 to open against 250 a year clear is a payback "
      "well under a year, and auto_open_ventures takes it",
      "fin_restaurant" in _s_pol2.auto_open_ventures(),
      (NODES["fin_restaurant"]["rev"], NODES["fin_restaurant"]["up"],
       _s_pol2.venture_capex("fin_restaurant")))
check("...and it was off by default, which is the whole of why they did not "
      "see it happen",
      _s_pol.policy.get("auto_open") is False,
      _s_pol.policy)

# "NOTHING ELSE RESTS ON THIS" HAS TO MEAN ZERO. A naive Rome player caught
# the game contradicting itself inside a minute: `why met_ore_crushing_sorting`
# answered "HOW MUCH RESTS ON THIS: nothing else; this is worth having for
# itself", while met_jigging_gravity, visible in their own list, refused with
# "missing prerequisites: met_ore_crushing_sorting". They found the same pair
# again in in2_tape_measure_steel and in2_baseline_measurement_apparatus. The
# bottom band covered 0 through 3. Banding is the right answer to the spoiler
# problem - the exact count is a map of the tree - but a band whose words are
# false is not. Vague is allowed, wrong is not.
check("only a genuine zero is described as having nothing resting on it",
      _PROTO._rests_band(0).startswith("nothing else")
      and not any(_PROTO._rests_band(_downstream_count).startswith("nothing else")
                  for _downstream_count in (1, 2, 3, 4, 41, 301, 1201)),
      [(_downstream_count, _PROTO._rests_band(_downstream_count)) for _downstream_count in (0, 1, 2, 3, 4)])
check("...and the bands still climb, so the new rung did not break the "
      "ladder",
      len({_PROTO._rests_band(_downstream_count) for _downstream_count in (0, 1, 4, 41, 301, 1201)}) == 6,
      [_PROTO._rests_band(_downstream_count) for _downstream_count in (0, 1, 4, 41, 301, 1201)])
check("...and every band has a short form for the column that renders it",
      all(_PROTO._rests_band(_downstream_count) in _PROTO._RESTS_SHORT
          for _downstream_count in (0, 1, 4, 41, 301, 1201)),
      sorted(_PROTO._RESTS_SHORT))

# THE TWO PAIRS THEY ACTUALLY REPORTED, end to end through `why`.
_s_rb = sim()
for _a, _b in (("met_ore_crushing_sorting", "met_jigging_gravity"),
               ("in2_tape_measure_steel",
                "in2_baseline_measurement_apparatus")):
    _rb_why = S._agent_dispatch(_s_rb, NODES, {"cmd": "why", "id": _a})
    _rb_rests = _rb_why.get("how_much_rests_on_this")
    check("%s does not claim nothing rests on it, when %s names it as a "
          "missing prerequisite" % (_a, _b),
          _a in NODES[_b]["pre"]
          and not (_rb_rests or "").startswith("nothing else"),
          (_rb_rests, NODES[_b]["pre"]))

# AND THE CLASS: no node with a dependent may say nothing rests on it.
_rb_kids = collections.Counter()
for _k, _n in NODES.items():
    for _p in _n["pre"]:
        _rb_kids[_p] += 1
_rb_liars = [_node_id for _node_id in sorted(NODES)
             if _rb_kids[_node_id] > 0
             and _PROTO._rests_band(_rb_kids[_node_id]).startswith("nothing else")]
check("no node in the whole tree that something else depends on is "
      "described as having nothing resting on it",
      not _rb_liars, _rb_liars[:8])
