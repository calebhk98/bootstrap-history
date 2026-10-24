"""Complaint 491: `SimWorld.demonstrated()` reads every active actor's known nodes as well as the seats' builds, so imitation can
copy a node from any actor that holds it. Runs on a stand-in sim holding only what the answer reads."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.agents_port import SimWorld


def actor(identity, knowledge, exited_year=None):
    return SimpleNamespace(identity=lambda: identity, knowledge=set(knowledge), record=SimpleNamespace(exited_year=exited_year))


def world_of(actors, granted=("known",)):
    registry = SimpleNamespace(actors={a.identity(): a for a in actors})
    game = SimpleNamespace(nodes={"known": {}, "novel": {}, "other": {}}, actors=registry, seats={},
                           state=SimpleNamespace(projects=SimpleNamespace(granted=set(granted)), seats={}))
    return SimWorld(game)


check("a node nobody holds is not demonstrated", "novel" not in world_of([actor("state:1", [])]).demonstrated())
held = world_of([actor("state:1", ["novel"])])
check("a node a state holds is demonstrated", "novel" in held.demonstrated(), held.demonstrated())
check("...and is not a seat's invention", "novel" not in held.founder_inventions(), held.founder_inventions())
check("a node the society already knew is not counted as held", "known" not in world_of([actor("state:1", ["known"])]).demonstrated())
check("a node only an actor that has exited held is no longer demonstrated",
      "novel" not in world_of([actor("firm:1", ["novel"], exited_year=90)]).demonstrated())
check("a name that is not a node is ignored", "ghost" not in world_of([actor("state:1", ["ghost"])]).demonstrated())
