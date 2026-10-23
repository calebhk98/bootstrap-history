"""SCENARIO: in a Rome game the military_supply notice of the state-pressure report carries the per-soldier burden the
crossing computes, a state that has paid for its army asks nothing more, and a dormant household gets no report.
The burden and leverage rules are in `test_military_logistics_wiring`.
"""
from .harness import *  # noqa: F401,F403



_all_military = [node_id for node_id in NODES if "military" in NODES[node_id].get("traits", ())]


# --- the crossing changes the NOTICE TEXT, not the MONEY. state_pressure_
# report()'s military_supply notice now carries this figure once eligible;
# money the state asks of a household is its unfunded army need, priced by the
# budget (actors/budget.py), not by this crossing's own "WHY NOT MONEY" figure.
def _grown(civ, employees=300.0, capital=3000000.0, eminence=20.0):
    """Same construction as test_scanners_and_scheduling.py's own _grown():
    a household large enough to be past the general state-notice line, built
    fresh here rather than imported so this file has no dependency on
    another topic's private helper."""
    grown_sim = unopened_sim(civ=civ, events=True)
    grown_sim.employees["artisan"] = employees
    grown_sim.labour._resync_pools()
    grown_sim.capital = capital
    grown_sim.eminence = eminence
    grown_sim.update_protection()
    return state_seeking(grown_sim)


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
      and ("kilogram" in _notice["military_supply"] or "kg" in _notice["military_supply"]),
      _notice.get("military_supply"))

_expected_one_kg = _one_mil.military_equipment_burden_kg_per_soldier_per_year()
check("the number IN the notice text is the same number the crossing's own "
      "method computes - not a second, independently-rounded copy",
      ("%.1f" % _expected_one_kg) in _notice["military_supply"],
      (_expected_one_kg, _notice["military_supply"]))

_full_mil_grown = _grown("rome_100ad")
_full_mil_grown.done.update(_all_military)
_full_mil_grown._done_changed()
check("the crossing's kilograms never become money on their own: a state that has "
      "paid for its army asks even a full-leverage household for nothing - what it "
      "asks is its unfunded army need (actors/budget.py)",
      _full_mil_grown.state_military_ask(1.0e6, _full_mil_grown.household_scale()) == 0.0,
      _full_mil_grown.state_military_ask(1.0e6, _full_mil_grown.household_scale()))


# --- dormant households are unaffected: state_pressure_report() still
# returns None (not a dict with only "what_helps") when nothing else is
# live and there is no military tech either - the crossing must not turn a
# quiet household noisy.
_dormant = unopened_sim(civ="rome_100ad")
check("a fresh, dormant household still gets no state-pressure report at "
      "all - this crossing does not add a floor sentence of its own",
      _dormant.state_pressure_report() is None, _dormant.state_pressure_report())
