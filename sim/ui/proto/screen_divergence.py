"""The `divergence` screen (Complaints/266): what the founder has changed
against where the run began, and which dated events came and went.

The game holds start values (the civilisation the game began with) and the dated hazard
list. It holds no baseline run and no per-technology historical date, so the
screen says what it cannot know instead of guessing.
"""
from sim.geography.api import regions_of_tiles, tiles_held

_HAPPENED = "happened"
_UNDER_WAY = "under way"
_UPCOMING = "upcoming"
_BEFORE_RUN = "before the run began"


def _pair(start, now, digits=4):
    return {"start": None if start is None else round(float(start), digits),
            "now": round(float(now), digits)}


def _built(sim):
    done_year = getattr(sim, "done_year", None) or {}
    return [{"id": node_id, "name": sim.nodes[node_id]["name"],
             "year": done_year.get(node_id)}
            for node_id in sorted(sim.done - sim.granted,
                                  key=lambda node: (done_year.get(node) or 0, node))]


def _dated_events(sim):
    run_start = sim.cfg["start_year"]
    rows = []
    for hazard in sim.civ.get("hazards") or []:
        years = hazard.get("years") or []
        if not years:
            continue
        year_start, year_end = years[0], years[-1]
        if year_end < run_start:
            status = _BEFORE_RUN
        elif year_end < sim.year:
            status = _HAPPENED
        elif year_start <= sim.year:
            status = _UNDER_WAY
        else:
            status = _UPCOMING
        row = {"status": status, "years": [year_start, year_end],
               "causes_checked": False}
        if not (sim.fog and status == _UPCOMING):
            row["name"] = hazard.get("name", "hazard")
        rows.append(row)
    return sorted(rows, key=lambda row: row["years"])


def divergence_report(sim):
    start = sim.start_civ

    def started(field):
        return None if start is None else start.get(field)

    now_regions = regions_of_tiles(tiles_held(sim.civ, sim.world_map))
    start_regions = [] if start is None else regions_of_tiles(
        tiles_held(start, sim.world_map))
    spread = sim.world_diffusion_report()
    return {
        "ok": True,
        "start_year": sim.cfg["start_year"], "year": sim.year,
        "years_elapsed": sim.year - sim.cfg["start_year"],
        "technologies_you_built": _built(sim),
        "spread_into_the_society": spread,
        "population": {"start": round(float(sim.civ.get("population", 0.0))),
                       "now": round(sim.population.total)},
        "wage_index": _pair(started("wage_index"), sim.wage_index),
        "price_index": _pair(started("price_index"), sim.price_index),
        "literacy_general": _pair(started("literacy_general"),
                                  sim.civ.get("literacy_general", 0.0)),
        "literacy_elite": _pair(started("literacy_elite"),
                                sim.civ.get("literacy_elite", 0.0)),
        "territory": {"start": start_regions, "now": now_regions,
                      "changed": start_regions != now_regions},
        "dated_events": _dated_events(sim),
        "cannot_know": [
            "no baseline run is held, so what the recorded society would have "
            "reached by now is not known: only the start values are compared",
            "technologies carry no historical date, so the screen lists what "
            "you built, not which of them the society would not yet have",
            "dated events fire on schedule and the game does not check their "
            "causes (causes_checked is false for every one), so none can "
            "yet be skipped or changed",
        ],
    }
