"""state_notices: regression checks, run individually with `--only state_notices`."""
from .harness import *  # noqa: F401,F403
from sim.ui import protocol as _PROTO

# --- the state notices you: requisition, office, military demand, ----------
# --- confiscation as a tail risk (society.py, all five civilization files) -
# A player who had already won the game with 691 employees, 1.1 billion
# denarii, working firearms, a power grid and a railway found that the state
# had never once requisitioned output, demanded military supply, pressed an
# office, or threatened confiscation - unrealistic in a specific way, since
# state predation on large private enterprise is one of the most reliable
# facts of pre-industrial economic history. These checks are for the fix.
_ALL_CIVS = ("rome_100ad", "han_china_100ad", "england_1300", "norse_900ad",
             "mexica_1500")

_s0 = sim(civ="rome_100ad")
check("a fresh household is below the line - the state has not noticed it yet",
      _s0.state_notice() < 0.02, _s0.state_notice())
check("...and state_pressure_report() says so with nothing to show, "
      "not a sentence repeated on every dormant turn",
      _s0.state_pressure_report() is None, _s0.state_pressure_report())
for _cv in _ALL_CIVS:
    _sp = S.load_civ(_cv).get("state_pressure") or {}
    check("%s: its civilization file carries its OWN requisition/office/"
          "military/confiscation names and notes, not a shared generic one"
          % _cv,
          all(_sp.get(field_name) for field_name in (
              "requisition_name", "requisition_note",
              "office_name", "office_note",
              "military_name", "military_note",
              "confiscation_name", "confiscation_note")),
          _sp)


def _grown(civ, employees=300.0, capital=3000000.0, eminence=20.0):
    """A household large enough to be past STATE_NOTICE_THRESHOLD on every
    civilisation whose state_capacity is not Norse's - built once here
    rather than copied into every check below.
    """
    grown_sim = sim(civ=civ, events=True)
    grown_sim.employees["artisan"] = employees
    grown_sim.labour._resync_pools()
    grown_sim.capital = capital
    grown_sim.eminence = eminence
    grown_sim.update_protection()
    return state_seeking(grown_sim)


_big = _grown("rome_100ad")
check("a household with 300 employees, 3,000,000 denarii and an eminence "
      "of 20 is past the general notice line for Rome (state_capacity 0.85)",
      _big.state_notice() > _big.STATE_NOTICE_THRESHOLD, _big.state_notice())
_req_share, _req_why = _big.requisition_report()
_off_share, _off_name = _big.office_report()
check("...and requisition now takes a real, nonzero share of revenue",
      _req_share > 0.0, _req_share)
check("...priced in this civilisation's own words, not a generic label",
      _off_name == _big.civ["state_pressure"]["office_name"], _off_name)
check("...and the office costs something too, alongside requisition",
      _off_share > 0.0, _off_share)

_pressed_protection = _big.protection   # as _grown left it
_big.protection = 0.0
_poor_requisition, _poor_office = _big.requisition_report()[0], _big.office_report()[0]
_big.protection = 0.85
_rich_requisition, _rich_office = _big.requisition_report()[0], _big.office_report()[0]
_big.protection = _pressed_protection
check("requisition is bargained down by protection - patronage and standing "
      "are not decorative here",
      _rich_requisition < _poor_requisition, (_rich_requisition, _poor_requisition))
check("...but the office is NOT bargained down the same way - it is the "
      "version you do not get to decline cheaply",
      abs(_rich_office - _poor_office) < 1e-9, (_rich_office, _poor_office))

_prot_before = sim(civ="rome_100ad")
_prot_before.update_protection()
_small_protection = _prot_before.protection
check("being pressed into office is also a shield: crossing the notice line "
      "raises protection by itself, on top of anything built",
      _pressed_protection > _small_protection, (_pressed_protection, _small_protection))

_no_mil = _grown("rome_100ad")
check("no militarily significant technology done: the state has nothing to "
      "ask this household for",
      not _no_mil.military_demand_eligible(), _no_mil.military_leverage())
_mil_done = _no_mil
_mil_done.done.update(node_id for node_id in NODES if "military" in NODES[node_id].get("traits", ())
)
_mil_done._done_changed()
check("...but the FIRST working gun (one military-branch node, not a "
      "standing army) is already enough to be asked for",
      _mil_done.military_leverage() >= _mil_done.MIL_LEVERAGE_FLOOR_FOR_DEMAND
      and _mil_done.military_demand_eligible(),
      _mil_done.military_leverage())

_tiny_notice = sim(civ="rome_100ad")
_tiny_notice.employees["artisan"] = 2.0
_tiny_notice.labour._resync_pools()
check("military demand still needs SOME visible scale - a founder who has "
      "merely studied cannon, with no household to speak of, is not yet "
      "worth a state's letter",
      not (_tiny_notice.military_leverage() >= 0.2
           and _tiny_notice.state_notice() > _tiny_notice.STATE_NOTICE_THRESHOLD_MILITARY),
      _tiny_notice.state_notice())

# 60 million coin at the old coin value, stated in labour hours so it does not
# move with what the coin metal costs
HUGE_CAPITAL_ROME = 2.24e8 * sim(civ="rome_100ad").labour.money_per_labour_hour()
_huge = _grown("rome_100ad", employees=2000.0, capital=HUGE_CAPITAL_ROME, eminence=25.0)
check("confiscation is a TAIL risk: it stays at zero until well past the "
      "general notice line, not the moment requisition starts",
      _big.confiscation_risk()[0] == 0.0 and _big.state_notice() > _big.STATE_NOTICE_THRESHOLD,
      (_big.state_notice(), _big.confiscation_risk()[0]))
check("...and only arrives once a household is truly enormous",
      _huge.confiscation_risk()[0] > 0.0, _huge.state_notice())

_huge_bare_risk = _huge.confiscation_risk()[0]
_huge_shielded = _huge
_huge_shielded.protection = 0.85
_huge_shielded.done.add("academy_network")
_huge_shielded._done_changed()
_huge_shielded.done.update(node_id for node_id in NODES if "military" in NODES[node_id].get("traits", ())
)
_huge_shielded._done_changed()
check("confiscation is mitigable, by exactly the things that mitigated it "
      "historically: a patron/standing, dispersed holdings, and being "
      "useful to a state that fights, ALL reduce the tail risk together",
      _huge_shielded.confiscation_risk()[0] < _huge_bare_risk,
      (_huge_shielded.confiscation_risk()[0], _huge_bare_risk))

_norse_extreme = sim(civ="norse_900ad")
_norse_extreme.employees["artisan"] = 2000.0
_norse_extreme.labour._resync_pools()
_norse_extreme.capital = 60000000.0
_norse_extreme.eminence = 30.0
check("Norse state_capacity (0.15) caps notice so low that even an "
      "extravagantly large household crosses no threshold here - 'the "
      "thing is an assembly, not a state' is a real mechanical floor, not "
      "only a line in the opening text",
      _norse_extreme.state_notice() < _norse_extreme.STATE_NOTICE_THRESHOLD
      and _norse_extreme.requisition_report()[0] == 0.0,
      _norse_extreme.state_notice())
_norse_built = state_seeking(sim(civ="norse_900ad"))
_norse_built.civ["state_capacity"] = 0.9          # as if centuries of kings,
_norse_built.state_capacity = 0.9                 # bishops and taxes arrived
_norse_built.employees["artisan"] = 2000.0
_norse_built.labour._resync_pools()
_norse_built.capital = 60000000.0
_norse_built.eminence = 30.0
check("...but a Norse state that DID build up state_capacity (the same "
      "tech-effect field every civilisation reads) is judged by the exact "
      "same rule as everyone else, not given a permanent exemption",
      _norse_built.requisition_report()[0] > 0.0, _norse_built.requisition_report())

# Fog safety (hard rule 3): nothing this mechanic prints may name a node id
# the player has not discovered. _state_pressure only ever uses this
# civilisation's own plain-language state_pressure names, never a tech id.
_fogged = _huge
_fogged.fog = True
_fogged.year = _fogged.year
_before_log = len(_fogged.log)
_fogged._state_pressure(_fogged.year)
_new_lines = " ".join(message for _year, message in _fogged.log[_before_log:])
_leaked = [node_id for node_id in NODES if node_id in _new_lines]
check("the state-notices-you log lines never leak a bare node id, under fog "
      "or off it - only this civilisation's own plain historical names",
      not _leaked, _leaked[:5])

# Determinism/dice-free guarantee: the probabilistic rolls (military demand,
# confiscation) must answer to `events`, the same switch every other
# probabilistic hazard in this file already answers to - a dice-free trial
# (path_search.py's own DetRNG, events=False) must see none of them fire,
# while the deterministic tax (requisition/office) is not a "dice" and must
# apply either way.
class _AlwaysFires(random.Random):
    def random(self):
        return 0.0


_det_off = _grown("rome_100ad", employees=2000.0, capital=HUGE_CAPITAL_ROME, eminence=25.0)
_det_off.events = False
_det_off.rng = _AlwaysFires(1)
_cap_before_off = _det_off.capital
_det_off._state_pressure(_det_off.year)
check("with events off, the probabilistic confiscation/military rolls never "
      "actually fire even when the rng would always take them - the warning "
      "that one is APPROACHING is allowed through regardless, the same way "
      "eminence's own conspicuousness warning in core.py's step() is not "
      "gated on events either, only its dice roll is",
      not any("handed over" in message or "the state takes what it judges" in message
             for _year, message in _det_off.log[-5:]),
      [message for _year, message in _det_off.log[-5:]])
check("...but the deterministic requisition/office tax still applies - it "
      "is not a roll of the dice, and a dice-free trial must still feel it",
      _det_off.capital < _cap_before_off, (_det_off.capital, _cap_before_off))

_det_on = _grown("rome_100ad", employees=2000.0, capital=HUGE_CAPITAL_ROME, eminence=25.0)
_det_on.events = True
_det_on.rng = _AlwaysFires(1)
_det_on._state_pressure(_det_on.year)
check("...and with events on, the same always-fires rng DOES produce the "
      "confiscation tail event this time",
      any("the state takes what it judges" in message for _year, message in _det_on.log),
      [message for _year, message in _det_on.log[-5:]])
