"""Complaint 602, home country: the founder's civilisation's state cannot keep an army larger than its people can spare.
Complaint 640: the view's hands and the army check are called on a stand-in game that holds only what they read."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents import headcount
from sim.agents.records import ActorRecord
from sim.actors.world_budget import BudgetView

from .world_stand_in import fake_needs

WORKING_AGE = 1.0e6


class HomeView(BudgetView):
    """The budget questions over a stand-in game: its working age, farm hours, last nutrition and the state's granary."""

    def __init__(self, farm_hours=None, nutrition=None, granary=0.0):
        record = ActorRecord(kind="government")
        record.stores["wheat_kg"] = granary
        flows = None if nutrition is None else SimpleNamespace(nutrition_ratio=nutrition)
        self.needs = fake_needs(
            working_age=WORKING_AGE, population_total=4.0 * WORKING_AGE, farm_holdings={"hours_needed": farm_hours},
            nutrition_ratio_last_year=lambda: None if flows is None else flows.nutrition_ratio)
        self._record = record

    def government(self):
        return SimpleNamespace(record=self._record)


hands = HomeView().state_hands()
check("the home country's hands are its working age", hands.working_age == WORKING_AGE, hands)
check("with no farming allocation yet and no famine, no hands are held back", hands.farm_hands == 0.0 and hands.food_ratio == 1.0, hands)

view = HomeView()
record = ActorRecord(kind="government")
soldiers, wanted = headcount.checked_army(view, record, 10.0 * WORKING_AGE, 10.0 * WORKING_AGE, 0.0)
booked = record.headcount["army"]
check("an army many times the working age is cut to the people free to serve, with the cause",
      soldiers <= WORKING_AGE and wanted <= WORKING_AGE and booked["shortfall"] > 0.0 and booked["cause"] == headcount.WORKING_AGE,
      (soldiers, wanted, booked))

record = ActorRecord(kind="government")
soldiers, wanted = headcount.checked_army(view, record, 0.001 * WORKING_AGE, 0.001 * WORKING_AGE, 0.0)
check("a feasible home army is untouched", record.headcount["army"]["shortfall"] == 0.0 and soldiers == wanted == 0.001 * WORKING_AGE,
      record.headcount)

record = ActorRecord(kind="government")
others = 0.4 * WORKING_AGE
soldiers, _wanted = headcount.checked_army(view, record, 0.9 * WORKING_AGE, 0.9 * WORKING_AGE, others)
check("the state's other people are taken from the same working age", soldiers <= WORKING_AGE - others, soldiers)
