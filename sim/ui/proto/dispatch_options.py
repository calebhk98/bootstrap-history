"""`options`: read or change the saved program settings, from the same table as the menu."""

from sim.engine.ui_port import settings, settings_table
from .command_registry import command


@command("options", group="game",
         summary="the saved settings (the menu's Options screen)",
         usage=["options", '{"cmd":"options","set":"rows_per_page","value":20}'],
         options={"set": "the setting's key, from the listing", "value": "its new value"},
         description="Lists every setting with its meaning and whether it applies only "
                     "when a game starts. With set and value, saves one in the config "
                     "file. In `agent` games the dice come from --no-events and "
                     "--deterministic, not from these settings.")
def _cmd_options(sim, nodes, cmd, ended):
    config = settings.load_config()
    key = cmd.get("set")
    if key is not None:
        if key not in settings_table.SETTINGS:
            return {"ok": False, "error": "no setting %r; the keys are: %s"
                    % (key, ", ".join(settings_table.SETTINGS))}
        if "value" not in cmd:
            return {"ok": False, "error": "give a value, e.g. "
                    '{"cmd":"options","set":"%s","value":...}' % key}
        value, problem = settings_table.parse_value(key, cmd["value"])
        if problem:
            return {"ok": False, "error": "%s: %s. Nothing was changed." % (key, problem)}
        if value is not settings_table.UNCHANGED:
            config[key] = value
            if not settings.save_config(config):
                return {"ok": False, "error": "could not write the config file %s" % settings.config_path()}
    return {"ok": True, "options": _fogged(sim, nodes, settings_table.rows(config)), "config_file": settings.config_path(),
            "note": "Saved settings are read when the program starts a game."}


def _fogged(sim, nodes, rows):
    """A setting whose value names a technology this founder has not heard of shows no id."""
    for row in rows:
        for field in ("value", "shown_as"):
            value = row.get(field)
            if isinstance(value, str) and value in nodes and not sim.is_visible(value):
                row[field] = "(a technology you have not heard of)"
    return rows
