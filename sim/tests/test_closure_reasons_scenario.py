"""Scenario for closure reasons in a whole game: a concern shut for want of staff is named, restored, kept
through a save and load, and a manual mothball afterwards inherits nothing from it. The rules are in test_closure_reasons."""
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


def restore_price(test_sim):
	before = test_sim.capital
	ok, message = test_sim.restore_work(NODE_ID)
	return ok, message, before - test_sim.capital


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
ok_first, _, _ = restore_price(game)
cleared = game.closure_of(NODE_ID) is None and NODE_ID not in game.shut_for_staff
game.state.scenario.year += 30
game.mothball_work(NODE_ID)
manual_record = game.closure_of(NODE_ID)
ok_again, _, _ = restore_price(game)

opened_game = staffed_sim()
staff_close(opened_game)
ok_open, _ = opened_game.open_venture(NODE_ID)

check("scenario: a staffing closure is named, survives a save and load, restores and clears, and a later manual one is its own",
      closed == [NODE_ID] and named == "staff" and survives and ok_first and cleared
      and manual_record == {"reason": "manual", "year": game.year} and ok_again
      and ok_open and opened_game.closure_of(NODE_ID) is None,
      dict(closed=closed, named=named, survives=survives, cleared=cleared, manual_record=manual_record,
           opened=ok_open))
