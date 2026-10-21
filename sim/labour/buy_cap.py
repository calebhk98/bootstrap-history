"""The household cap on buying people: the same room `hire` enforces."""
from sim.refusal import Refusal


def over_room_refusal(people, room, advice):
    """The refusal text when `people` exceed the `room` the household can feed, house and oversee (None when they fit).
    A person you own needs feeding and housing exactly as much as one you pay."""
    if people <= room:
        return None
    return Refusal("household_room",
                   "you can supervise, house and teach %.2f more people, not %g - and a person you own needs feeding and "
                   "housing exactly as much as one you pay. %s" % (max(0.0, room), people, advice()),
                   room=max(0.0, room), people=people)
