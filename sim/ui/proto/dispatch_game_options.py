"""Game-level per-save settings: dashboard_history_years and future per-game options."""

from .command_registry import command


def _parse_history_cap(value):
    """Parse dashboard history cap from user input: positive int or 'off'/'none'."""
    if isinstance(value, str):
        if value.lower() in ("off", "none"):
            return None, None
        try:
            value = int(value)
        except ValueError:
            return None, "must be a positive integer or 'off'/'none'"
    if isinstance(value, int):
        if value <= 0:
            return None, "must be a positive integer or 'off'/'none'"
        return value, None
    return None, "must be a positive integer or 'off'/'none'"


@command("game_options", group="game",
         summary="per-game settings that affect a save",
         usage=["game_options", '{"cmd":"game_options","set":{"dashboard_history_years":"off"}}'],
         options={"set": "a dict of option names to their values"},
         description="Lists every per-game option and its current value. With set, changes "
                     "one or more. dashboard_history_years: cap the dashboard history to N "
                     "most recent years (default: off, no cap). Set to a positive integer or "
                     "'off'/'none' to disable the cap.")
def _cmd_game_options(sim, nodes, cmd, ended):
    requested_options = cmd.get("set")
    changed = {}
    if requested_options is not None:
        if not isinstance(requested_options, dict):
            return {"ok": False,
                    "error": 'set must be an object, e.g. '
                             '{"cmd":"game_options","set":{"dashboard_history_years":10}}'}
        for key, value in requested_options.items():
            if key == "dashboard_history_years":
                parsed, error = _parse_history_cap(value)
                if error:
                    return {"ok": False, "error": "dashboard_history_years: %s" % error}
                sim.state.seat_progress.dashboard_history_years = parsed
                changed[key] = parsed
            else:
                return {"ok": False, "error": "no such game option: %s. Available: "
                        "dashboard_history_years" % key}
    return {"ok": True,
            "game_options": {
                "dashboard_history_years": sim.state.seat_progress.dashboard_history_years
            },
            "changed": changed,
            "note": "These options are saved with the game and affect how a save is written."}
