"""SMOKE: a screen's question about a project's material throttle does not change the game: asking before a step leaves the
year that follows as if nobody had asked (the multi-year step's warning asks, the single step's does not). The restoring is
That the quote
changes nothing is called on the module in test_peek_resource_throttle."""
from .harness import *  # noqa: F401,F403

from sim.engine.saveload import save_state, read_save_text
from sim.materials.api import ApplyThrottle
import json
import tempfile


def dump(game):
	with tempfile.TemporaryDirectory() as folder:
		save_state(game, folder + "/game.json")
		return json.loads(read_save_text(folder + "/game.json"))


def made():
	game = unopened_sim(events=True, surveyed=())
	for node_id in ("tx2_bleaching_sun", "tx2_count_standard", "clock_mechanical_escapement"):
		game.start_project(node_id)
	return game


asked, untouched = made(), made()
node_id = sorted(asked.active)[0]
factor, binding = asked.peek_project_resource_throttle(node_id)
def differences(a, b, path=""):
	if isinstance(a, dict) and isinstance(b, dict):
		return [d for key in sorted(set(a) | set(b)) for d in
		        (differences(a[key], b[key], path + "/" + str(key)) if key in a and key in b else [path + "/" + str(key)])]
	if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
		return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, path + "[%d]" % i)]
	return [] if a == b else [path]


left = differences(dump(asked), dump(untouched))
check("asking leaves the stock, the year's draws and the holdings as they were", not left, left[:10])
# a step would work the throttle out (and keep what it banks): the same figures, asked of the untouched twin
check("the peek answers what the project's throttle is", factor == untouched.send(ApplyThrottle(node_id)), factor)
check("...and which pool binds it", binding == untouched.view("material_binding")(), binding)
