"""auto_hire_buys_room: a staffing closure with no room left reopens once the household can pay for room (Complaint 525)."""
from .harness import *  # noqa: F401,F403

_node_id = "tex_rope_walk"


def _closed_for_want_of_staff(capital):
    """A household whose room is full of idle farmhands while the concern it runs lost its crew."""
    game = sim(civ="norse_900ad", capital=capital)
    game.policy["auto_hire"] = True
    game.done.update(NODES[_node_id]["pre"])
    game.done.add(_node_id)
    game._done_changed()
    scholars, artisans = game.venture_hands(_node_id)
    game.employees["artisan"] = game.employees.get("artisan", 0.0) + artisans + 1
    game.employees["scholar"] = game.employees.get("scholar", 0.0) + scholars + 1
    game.labour._resync_pools()
    game.state.household.worker_housing_places = 20.0
    opened = game.open_venture(_node_id)
    assert opened[0], opened
    game.state.household.worker_housing_places = 0.0
    game.employees["artisan"] = 0.0
    game.employees["scholar"] = 0.0
    game.labour._resync_pools()
    game.employees["farmhand"] = game.employees.get("farmhand", 0.0) + max(0, int(game.labour.household_room()))
    game.labour._resync_pools()
    return game


_rich = _closed_for_want_of_staff(60000.0)
_room_before = _rich.labour.household_room()
for _year in range(3):
    _rich.step()
check("set-up: the household's room was used up before the year turned", _room_before < 1.0, _room_before)
check("a rich household with no room left buys housing and hires the staff attrition took, as a player's "
      "'buy housing' then 'hire' would",
      _rich.employees.get("artisan", 0.0) >= 1.0,
      (dict(_rich.employees), _rich.state.household.worker_housing_places))
check("...and the room came from worker housing, bought at the price a player's quote shows",
      (_rich.state.household.worker_housing_places or 0.0) > 0.0,
      _rich.state.household.worker_housing_places)

_poor = _closed_for_want_of_staff(60000.0)
_poor.capital = 0.0
for _year in range(3):
    _poor.step()
    _poor.capital = 0.0
check("a household that cannot pay for room buys none",
      (_poor.state.household.worker_housing_places or 0.0) == 0.0,
      _poor.state.household.worker_housing_places)

# The policy's own call, with no attrition draw in the way.
_direct = _closed_for_want_of_staff(60000.0)
_direct.employees["farmhand"] = _direct.employees.get("farmhand", 0.0) + max(0, int(_direct.labour.household_room()))
_direct.labour._resync_pools()
_room_direct = _direct.labour.household_room()
_plain_hired, _plain_reply = _direct.labour.hire("artisan", 1)
check("set-up: a plain hire is refused for want of room",
      not _plain_hired and _plain_reply.cause == "household_room", (_room_direct, _plain_reply))
_bought_hired, _bought_reply = _direct.labour.hire_buying_room("artisan", 1)
check("hire_buying_room buys the room and then hires", _bought_hired
      and (_direct.state.household.worker_housing_places or 0.0) >= 1.0, _bought_reply)

_broke = _closed_for_want_of_staff(60000.0)
_broke.employees["farmhand"] = _broke.employees.get("farmhand", 0.0) + max(0, int(_broke.labour.household_room()))
_broke.labour._resync_pools()
_broke.capital = 0.0
_broke_hired, _broke_reply = _broke.labour.hire_buying_room("artisan", 1)
check("hire_buying_room leaves the refusal alone when the purse cannot pay for the room",
      not _broke_hired and (_broke.state.household.worker_housing_places or 0.0) == 0.0, _broke_reply)
