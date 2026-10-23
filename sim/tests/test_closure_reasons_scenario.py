"""SMOKE: a concern shut for want of staff in a game is named and kept through a save and load. The rules (the record,
restoring, the manual closure inheriting nothing) are in test_closure_reasons."""
from .harness import *  # noqa: F401,F403

NODE_ID = concern_needing_craftsmen_to_supervise()


def staffed_sim():
	# A running concern that needs a craftsman to supervise it.
	test_sim = unopened_sim(capital=1_000_000.0)
	test_sim.done.update(NODES[NODE_ID]["pre"])
	test_sim.done.add(NODE_ID)
	test_sim._done_changed()
	test_sim.employees["artisan"] = 6.0
	test_sim.labour._resync_pools()
	opened, reason = test_sim.open_venture(NODE_ID)
	check("set-up: the fixture's founder can afford to open the concern", opened, reason)
	return test_sim


def staff_close(test_sim):
	test_sim.employees["artisan"] = 0.0
	test_sim.labour._resync_pools()
	closed = test_sim.close_unstaffed_ventures(test_sim.year)
	test_sim.employees["artisan"] = 6.0
	test_sim.labour._resync_pools()
	return closed


game = staffed_sim()
closed = staff_close(game)
named = (game.closure_of(NODE_ID) or {}).get("reason")
with tempfile.TemporaryDirectory() as save_folder:
	save_path = os.path.join(save_folder, "closure_reasons_save.json")
	S.save_state(game, save_path)
	loaded = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=S.load_civ("rome_100ad"))
	loaded.goal, loaded.done_year = GOAL, {}
	S.load_state(loaded, save_path)
survives = loaded.closure_of(NODE_ID) == game.closure_of(NODE_ID)

check("scenario: a staffing closure is named and survives a save and load",
      closed == [NODE_ID] and named == "staff" and survives, dict(closed=closed, named=named, survives=survives))
