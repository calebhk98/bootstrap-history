"""The map, education, demography and divergence screens (Complaints 239, 94, 266), one rule at a time on stand-ins that write out what
the rule reads: which tiles and neighbours the map lists, how the education screen splits the schooling gain and names what limits
literacy, which status a dated event has and whether fog hides its name, and the figures the demography screen takes from a year's flows.
The registration and the aliases are test_missing_screens."""
from types import SimpleNamespace
from unittest import mock

from sim.diffusion import constants as diffusion_constants
from sim.diffusion.module import Diffusion
from sim.tests import literacy_stand_in, module_harness
from sim.ui.proto import screen_demography, screen_divergence, screen_education, screen_map

from .harness import *  # noqa: F401,F403
from sim.tests.ui_stand_in import Game
from sim.tests import store_stand_in

QUICK_TOPIC = True

# --- map: held tiles by people, the base marked, the rest carrying the days to reach them, neighbours not held.
TILE_NAMES = Game(
    tile_name=lambda tile_id: "name_" + tile_id, region_name=lambda tile_id: "region", terrain=lambda tile_id: "plain",
    region_names=lambda: {},
    neighbours=lambda tile_id: {"t1": ["t2", "t9"], "t2": ["t1", "t8"], "t3": ["t9"]}[tile_id])
held = {"t1": 50.4, "t2": 300.0, "t3": 10.0}
labour = Game(settlement_tiles=lambda: held, base_tile=lambda: "t1", home_town_population_estimate=lambda: 77.6,
                         relocation_quote=lambda tile_id: (3.4, 1.0) if tile_id != "t3" else None)
map_game = Game(labour=labour, tile_places=lambda tile: [], regions_of=lambda tiles: ["r"],
                tiles_listed_by=lambda civilisation: set(held), civ={"short_name": "Testland"}, population=Game(total=1234.6))
with mock.patch.object(screen_map, "tile_names", TILE_NAMES), \
        mock.patch.object(screen_map, "_deposits_by_tile", lambda: {"t2": [{"name": "seam"}]}):
    report = screen_map.map_report(map_game, full=True)
    short = screen_map.map_report(map_game)
check("the held tiles are listed by people, most first, each with its people rounded",
      [(row["tile"], row["people"]) for row in report["tiles"]] == [("t2", 300), ("t1", 50), ("t3", 10)], report["tiles"])
check("the base row is marked and carries no days; another tile carries the days from the base; one with no quote carries none",
      report["tiles"][1].get("is_your_base") is True and "days_from_your_base" not in report["tiles"][1]
      and report["tiles"][0]["days_from_your_base"] == 3 and "days_from_your_base" not in report["tiles"][2], report["tiles"])
check("a tile lists the deposits on it", report["tiles"][0]["deposits"] == [{"name": "seam"}] and report["tiles"][1]["deposits"] == [])
check("next door lists the neighbours of held tiles that are not held, each beside the held tile that first named it",
      [(row["tile"], row["beside"]) for row in report["next_door"]] == [("t8", "name_t2"), ("t9", "name_t1")], report["next_door"])
check("the base is stated with its people and the town's estimate",
      report["you_are_based_at"]["tile"] == "t1" and report["you_are_based_at"]["people"] == 50
      and report["you_are_based_at"]["town_people"] == 78, report["you_are_based_at"])
check("the report counts the tiles held and the neighbours", report["tiles_held"] == 3 and report["next_door_total"] == 2, report)
map_game.stores = store_stand_in.base_book()
with mock.patch.object(screen_map, "map_report", side_effect=lambda game, full=False: {"tiles": [], "next_door": []}):
    refused = screen_map.map_screen(map_game, {"layer": "no_such_store"})
check("a layer that names no tile store is refused with cause unknown_layer", refused["ok"] is False and refused["cause"] == "unknown_layer", refused)
many = {"t%d" % number: float(number) for number in range(30)}
many_game = Game(labour=Game(settlement_tiles=lambda: many, base_tile=lambda: "t0", home_town_population_estimate=lambda: 1.0,
                                                   relocation_quote=lambda tile_id: (1.0, 1.0)),
                            tile_places=lambda tile: [], regions_of=lambda tiles: [], tiles_listed_by=lambda civilisation: set(),
                            civ={}, population=Game(total=1.0))
with mock.patch.object(screen_map, "tile_names", Game(**{**TILE_NAMES.__dict__, "neighbours": lambda tile_id: []})):
    default_view = screen_map.map_report(many_game)
    full_view = screen_map.map_report(many_game, full=True)
check("the map shows the default number of tiles unless full is asked, and counts them all",
      len(default_view["tiles"]) == screen_map.TILES_SHOWN_BY_DEFAULT and len(full_view["tiles"]) == 30 and default_view["tiles_held"] == 30)

# --- education
check("a share of a ceiling is None when the ceiling is nothing", screen_education._fraction_of(0.3, 0.0) is None)
check("a share of a ceiling is the value over the ceiling", screen_education._fraction_of(0.3, 0.6) == 0.5)
schools = [{"flow_added": 0.3}, {"flow_added": 0.1}, {"flow_added": 0.0}]
enrolling = Game(literacy_next_year=lambda: {"literacy_general": 0.30}, literacy=lambda field: 0.20, population=Game(total=1000.0))
screen_education._enrolment(enrolling, schools)
check("the society's gain is split between the running schools by their share of the flow, and a school that adds nothing gets nothing",
      [row["share_of_schooling_flow"] for row in schools] == [0.75, 0.25, 0.0]
      and [row["people_made_literate_next_year"] for row in schools] == [75.0, 25.0, 0.0], schools)
check("with no school running the limit is said to be no school",
      screen_education._limited_by(Game(effective_schooling_flow=lambda: 0.0), 0.5) == "no school running")
running = Game(effective_schooling_flow=lambda: 0.2)
check("a society at its ceiling is limited by the ceiling", screen_education._limited_by(running, 0.99) == "the ceiling (farm share and unschooled share)")
check("a society below its ceiling with a school is limited by the flow", screen_education._limited_by(running, 0.5) == "the schooling flow")
check("a ceiling of nothing does not read as at the ceiling", screen_education._limited_by(running, None) == "the schooling flow")
school_tree = {"heard": {"name": "Heard"}, "hidden": {"name": "Hidden"}}
fogged = Game(fog=True, is_visible=lambda node_id: node_id == "heard", nodes=school_tree, has=lambda node_id: False,
                         running=lambda node_id: False, effect_holds=lambda node_id, spec: False, institution_units=lambda node_id: 0,
                         effect_value=lambda node_id, spec: 0.0)
with mock.patch.object(screen_education.ui_port, "effect_terms", lambda game, name: [("heard", {}), ("hidden", {})]):
    shown_fogged = screen_education._schools(fogged)
    shown_clear = screen_education._schools(Game(**{**fogged.__dict__, "fog": False}))
check("under fog the schools listed are only those the player has heard of",
      [row["id"] for row in shown_fogged] == ["heard"] and [row["id"] for row in shown_clear] == ["heard", "hidden"])


class _Shares:
    """The literacy strata as the schooling step reads them: copy, get and school toward a ceiling."""

    def __init__(self, shares):
        self.shares = dict(shares)

    def copy(self):
        return _Shares(self.shares)

    def get(self, field):
        return self.shares[field]

    def school(self, field, step, ceiling):
        self.shares[field] += step * (ceiling - self.shares[field])


def _schooling_game(flow=1.0):
    """The diffusion module whose schools give `flow`, over a country that reads 0.2 and 0.5, and those strata."""
    strata = _Shares({"literacy_general": 0.2, "literacy_elite": 0.5})

    class Schooled(Diffusion):
        def effective_schooling_flow(self, field=None):
            return flow

        def literacy_ceiling(self, field):
            return {"literacy_elite": 0.9, "common": 0.8}[field]
    views, answers = literacy_stand_in.over(strata)
    module = module_harness.build(Schooled, views=views, answers=answers)
    return module, strata


with mock.patch.object(diffusion_constants, "LITERACY_GROWTH_RATE_ELITE", 0.1), \
        mock.patch.object(diffusion_constants, "LITERACY_GROWTH_RATE_GENERAL", 0.1):
    previewing, previewing_strata = _schooling_game()
    preview = previewing.literacy_next_year()
    check("a preview of the schooling year reports the gain and leaves the strata where they were",
          previewing_strata.shares == {"literacy_general": 0.2, "literacy_elite": 0.5} and abs(preview["literacy_general"] - 0.26) < 1e-9, (preview, previewing_strata.shares))
    applying, applying_strata = _schooling_game()
    applied = applying._school_literacy()
    check("the schooling year moves the strata to the figures the preview gave", applied == preview and abs(applying_strata.shares["literacy_general"] - 0.26) < 1e-9, (applied, preview))
check("with no schooling flow the schooling year changes nothing", _schooling_game(0.0)[0]._school_literacy() == {})

# --- demography
flows = Game(start_total=2000.0, births=60.4, deaths=40.6, immigration=1.0, emigration=2.0, deaths_children=10.0,
                        deaths_working_age=20.0, deaths_elderly=10.6, nutrition_ratio=0.98765)
with mock.patch.object(screen_demography.ui_port, "last_demographic_step", lambda game: flows):
    last = screen_demography._last_year(Game())
check("last year's births and deaths are the flows' figures rounded, with the rates per thousand of the start total",
      last["births"] == 60 and last["deaths"] == 41 and last["births_per_thousand"] == 30.2 and last["deaths_per_thousand"] == 20.3
      and last["nutrition_ratio"] == 0.9877, last)
no_start = Game(**{**flows.__dict__, "start_total": 0.0})
with mock.patch.object(screen_demography.ui_port, "last_demographic_step", lambda game: no_start):
    check("a year that began with nobody has no rate per thousand", screen_demography._last_year(Game())["births_per_thousand"] is None)
record_game = Game(view=lambda name: lambda: [{"year": 100, "births": 5, "deaths": 4, "nutrition_ratio": 1.0},
                                                          {"year": 101, "births": 7, "deaths": 6, "nutrition_ratio": 0.9}])
with mock.patch.object(screen_demography.ui_port, "last_demographic_step", lambda game: None):
    from_record = screen_demography._last_year(record_game)
    check("with no flows held the last year is the newest record's births, deaths and nutrition",
          from_record == {"births": 7, "deaths": 6, "nutrition_ratio": 0.9, "year": 101}, from_record)
    empty_record = Game(view=lambda name: lambda: [])
    check("with no flows and no record there is no last year", screen_demography._last_year(empty_record) is None)

# --- divergence
check("a start/now pair is rounded and a missing start stays missing",
      screen_divergence._pair(None, 1.23456) == {"start": None, "now": 1.2346} and screen_divergence._pair(1.0, 2.0)["start"] == 1.0)
built_game = Game(done={"b", "a", "c", "g"}, granted={"g"}, done_year={"a": 5, "b": 3}, nodes={name: {"name": name.upper()} for name in "abcg"})
check("the technologies you built exclude what was granted and run in the order built, undated last",
      [row["id"] for row in screen_divergence._built(built_game)] == ["c", "b", "a"], screen_divergence._built(built_game))
hazards = [{"name": "old", "years": [10, 20]}, {"name": "past", "years": [50, 60]}, {"name": "now", "years": [95, 110]},
           {"name": "later", "years": [200, 210]}, {"name": "unscheduled"}]
event_game = Game(cfg={"start_year": 30}, year=100, civ={"hazards": hazards}, fog=False)
event_game.event_cause_report = lambda hazard: {"checked": False, "failed": []}
events = screen_divergence._dated_events(event_game)
fogged_events = screen_divergence._dated_events(Game(**{**event_game.__dict__, "fog": True}))
check("a dated event is before the run, happened, under way or upcoming by where the year stands against its years",
      [(row["years"][0], row["status"]) for row in events] == [(10, "before the run began"), (50, "happened"), (95, "under way"), (200, "upcoming")], events)
check("an event with no years is not listed", len(events) == 4)
check("under fog an upcoming event's name is withheld and the others keep theirs",
      [row.get("name") for row in fogged_events] == ["old", "past", "now", None], fogged_events)
failing = {"checked": True, "failed": [{"quantity": "q", "node": "n", "op": ">", "threshold": 1, "value": 0, "why": "w"}]}
event_game.event_cause_report = lambda hazard: failing
judged = screen_divergence._dated_events(event_game)[0]
check("an event whose causes fail says so and lists the failed causes", judged["causes_hold_now"] is False and judged["failed_causes"][0]["quantity"] == "q", judged)
with mock.patch.object(screen_divergence.baseline_ensemble, "read_cache", return_value=None):
    section = screen_divergence.baseline_section(Game(civ={"id": "rome"}, cfg={"start_year": 1}, year=1))
check("with no baseline ensemble stored the section says it is unavailable and how to generate it",
      section["available"] is False and "baseline-ensemble --civ rome" in section["how_to_generate"], section)
with mock.patch.object(screen_divergence.baseline_ensemble, "read_cache", return_value={"start_year": 99}):
    other_start = screen_divergence.baseline_section(Game(civ={"id": "rome"}, cfg={"start_year": 1}, year=1))
check("an ensemble made for another start year is unavailable", other_start["available"] is False, other_start)
