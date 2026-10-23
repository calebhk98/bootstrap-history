"""SMOKE (Complaint 153): a posted bounty round-trips through a save file from one unopened game to another as an active
bountied project. What a bounty costs the poster, and the credit freeze, are rules in test_bounty_save_and_credit_freeze."""
from .harness import *  # noqa: F401,F403
from sim.engine.saveload import save_state, load_state

source = unopened_sim(capital=1e9)
target = unopened_sim(capital=1.0)
bounty_id = next(node_id for node_id in ORDER
                 if node_id not in source.done and NODES[node_id]["ph"] > 100
                 and NODES[node_id]["lab"] and source.bounty_eligible(node_id))
posted = source.post_bounty(bounty_id)
save_path = os.path.join(tempfile.mkdtemp(), "save.json")
save_state(source, save_path)
try:
    load_state(target, save_path)
    reload_error = None
except ValueError as error:
    reload_error = str(error)
check("scenario: a posted bounty loads back from a save as an active bountied project",
      posted and reload_error is None and bounty_id in target.active and bounty_id in target.bountied,
      (posted, reload_error))
