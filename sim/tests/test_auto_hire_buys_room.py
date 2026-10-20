"""auto_hire_buys_room: a staffing closure with no room left reopens once the household can pay for room (Complaint 525).
The room purchase is a rule on built inputs; two named scenarios run the policy on a game."""
from sim.labour.labour_staff_controls import housing_places_to_buy

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


check("room that already holds the new people buys no housing", housing_places_to_buy(3, 5.0, 100.0, 10.0, 1.0e9) == 0)
check("housing is bought for the people the room is short of",
      housing_places_to_buy(3, 1.0, 100.0, 10.0, 1.0e9) == 2)
check("negative room counts as none", housing_places_to_buy(2, -4.0, 100.0, 10.0, 1.0e9) == 2)
check("housing and the hiring outlay together within the budget are bought",
      housing_places_to_buy(1, 0.0, 100.0, 50.0, 150.0) == 1)
check("a purse that cannot pay for housing and the hire together buys no room",
      housing_places_to_buy(1, 0.0, 100.0, 50.0, 149.0) == 0)

_rich = _closed_for_want_of_staff(600000.0)
_room_before = _rich.labour.household_room()
_reopened_years = 0
for _year in range(4):
    _rich.step()
    _reopened_years += _node_id in _rich.operating
check("scenario: a rich household with no room left buys worker housing and hires, so the concern attrition shut reopens",
      _room_before < 1.0 and _reopened_years >= 1 and (_rich.state.household.worker_housing_places or 0.0) > 0.0,
      (_room_before, _reopened_years, _rich.state.household.worker_housing_places, dict(_rich.employees)))

_poor = _closed_for_want_of_staff(60000.0)
_poor.capital = 0.0
for _year in range(4):
    _poor.step()
    _poor.capital = 0.0
_skips = [row for row in _poor.state.household.automation_audit
          if row["policy"] == "auto_hire" and row["action"] == "skipped"]
check("scenario: a household that cannot pay stays shut, buys no room, and the audit says why the hire was refused",
      _node_id not in _poor.operating
      and (_poor.state.household.worker_housing_places or 0.0) == 0.0
      and bool(_skips) and "shut for want of staff" in _skips[-1]["reason"],
      (_node_id in _poor.operating, _poor.state.household.worker_housing_places, _skips[-1:] if _skips else "no skip row"))
