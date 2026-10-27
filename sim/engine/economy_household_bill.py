"""What the seat's household pays for its needs: the economy's need floors at the prices on its tile."""
from sim.constants import declare


class HouseholdBillMixin:

    HOUSEHOLD_DEPENDANT_PEOPLE = declare(
        "HOUSEHOLD_DEPENDANT_PEOPLE", 1.0, kind="initial_condition",
        unit="people besides the founder and the household's freedmen and slaves",
        source=None, confidence="D",
        why="How many kin and retainers a founder arrives keeping; each is a person with the full need floors. "
            "A real figure would come from the civilisation's household structure.")

    def household_need_floors_per_person(self):
        """What one person's floor of each need costs a year on the seat's tile: the economy's prices and the
        tile's climate floors (the need basket). While the economy opens, the same basket on the goods market."""
        floors = self.economy.agent_need_floor_costs_at()
        if floors:
            return dict(floors)
        return self.view("actor_world")().need_floor_costs_per_person_year()

    def household_bill_per_person(self):
        """One person's yearly bill for every need's floor: the figure the founder and an economy household pay."""
        return sum(self.household_need_floors_per_person().values())

    def household_dependant_people(self):
        """People the household keeps besides the founder: each a person with needs of their own."""
        staff = self.view("staff")()
        return self.HOUSEHOLD_DEPENDANT_PEOPLE + staff["freedmen"] + staff["slaves"]
