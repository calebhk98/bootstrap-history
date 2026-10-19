"""The world event log: dated records of what changed in the world and why, saved with the game and readable by
every seat (Complaint 493).

A record is {year, kind, actors, tiles, cause, facts}: who was involved (country or seat ids), the tiles, a
cause in words, and structured figures. The log lives in `state.economy.world_events`, is shared by all seats
and keeps the last `event_log_years_kept` years (data/world/world_hazards.json)."""
from . import world_hazard_data


def record(sim, kind, actors=(), tiles=(), cause="", **facts):
    """Append one record dated to the game's current year; returns it."""
    entry = {"year": int(sim.state.scenario.year), "kind": kind, "actors": [str(actor) for actor in actors],
             "tiles": [str(tile) for tile in tiles], "cause": cause, "facts": dict(facts)}
    kept = sim.state.economy.world_events
    kept.append(entry)
    oldest = entry["year"] - world_hazard_data.years_kept()
    if kept[0]["year"] <= oldest:
        kept[:] = [row for row in kept if row["year"] > oldest]
    return entry


def rows(sim, kind=None, since_year=None, actor=None):
    """The records, oldest first, optionally of one kind, from a year on, or involving one actor."""
    return [dict(row) for row in sim.state.economy.world_events
            if (kind is None or row["kind"] == kind)
            and (since_year is None or row["year"] >= since_year)
            and (actor is None or actor in row["actors"])]
