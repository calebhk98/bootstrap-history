"""What moved in each score component since the player last typed `score`."""


def attach_change_since_last_score(sim, report):
    """Add `since_last_score` to each component that was also read last time, then remember this reading."""
    seat_progress = sim.state.seat_progress
    earlier = seat_progress.score_last_seen or {}
    seen = {}
    for name, component in report["components"].items():
        if component.get("normalized") is None:
            continue
        seen[name] = {"normalized": component["normalized"], "raw": component.get("raw")}
        before = earlier.get("components", {}).get(name)
        if before is not None:
            component["since_last_score"] = {
                "year": earlier.get("year"),
                "raw_before": before["raw"],
                "normalized_change": round(component["normalized"] - before["normalized"], 4)}
    seat_progress.score_last_seen = {"year": sim.year, "components": seen}
    return report
