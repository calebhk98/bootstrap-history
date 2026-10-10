"""The baseline ensemble (Complaints/266): N no-intervention runs summarised into distributions by year, cached
to a file, and read by the divergence screen. The game runner is a stub here: a real game takes about an hour."""

QUICK_TOPIC = True

import json
import os
import tempfile
from types import SimpleNamespace

from .harness import check

from sim.engine import baseline_ensemble
from sim.ui.proto import screen_divergence


def stub_runner(civilisation_id, seed, years):
	"""A population that grows by `seed` a year, a technology each at fixed offsets; offset 0 is the opening."""
	rows = []
	for offset in range(years + 1):
		rows.append({"year": 100 + offset, "population": 1000.0 + seed * offset, "wage_index": 1.0,
					 "literacy_general": 0.1, "literacy_elite": 0.9, "territory_tiles": 10,
					 "technologies": sorted(["opening_tech"] + (["early_tech"] if offset >= 2 else [])
											+ (["late_tech"] if offset >= 3 * seed else []))})
	return rows


ensemble = baseline_ensemble.run_ensemble("fixture_civ", [1, 2, 3, 4, 5], 6, runner=stub_runner)
check("the ensemble records its runs and horizon", ensemble["runs"] == 5 and ensemble["years"] == 6
	and ensemble["start_year"] == 100 and ensemble["seeds"] == [1, 2, 3, 4, 5])
population = ensemble["metrics"]["population"]
check("each metric has a value per year from the opening", len(population["median"]) == 7)
check("the median at an offset is the middle run", population["median"][4] == 1000.0 + 3 * 4)
check("the lower and upper bands bracket it", population["p10"][4] <= population["median"][4] <= population["p90"][4]
	and population["p10"][4] < population["p90"][4])
check("technologies hold the offset each run first held them",
	ensemble["technologies"]["early_tech"] == [2, 2, 2, 2, 2] and ensemble["technologies"]["opening_tech"] == [0] * 5)
check("a technology some runs never reach lists only the runs that did",
	ensemble["technologies"]["late_tech"] == [3, 6])
try:
	baseline_ensemble.run_ensemble("fixture_civ", [], 6, runner=stub_runner)
	refused = False
except ValueError:
	refused = True
check("an empty seed list is refused", refused)

# the cache file
with tempfile.TemporaryDirectory() as directory:
	check("no cache reads as absent", baseline_ensemble.read_cache("fixture_civ", directory) is None)
	path = baseline_ensemble.write_cache(ensemble, directory)
	check("the cache is one json file per civilisation", os.path.basename(path) == "fixture_civ.json")
	check("it reads back as written", baseline_ensemble.read_cache("fixture_civ", directory) == json.loads(json.dumps(ensemble)))
	with open(path, "w", encoding="utf-8") as handle:
		handle.write("{not json")
	check("a damaged cache reads as absent", baseline_ensemble.read_cache("fixture_civ", directory) is None)
	baseline_ensemble.write_cache(ensemble, directory)

	nodes = {"early_tech": {"name": "Early tech"}, "late_tech": {"name": "Late tech"},
			 "never_tech": {"name": "Never tech"}, "opening_tech": {"name": "Opening tech"}}

	def fake_sim(year, built):
		return SimpleNamespace(
			civ={"id": "fixture_civ", "literacy_general": 0.1, "literacy_elite": 0.9},
			cfg={"start_year": 100}, year=year, wage_index=1.0, population=SimpleNamespace(total=1005.0),
			world_map=None, nodes=nodes, done=set(built), granted=set(), tiles_now=10)

	screen_divergence.tile_count = lambda sim: sim.tiles_now
	section = screen_divergence.baseline_section(fake_sim(104, ["early_tech", "late_tech", "never_tech"]), directory)
	check("the screen reads the cache", section["available"] is True and section["runs"] == 5)
	check("it places the population against the baseline band",
		section["compared"]["population"]["position"] in ("below", "within", "above"))
	rows = {row["id"]: row for row in section["technologies"]}
	check("a technology all runs held by now is one the society would hold",
		rows["early_tech"]["would_not_yet_hold"] is False and rows["early_tech"]["runs_holding"] == 5)
	check("a technology few runs held by now is one it would not yet hold",
		rows["late_tech"]["would_not_yet_hold"] is True and rows["late_tech"]["runs_holding"] == 1)
	check("a technology no run held within the horizon says so",
		rows["never_tech"]["runs_holding"] == 0 and rows["never_tech"]["would_not_yet_hold"] is True
		and rows["never_tech"]["median_first_year"] is None)
	check("a held technology names the year the baseline median first held it", rows["early_tech"]["median_first_year"] == 102)
	beyond = screen_divergence.baseline_section(fake_sim(500, ["late_tech"]), directory)
	check("past the horizon the last year stands in, and the section says so", beyond["compared_at_offset"] == 6
		and beyond["beyond_horizon"] is True)

	absent = screen_divergence.baseline_section(fake_sim(104, []), os.path.join(directory, "nowhere"))
	check("without a cache the screen says it needs generating", absent["available"] is False)
	check("and gives the command to generate it", "baseline-ensemble" in absent["how_to_generate"]
		and "fixture_civ" in absent["how_to_generate"])

	mismatched = dict(ensemble, start_year=1500)
	baseline_ensemble.write_cache(mismatched, directory)
	other = screen_divergence.baseline_section(fake_sim(104, []), directory)
	check("a cache built for another start year is not used", other["available"] is False and "start year" in other["reason"])

# the subcommand, with the stub in place of a game
from sim.ui.cli_baseline import cmd_baseline_ensemble

with tempfile.TemporaryDirectory() as directory:
	arguments = SimpleNamespace(civ="fixture_civ", seeds=3, years=4, jobs=1, directory=directory)
	check("the subcommand plays the seeds and succeeds", cmd_baseline_ensemble(arguments, runner=stub_runner) == 0)
	stored = baseline_ensemble.read_cache("fixture_civ", directory)
	check("and leaves the cache the screen reads", stored is not None and stored["runs"] == 3 and stored["years"] == 4
		and stored["seeds"] == [1, 2, 3])
