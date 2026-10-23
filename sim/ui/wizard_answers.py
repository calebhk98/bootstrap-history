"""What the New Game wizard remembers of its answers, as next time's defaults."""

REMEMBERED_KEYS = ("default_civ", "default_kit", "default_fog", "default_fuzzy_estimates", "default_mortal",
                   "default_goal", "default_horizon")


def remember_answers(config, civilisation_id, kit, fog, fuzzy, mortal, goal, horizon):
    """Write the wizard's answers (fog, fuzzy and mortal as "y"/"n") into `config` under the `default_*` keys and
    nothing else: the display width, rows per page and the welcome toggle belong to the Options screen."""
    config["default_civ"] = civilisation_id
    config["default_kit"] = kit
    config["default_fog"] = (fog == "y")
    config["default_fuzzy_estimates"] = (fuzzy == "y")
    config["default_mortal"] = (mortal == "y")
    config["default_goal"] = goal
    config["default_horizon"] = horizon
    return config
