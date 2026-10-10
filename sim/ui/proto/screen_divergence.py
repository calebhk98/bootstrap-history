"""The `divergence` screen (Complaints/266): what the founder has changed
against where the run began, and which dated events came and went.

The game holds start values (the civilisation the game began with) and the dated hazard
list, each hazard's stated causes judged against the run as it stands. The baseline ensemble
(`simulator.py baseline-ensemble`, kept in a cache file) says what the society tends to reach with no
player; when it has not been generated the screen says so and how to make it, rather than guessing.
"""
from sim.engine import baseline_ensemble, event_causes
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
        report = event_causes.evaluate_causes(sim, hazard)
        row = {"status": status, "years": [year_start, year_end],
               "causes_checked": report["checked"]}
        if report["checked"]:
            row["causes_hold_now"] = not report["failed"]
            row["failed_causes"] = [
                {key: cause[key] for key in ("quantity", "node", "op", "threshold", "value", "why")}
                for cause in report["failed"]]
        if hazard.get("causes_not_modelled"):
            row["causes_not_modelled"] = list(hazard["causes_not_modelled"])
        if not (sim.fog and status == _UPCOMING):
            row["name"] = hazard.get("name", "hazard")
        rows.append(row)
    return sorted(rows, key=lambda row: row["years"])


def tile_count(sim):
    return len(tiles_held(sim.civ, sim.world_map))


def _current(sim):
    return {"population": float(sim.population.total), "wage_index": float(sim.wage_index),
            "literacy_general": float(sim.civ.get("literacy_general", 0.0)),
            "literacy_elite": float(sim.civ.get("literacy_elite", 0.0)),
            "territory_tiles": float(tile_count(sim))}


def baseline_section(sim, directory=None):
    """The run against the baseline ensemble: each measure against its band for this year, and which
    technologies you built that the baseline society would not yet hold. Absent: how to generate it."""
    civilisation_id = str(sim.civ.get("id"))
    stored = baseline_ensemble.read_cache(civilisation_id, directory)
    generate = ("python3 sim/simulator.py baseline-ensemble --civ %s --seeds 20 --years 300 "
                "(each game takes a long time to play; add --jobs to play several at once)" % civilisation_id)
    if stored is None:
        return {"available": False, "how_to_generate": generate,
                "reason": "no baseline ensemble has been generated for this civilisation"}
    if stored.get("start_year") != sim.cfg["start_year"]:
        return {"available": False, "how_to_generate": generate,
                "reason": "the stored ensemble was made for another start year"}
    offset = max(0, sim.year - sim.cfg["start_year"])
    horizon = min(offset, stored["years"])
    compared = {}
    for metric, value in _current(sim).items():
        bands = {name: stored["metrics"][metric][name][horizon] for name, _share in baseline_ensemble.BANDS}
        compared[metric] = {"now": round(value, 4), "baseline": {name: round(band, 4) for name, band in bands.items()},
                            "position": baseline_ensemble.position(value, bands)}
    technologies = [dict(row, **baseline_ensemble.technology_standing(stored, row["id"], horizon))
                    for row in _built(sim)]
    return {"available": True, "runs": stored["runs"], "years_played": stored["years"],
            "compared_at_offset": horizon, "beyond_horizon": offset > stored["years"],
            "compared": compared, "technologies": technologies,
            "technologies_ahead_of_the_baseline": [row["name"] for row in technologies if row["would_not_yet_hold"]]}


def divergence_report(sim):
    start = sim.start_civ

    def started(field):
        return None if start is None else start.get(field)

    now_regions = regions_of_tiles(tiles_held(sim.civ, sim.world_map))
    start_regions = [] if start is None else regions_of_tiles(
        tiles_held(start, sim.world_map))
    spread = sim.world_diffusion_report()
    baseline = baseline_section(sim)
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
        "baseline": baseline,
        "cannot_know": [
            ("the baseline is the society's own tendency over several runs with no "
             "player, not recorded history, so it can differ from what happened"
             if baseline["available"] else
             "no baseline ensemble is held, so what the society would have reached "
             "by now is not known: only the start values are compared; generate it with "
             + baseline["how_to_generate"]),
            "an event with causes_checked false states no causes in its data and "
            "fires on schedule; one with causes_checked true is skipped (or "
            "weakened) in a year its causes do not hold, judged as things "
            "stand today",
        ],
    }
