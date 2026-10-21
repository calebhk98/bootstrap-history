"""The share of the founder's military work the state holds (Complaint 640): called on lists built here, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine.adoption_share import held_share

ids = ["pike", "cannon", "musket", "mortar"]
check("the founder's military work does not reach a state that holds none of it", held_share(ids, set()) == 0.0)
check("holding some of it is that fraction of it", held_share(ids, {"cannon"}) == 0.25)
check("holding more of it is a larger share", held_share(ids, {"cannon", "pike"}) > held_share(ids, {"cannon"}))
check("holding all of it is full adoption", held_share(ids, set(ids)) == 1.0)
check("what the state holds that the founder did not make adds nothing", held_share(ids, {"catapult"}) == 0.0)
check("holding the founder's work and more is still full adoption, not more", held_share(ids, set(ids) | {"catapult"}) == 1.0)
check("with no military work built the share is nothing, not a division by zero", held_share([], {"cannon"}) == 0.0)
check("a one-shot iterable of techniques is counted once", held_share(iter(ids), {"pike", "cannon"}) == 0.5)
