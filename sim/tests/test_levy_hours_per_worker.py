"""Complaint 621: the hours the state called up for its works and army reach the economy as the working time each
working-age person no longer offers. The rule is called on a stub game with a government that took hours."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents.api import ActorRecord
from sim.agents.government import Government
from sim.markets import port_levy


def stub_game(hours_by_destination, working_age, has_government=True):
    """A game whose home state has taken these hours this year, among this many working-age people."""
    government = Government("government:home", ActorRecord(kind="government"))
    government.record.corvee_hours = dict(hours_by_destination)
    return SimpleNamespace(actors=SimpleNamespace(government_of=lambda country: government if has_government else None),
                           population=SimpleNamespace(working_age=working_age))


check("hours taken for works and army are spread over the working age",
      port_levy.levy_hours_per_worker(stub_game({"works": 600.0, "army": 400.0}, 100.0)) == 10.0)
check("a state that took no hours takes none from each worker",
      port_levy.levy_hours_per_worker(stub_game({}, 100.0)) == 0.0)
check("a country with no working-age people loses no hours per worker",
      port_levy.levy_hours_per_worker(stub_game({"works": 600.0}, 0.0)) == 0.0)
check("before a state exists nothing is taken",
      port_levy.levy_hours_per_worker(stub_game({"works": 600.0}, 100.0, has_government=False)) == 0.0)
