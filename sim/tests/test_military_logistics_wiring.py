"""test_military_logistics_wiring: the ONE crossing wiring sim/world/
military_logistics.py into sim/engine/society.py, and only that crossing.

See sim/world/military_logistics.py's module docstring ("BUILT STANDALONE;
NOW WIRED IN, ONE CROSSING ONLY") and SocietyMixin.military_equipment_
burden_kg_per_soldier_per_year()'s own docstring in sim/engine/society.py
for what was wired in, what was rejected, and why. This file checks that
crossing specifically - not military_logistics.py's own arithmetic, which
sim/tests/test_military_logistics.py already covers standalone.

Uses the full engine harness (sim/tests/harness.py), unlike test_military_
logistics.py's plain unittest style, because this crossing lives in
sim/engine/society.py and cannot be exercised without a real Sim.
"""
from .harness import *  # noqa: F401,F403

from sim.world import military_logistics as logistics


# --- the melee-tier floor: at zero military leverage, the reported burden is
# exactly military_logistics.py's own melee-only figure - no firearm, no
# ammunition, iron upkeep alone. Not re-derived here; read straight from the
# module so a change to IRON_KG_PER_EQUIPPED_SOLDIER or ANNUAL_EQUIPMENT_
# REPLACEMENT_FRACTION is still traceable through this test rather than past
# it.
_zero_lev = sim(civ="rome_100ad")
check("at zero military leverage, the founder is out entirely",
      _zero_lev.military_leverage() == 0.0, _zero_lev.military_leverage())
check("...so the reported per-soldier burden is military_logistics.py's own "
      "melee-only figure, exactly",
      _zero_lev.military_equipment_burden_kg_per_soldier_per_year()
      == logistics.annual_iron_and_ammunition_burden_kg_per_soldier(),
      (_zero_lev.military_equipment_burden_kg_per_soldier_per_year(),
       logistics.annual_iron_and_ammunition_burden_kg_per_soldier()))

# --- the rifle-tier ceiling: at full military leverage (every military-trait
# node done), the reported burden is exactly military_logistics.py's
# MODERN_SERVICE_RIFLE figure at society.py's own declared campaign tempo -
# again read from the module's functions, not a number typed into this test.
_full_lev = sim(civ="rome_100ad")
_all_military = [node_id for node_id in NODES if "military" in NODES[node_id].get("traits", ())]
_full_lev.done.update(_all_military)
_full_lev._done_changed()
check("crediting every military-trait node saturates leverage at 1.0",
      _full_lev.military_leverage() == 1.0, _full_lev.military_leverage())
_expected_rifle_kg = logistics.annual_iron_and_ammunition_burden_kg_per_soldier(
    firearm=logistics.MODERN_SERVICE_RIFLE,
    engagements_per_year=_full_lev.MILITARY_EQUIPMENT_ERA_CAMPAIGN_TEMPO_ENGAGEMENTS_PER_YEAR)
check("...so the reported per-soldier burden is military_logistics.py's own "
      "modern-rifle figure at society.py's declared campaign tempo, exactly",
      abs(_full_lev.military_equipment_burden_kg_per_soldier_per_year() - _expected_rifle_kg) < 1e-9,
      (_full_lev.military_equipment_burden_kg_per_soldier_per_year(), _expected_rifle_kg))

# --- monotone in between: THE STAKEHOLDER'S OWN SCENARIO ("give Rome guns")
# run through the numbers - a founder who has built out more of the military
# branch reports a heavier per-soldier physical claim, never a lighter one,
# and never one outside [melee, rifle].
_melee_kg = logistics.annual_iron_and_ammunition_burden_kg_per_soldier()
_partial = sim(civ="rome_100ad")
_partial.done.update(_all_military[:5])
_partial._done_changed()
_partial_burden = _partial.military_equipment_burden_kg_per_soldier_per_year()
check("partial military leverage reports a burden strictly between the "
      "melee floor and the rifle ceiling",
      _melee_kg < _partial_burden < _expected_rifle_kg,
      (_melee_kg, _partial_burden, _expected_rifle_kg))
check("more military nodes done means a heavier reported burden, never a "
      "lighter one - the crossing moves the SAME direction as leverage "
      "itself, always",
      _full_lev.military_equipment_burden_kg_per_soldier_per_year() > _partial_burden
      > _zero_lev.military_equipment_burden_kg_per_soldier_per_year())


# --- the crossing changes the NOTICE TEXT, not the MONEY. state_pressure_
# report()'s military_supply notice now carries this figure once eligible;
# the MILITARY_DEMAND_BASE_SHARE/LEVERAGE_SHARE arithmetic (money) is
# untouched by this crossing - see military_equipment_burden_kg_per_soldier_
# per_year()'s own "WHY NOT MONEY" section for why that boundary is kept.
def _grown(civ, employees=300.0, capital=3000000.0, eminence=20.0):
    """Same construction as test_scanners_and_scheduling.py's own _grown():
    a household large enough to be past the general state-notice line, built
    fresh here rather than imported so this file has no dependency on
    another topic's private helper."""
    grown_sim = sim(civ=civ, events=True)
    grown_sim.employees["artisan"] = employees
    grown_sim._resync_pools()
    grown_sim.capital = capital
    grown_sim.eminence = eminence
    grown_sim.update_protection()
    return grown_sim


_no_mil = _grown("rome_100ad")
check("a grown household with no military tech gets no military_supply "
      "notice at all",
      "military_supply" not in (_no_mil.state_pressure_report() or {}),
      _no_mil.state_pressure_report())

_one_mil = _grown("rome_100ad")
_one_mil.done.update(_all_military[:1])
_one_mil._done_changed()
_notice = _one_mil.state_pressure_report()
check("the first military-branch node is already enough to be asked for, "
      "and the notice now names a physical figure, not just a warning "
      "sentence",
      _one_mil.military_demand_eligible() and "military_supply" in _notice
      and "kg" in _notice["military_supply"],
      _notice.get("military_supply"))

_expected_one_kg = _one_mil.military_equipment_burden_kg_per_soldier_per_year()
check("the number IN the notice text is the same number the crossing's own "
      "method computes - not a second, independently-rounded copy",
      ("%.1f" % _expected_one_kg) in _notice["military_supply"],
      (_expected_one_kg, _notice["military_supply"]))

_before_take = (_one_mil.MILITARY_DEMAND_BASE_SHARE, _one_mil.MILITARY_DEMAND_LEVERAGE_SHARE)
_full_mil_grown = _grown("rome_100ad")
_full_mil_grown.done.update(_all_military)
_full_mil_grown._done_changed()
check("MILITARY_DEMAND_BASE_SHARE/LEVERAGE_SHARE (the money mechanic) are "
      "unchanged by this crossing regardless of leverage - only the notice "
      "TEXT moves, per this crossing's own 'WHY NOT MONEY' rejection",
      (_full_mil_grown.MILITARY_DEMAND_BASE_SHARE, _full_mil_grown.MILITARY_DEMAND_LEVERAGE_SHARE)
      == _before_take, ((_full_mil_grown.MILITARY_DEMAND_BASE_SHARE,
                          _full_mil_grown.MILITARY_DEMAND_LEVERAGE_SHARE), _before_take))


# --- dormant households are unaffected: state_pressure_report() still
# returns None (not a dict with only "what_helps") when nothing else is
# live and there is no military tech either - the crossing must not turn a
# quiet household noisy.
_dormant = sim(civ="rome_100ad")
check("a fresh, dormant household still gets no state-pressure report at "
      "all - this crossing does not add a floor sentence of its own",
      _dormant.state_pressure_report() is None, _dormant.state_pressure_report())


# --- round-trips within the build: military_leverage() is computed fresh
# from self.household.done every call (see its own docstring), and this
# crossing adds no new persisted field of its own - nothing here needs a
# SAVE_FIELDS entry, so nothing here can fail to round-trip. This check
# confirms that by construction: the reported burden survives a save/load
# because the DONE SET it is computed from already does.
_save_check = _grown("rome_100ad")
_save_check.done.update(_all_military[:3])
_save_check._done_changed()
_before_burden = _save_check.military_equipment_burden_kg_per_soldier_per_year()
_saved_done = set(_save_check.done)
_reloaded = _grown("rome_100ad")
_reloaded.done.update(_saved_done)
_reloaded._done_changed()
check("the reported burden is a pure function of the done set, so it "
      "round-trips through anything that round-trips `done` - no new "
      "SAVE_FIELDS entry needed for this crossing",
      _reloaded.military_equipment_burden_kg_per_soldier_per_year() == _before_burden,
      (_reloaded.military_equipment_burden_kg_per_soldier_per_year(), _before_burden))
