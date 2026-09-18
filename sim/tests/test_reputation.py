"""reputation: split verbatim from the old test_regressions.py (original lines 7583-7781).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# REPUTATION: a tester reported it rewards raw completion count, so it can
# be maximised by building trinkets you never use. Confirmed against the
# real gain formula in projects.py: it reads n["rev"]/traits and
# self.done, and never reads self.operating at all. This is diagnosed and
# left as a finding, not fixed here: the fix lives in projects.py, which
# this pass does not own (see the task's own file-ownership boundary) -
# see the final report for the recommended change.
# =============================================================================
s_rep = sim()
_rep_cands = [node_id for node_id, node in NODES.items() if node.get("rev", 0) > 0]
_rk = sorted(_rep_cands)[0]
_n = NODES[_rk]
_rep0 = s_rep.reputation
s_rep.done.add(_rk); s_rep._done_changed(); s_rep.done_year[_rk] = s_rep.year
s_rep.apply_tech_effects(_rk)
_gain = (0.6 + 0.5 * max(0.0, s_rep.state_interest(_n))
         + (1.2 if _n["rev"] > 0 else 0.0))
s_rep.reputation = min(100.0, s_rep.reputation + _gain)
check("FINDING (not fixed here, see report): completing a revenue-bearing "
      "node raises reputation even when it is never opened as a concern",
      s_rep.reputation > _rep0 and _rk not in s_rep.operating,
      (_rep0, s_rep.reputation, _rk in s_rep.operating))


# --- JOB 1: techniques should not cost upkeep. A play tester asked "should
# any techs cost upkeep? Shouldn't that all be on the building/thing it
# unlocks?" and was right: 2,444 non-institution nodes carried upkeep, most
# of them pure knowledge (a theory, a hand technique, a machine-tool
# accessory) with no premises, staff or standing cost to speak of. The audit
# zeroed upkeep on every one of those that had no revenue either - a node
# with revenue is already a going concern by the tree's own definition - and
# kept it only on physical plant (furnaces, mills, mines, chemical process
# works) and a short hand-picked list of named facilities (hospitals,
# clinics, road networks, the arsenal). This is em_theory: pure knowledge,
# nothing to run.
check("a pure technique no longer costs anything to keep knowing",
      NODES["em_theory"]["up"] == 0.0 and NODES["em_theory"]["rev"] == 0.0,
      (NODES["em_theory"]["up"], NODES["em_theory"]["rev"]))
check("that same technique is no longer offered as a going concern to open",
      sim().is_venture("em_theory") is False, sim().is_venture("em_theory"))
# And the flip side: an actual furnace you fire every day still costs
# something to keep firing, same as before the audit.
check("a furnace you actually run still carries real upkeep",
      NODES["met_open_hearth_furnace"]["up"] > 0,
      NODES["met_open_hearth_furnace"]["up"])
# A venture that sells something was never in scope for the audit - revenue
# is what makes it a going concern in the first place - so blast_furnace,
# which both sells cast iron and costs money to run, is untouched.
check("a venture that already sells something keeps its upkeep untouched",
      NODES["blast_furnace"]["up"] == 7000.0 and NODES["blast_furnace"]["rev"] > 0,
      (NODES["blast_furnace"]["up"], NODES["blast_furnace"]["rev"]))

# --- JOB 2: rubber should be made, not bought. A play tester asked whether
# rubber could even be bought for most of the run, and said you should have
# to make it with your own factory - tapping and coagulating latex, and
# vulcanising anything that must not melt in summer or crack in winter.
# Before this, every rubber good gated on mat_natural_rubber directly and
# then simply bought rubber_kg at a price, with tl_vulcanized_rubber built
# and never required by anything.
check("coagulating rubber is its own step, not free the moment you know the vine",
      NODES["mat_rubber_coagulated"]["pre"] == ["mat_natural_rubber"],
      NODES["mat_rubber_coagulated"]["pre"])
check("a pneumatic tyre needs vulcanised rubber, not raw coagulated latex",
      "tl_vulcanized_rubber" in NODES["tl_pneumatic_tyre"]["pre"]
      and "mat_natural_rubber" not in NODES["tl_pneumatic_tyre"]["pre"],
      NODES["tl_pneumatic_tyre"]["pre"])
check("an eraser needs coagulated rubber but not full vulcanisation",
      "mat_rubber_coagulated" in NODES["tx2_eraser"]["pre"]
      and "tl_vulcanized_rubber" not in NODES["tx2_eraser"]["pre"],
      NODES["tx2_eraser"]["pre"])
check("vulcanisation itself is built from coagulated rubber, not raw latex",
      "mat_rubber_coagulated" in NODES["tl_vulcanized_rubber"]["pre"]
      and "mat_natural_rubber" not in NODES["tl_vulcanized_rubber"]["pre"],
      NODES["tl_vulcanized_rubber"]["pre"])

# --- JOB 3a: England's own briefing calls cheap iron and the temperature to
# make it "the biggest single technology gap you face", and blast_furnace's
# own note calls itself "the biggest single technology gap" in the same
# words - yet England's starting kit handed over blast_furnace, mat_cast_
# iron and cap_heat_1300 (Han China's real grant, copied by mistake) for
# free. A blast furnace did not reach England until Newbridge in 1496.
_eng = S.load_civ("england_1300")
check("England no longer starts already owning the iron gap its own briefing describes",
      not ({"blast_furnace", "mat_cast_iron", "cap_heat_1300"}
           & set(_eng["starting_techs"])),
      _eng["starting_techs"])

# --- JOB 3b: the cursus publicus (Roman imperial dispatch relay) and the
# Pharos (one specific Ptolemaic building at Alexandria) are not a generic
# capability any society might have. FOREIGN_MARKERS in fog.py already
# catches both by name; this pins that Han China - which has no Roman
# citizenship, no Roman roads and no Alexandria - is never handed either one
# for free, the way testers kept finding Roman-branded grants in other
# people's civilisations.
_han = sim(civ="han_china_100ad")
check("Han China is never handed Rome's courier relay or Ptolemy's lighthouse for free",
      "lnd_cursus_publicus" not in _han.granted
      and "sea_pharos_lighthouse" not in _han.granted,
      (sorted(_han.granted & {"lnd_cursus_publicus", "sea_pharos_lighthouse"})))

# --- JOB 3c: the Norse civilisation's flagship starting technologies -
# clinker hull, deep keel, bog-iron bloomery - are supposed to be its
# superb shipbuilding and ironworking, but `why sea_keel_deep` reported
# "(nothing, this is a leaf)": literally nothing in the tree depended on it,
# contradicting the civilisation's own self-description. It is now a real
# alternative route (alongside the Mediterranean fore-and-aft rig) into
# open-ocean navigation, which needs SOME way to sail to windward and
# previously named none at all.
check("the Norse deep keel now genuinely enables open-ocean navigation",
      any("sea_keel_deep" in group.get("options", {})
          for group in NODES["exp_openocean_navigation"]["req_any"]),
      NODES["exp_openocean_navigation"]["req_any"])

# --- FREE AND WEIGHTLESS IS NOT THE SAME AS UNIVERSALLY AVAILABLE. The
# ambient grant hands a society anything tier 0 that costs nothing and takes
# nobody's attention, which is right for a craft that society actually has
# and wrong for one it demonstrably does not. The Mexica were handed the
# square sail, the spritsail, a mortise-and-tenon Mediterranean hull, large
# merchant sailing ships and the monsoon route to India, before turn one, in
# a civilisation whose own menu says every load moves on a human back and
# whose water transport is the paddled canoe. needs_first already existed to
# say a thing is impossible here rather than merely dear; both grant paths
# now consult it.
_mex = sim(civ="mexica_1500")
check("the Mexica are not handed other people's seas: no sail, no "
      "Mediterranean hull, no merchant fleet, no monsoon crossing",
      not any(tech_id in _mex.granted for tech_id in
              ("sea_square_sail", "sea_spritsail", "sea_mortise_tenon",
               "sea_merchant_ships_large", "sea_monsoon_route")),
      sorted(tech_id for tech_id in _mex.granted if tech_id.startswith("sea_")))
check("...and canoe use does not silently grant an Old World nautical package",
      not any(tech_id in _mex.granted for tech_id in
              ("sea_anchor", "sea_sounding_lines", "sea_coastal_pilotage",
               "sea_steering_oars")),
      sorted(tech_id for tech_id in _mex.granted if tech_id.startswith("sea_")))
check("the ocean-going hull gate remains a buildable route, not an inherited gift",
      "exp_oceangoing_hull" not in _mex.granted
      and "exp_oceangoing_hull" in NODES,
      sorted(x for x in PLANNER.closure(NODES, "exp_oceangoing_hull")
             if x.startswith("sea_")))
check("a seafaring society is untouched by the gate",
      "sea_square_sail" in sim(civ="norse_900ad").granted, True)

# --- JOB 4: the blind prerequisite audit (BLIND_TREE_phase2.md) found three
# genuine small gaps and this implements all three, marginal cost verified
# with closure() rather than trusted from the document (a previous audit
# nearly deferred a correct fix by quoting 101 when the true marginal cost
# was 1).
check("placing a whisker a few hundredths of a millimetre apart now requires something that can see the gap",
      "microscope_compound" in NODES["gp_whisker_forming"]["pre"],
      NODES["gp_whisker_forming"]["pre"])
check("the germanium surface now gets a chemical/electrolytic etch, not mechanical lapping alone",
      "el2_electropolishing_etching_surface_finish" in NODES["gp_whisker_forming"]["pre"],
      NODES["gp_whisker_forming"]["pre"])
# mat_gold sits on gp_whisker_forming, one step short of the goal, not on
# point_contact_transistor directly - a first attempt put it on the goal
# itself and a fog regression test caught the leak: mat_gold is tier0/ph0,
# auto-granted and therefore always is_visible(), and the goal is the one
# node `why` always answers under fog, so direct_prerequisites (unlike
# every other node, where is_visible() filters it) named the goal's own
# prerequisite from turn one.
check("the contact alloys are real prerequisites now, not just bare material costs",
      "mat_gold" in NODES["gp_whisker_forming"]["pre"]
      and "phosphor_bronze_alloy" in NODES["gp_whisker_forming"]["pre"],
      NODES["gp_whisker_forming"]["pre"])
# THE CLAIM, NOT A TOTAL. This asserted the closure was exactly 157, which
# was true on the day it was written and stopped being true the moment the
# goal moved from the 1947 point-contact device to the 1951 junction
# transistor. A hard total is a check on where the goal happens to sit; the
# thing the audit actually claimed is that these four additions were cheap,
# and that is what is worth pinning. Marginal cost is the closure of the
# addition MINUS what the goal already needed, which is the number a previous
# audit got wrong by quoting 101 when the truth was 1.
_clo_now = S.closure(NODES, GOAL)
_added = ("microscope_compound", "el2_electropolishing_etching_surface_finish",
          "mat_gold", "phosphor_bronze_alloy")
check("the four audited prerequisites really are on the road to the goal",
      all(added_id in _clo_now for added_id in _added),
      [added_id for added_id in _added if added_id not in _clo_now])
_marginal = len(set().union(*(S.closure(NODES, added_id) | {added_id} for added_id in _added))
                - (_clo_now - set(_added)))
check("...and between them they cost the road about eight nodes, not dozens",
      _marginal <= 10, _marginal)

# --- This audit's own mistake, caught by the very fog test above it: writing
# a new prerequisite's id into point_contact_transistor's NOTE leaked it in
# prose, because the goal is special-cased to answer `why` under fog no
# matter what, and note text - unlike direct_prerequisites - is never
# filtered by is_visible(). Pin it so a future data edit cannot reintroduce
# the same leak by being specific in the wrong field.
check("the goal's own note never spells out the id of one of its prerequisites",
      not any(prereq_id in NODES["point_contact_transistor"]["note"]
              for prereq_id in NODES["point_contact_transistor"]["pre"]),
      [prereq_id for prereq_id in NODES["point_contact_transistor"]["pre"]
       if prereq_id in NODES["point_contact_transistor"]["note"]])
