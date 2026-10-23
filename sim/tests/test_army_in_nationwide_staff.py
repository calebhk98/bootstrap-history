"""Complaint 314: the nationwide staff count that labour reads carries the government's whole army in place of the
slice of it the founder's pool lost, and no one else's. The rule is `ActorsMixin.actor_staff_nationwide`, called on a
stand-in game."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents.api import SOLDIER_TRADE
from sim.engine.society_actors import ActorsMixin


def stand_in(army, soldiers_in_workforce, pool_slice, civilisation_id="testland", has_government=True):
    records = {"government:" + civilisation_id: SimpleNamespace(army=army, workforce={SOLDIER_TRADE: soldiers_in_workforce})} \
        if has_government else {"firm:x": SimpleNamespace(army=0.0, workforce={})}
    return SimpleNamespace(state=SimpleNamespace(actors=SimpleNamespace(records=records)), civ={"id": civilisation_id},
                           actor_staff_fte=lambda trade: pool_slice.get(trade, 0.0))


def nationwide(game, trade):
    return ActorsMixin.actor_staff_nationwide(game, trade)


game = stand_in(army=120.0, soldiers_in_workforce=30.0, pool_slice={SOLDIER_TRADE: 30.0, "smith": 7.0})
check("the soldier trade reads the government's whole army", nationwide(game, SOLDIER_TRADE) == 120.0, nationwide(game, SOLDIER_TRADE))
check("another trade reads only the slice the actors drew from the pool", nationwide(game, "smith") == 7.0)
check("without a government record the soldier trade reads the pool's slice",
      nationwide(stand_in(0.0, 0.0, {SOLDIER_TRADE: 5.0}, has_government=False), SOLDIER_TRADE) == 5.0)
check("an army smaller than the workforce slice never makes the count negative",
      nationwide(stand_in(army=0.0, soldiers_in_workforce=50.0, pool_slice={SOLDIER_TRADE: 10.0}), SOLDIER_TRADE) == 0.0)
check("before any actor exists the count is zero",
      nationwide(SimpleNamespace(state=SimpleNamespace(actors=None)), SOLDIER_TRADE) == 0.0)
