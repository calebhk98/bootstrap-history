"""SCENARIO (Complaint 640): for Complaint 621 in a whole game: a civilisation that declares a corvee and a conscription takes the hours from its
working-age people, staffs its works with them unpaid, fills its army with them, and hands the lost hours to the economy
as the working time its households no longer offer. The rules are in test_state_corvee and test_levy_hours_per_worker;
the worth of the corvee to the state's revenue and the cost of a conscript army are held by test_state_corvee."""
from .harness import *  # noqa: F401,F403

from sim.agents import revenue_labour
from sim.engine import economy_port_levy
from sim.engine.agents_port import SimWorld

DAYS = 20.0
CONSCRIPT_DAYS = 5.0


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def with_dues(*forms):
    game = sim()
    record = game.state_treasury().record   # the state's own forms, copied from the civilisation's file at setup
    record.revenue_forms = list(record.revenue_forms) + list(forms)
    return game


plain = sim()
one_year(plain)
check("a civilisation that declares no labour due takes no hours from its people",
      economy_port_levy.levy_hours_per_worker(plain) == 0.0 and sum(plain.state_treasury().record.corvee_hours.values()) == 0.0,
      plain.state_treasury().record.corvee_hours)

game = with_dues({"form": "corvee", "basis": "labour_days", "rate": DAYS, "per": "working_age_person", "to": "works"})
treasury = game.state_treasury()
one_year(game)
working_age = game.population.working_age
expected_hours = DAYS * revenue_labour.HOURS_PER_WORKING_DAY * working_age
check("the days owed are taken as hours from the working-age people",
      abs(treasury.record.corvee_hours["works"] - expected_hours) < 1e-6 * expected_hours,
      (treasury.record.corvee_hours, expected_hours))
check("the hours reach the economy as working time each household no longer offers",
      abs(economy_port_levy.levy_hours_per_worker(game) - DAYS * revenue_labour.HOURS_PER_WORKING_DAY) < 1e-6,
      economy_port_levy.levy_hours_per_worker(game))

soldiers = with_dues({"form": "conscription", "basis": "labour_days", "rate": CONSCRIPT_DAYS, "per": "working_age_person",
                      "to": "army"})
treasury = soldiers.state_treasury()
one_year(soldiers)
booked = treasury.record.headcount["army"]
conscripts = treasury.record.corvee_hours["army"] / SimWorld(soldiers).hours_per_person_year
check("conscripts are part of the army the country's people can spare",
      conscripts > 0.0 and booked["granted"] >= conscripts - 1e-6 and treasury.record.army >= conscripts - 1e-6,
      (conscripts, booked, treasury.record.army))
