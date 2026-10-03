"""Long explanations shown once per game, then a one-line pointer.

The record is `ScenarioState._said_explanations` (topic -> year first shown),
which the save file carries. A command's `full` flag always shows the whole
text again.
"""

import sim.engine.ui_port as ui_port


def already_explained(sim, topic, cmd):
    """True when `topic` was shown earlier in this game and the player did
    not ask for `full`. Marks the topic shown either way."""
    scenario = sim.state.scenario
    said = ui_port.said_explanations(scenario) or {}
    seen = topic in said
    if not seen:
        said[topic] = sim.year
        ui_port.set_said_explanations(scenario, said)
    return seen and not cmd.get("full")
