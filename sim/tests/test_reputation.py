"""reputation: regression checks, run individually with `--only reputation`."""
from .harness import *  # noqa: F401,F403

"""reputation: the tree's data after the tester reports (upkeep of techniques, rubber made not bought, England's iron,
the Norse keel, the blind prerequisite audit), the standing finishing a node adds, and what makes a node a concern. The
data checks read the tree; the gain and the concern rule run on a stand-in game (no game is built). Who a society is
granted at the start is test_reputation_scenario."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.projects import constants as projects_constants
from sim.tests import production_host, projects_host

QUICK_TOPIC = True


def _Finishing(interest):
    """The reputation gain of a finished node, over a state interest the test sets. The module has no `operating` of any kind
    set up, so the gain cannot read whether the node was ever opened."""
    return projects_host.build(state_interest=lambda node: interest, operating=None)


_base = _Finishing(0.0).reputation_gain_of({"rev": 0})
check("finishing a node with no revenue and no state interest adds the base standing",
      _base == projects_constants.REPUTATION_GAIN_BASE, _base)
check("revenue adds the revenue bonus",
      abs(_Finishing(0.0).reputation_gain_of({"rev": 5}) - _base - projects_constants.REPUTATION_GAIN_REVENUE_BONUS) < 1e-12)
check("state approval adds its coefficient times the interest, and disapproval subtracts nothing",
      abs(_Finishing(2.0).reputation_gain_of({"rev": 0}) - _base - 2.0 * projects_constants.REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT) < 1e-12
      and _Finishing(-3.0).reputation_gain_of({"rev": 0}) == _base)
# FINDING (diagnosed, not changed): standing rewards completion, not use. The stand-in above has no set of running
# concerns, so a gain that read one would raise; it does not.
check("the gain reads only the node and the state's regard, so a node finished and never opened earns the same standing as one that runs",
      _Finishing(1.0).reputation_gain_of({"rev": 1}) > _base)


def _Concerns(nodes, granted=()):
    """What makes a node a going concern: it earns or costs to keep, and the society did not already have it."""
    return production_host.build(tree_nodes=nodes, techniques_granted=set(granted))


_nodes = {"theory": {"rev": 0.0, "up": 0.0}, "shop": {"rev": 10.0, "up": 0.0}, "plant": {"rev": 0.0, "up": 5.0}}
_concerns = _Concerns(_nodes, granted=("plant",))
check("a node that neither earns nor costs to keep is knowledge, not a concern to open",
      _concerns.is_venture("theory") is False)
check("a node that earns, or costs to keep, is a concern",
      _concerns.is_venture("shop") is True and _Concerns(_nodes).is_venture("plant") is True)
check("...but not one the society was already given", _concerns.is_venture("plant") is False and _concerns.is_concern_node("plant") is True)
check("an unknown node is no concern", _concerns.is_venture("nothing") is False)

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
      _Concerns(NODES).is_venture("em_theory") is False)
# And the flip side: an actual furnace you fire every day still costs
# something to keep firing, same as before the audit.
check("a furnace you actually run still carries real upkeep",
      NODES["met_open_hearth_furnace"]["up"] > 0,
      NODES["met_open_hearth_furnace"]["up"])
# A venture that sells something was never in scope for the audit - revenue
# is what makes it a going concern in the first place - so blast_furnace,
# which both sells cast iron and costs money to run, keeps a running cost. That
# cost is now derived from its staff and plant (sim/engine/node_upkeep.py),
# not the authored figure the audit once left alone.
check("a venture that already sells something keeps its upkeep",
      NODES["blast_furnace"]["up"] > 0 and NODES["blast_furnace"]["rev"] > 0,
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
# THE CLAIM, NOT A TOTAL: a hard total (157, pinned in an earlier version of
# this check) is a check on where the goal happens to sit, and breaks the
# moment the goal moves - as it did, from the 1947 point-contact device to
# the 1951 junction transistor. The thing the audit actually claimed is that
# these four additions were cheap, and that is what is worth pinning.
# Marginal cost is the closure of the addition MINUS what the goal already
# needed, which is the number a previous
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
