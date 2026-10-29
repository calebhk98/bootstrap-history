"""The successor objective `state` shows: deputies, their hours, and whether
they are enough to carry the work without the founder."""

from sim.engine.ui_port import plain_number


def succession_block(sim):
    """Deputy count, yearly hours, the threshold, and a named objective."""
    deputies = sim.view("staff")()["directors_extra"]
    patronage = sim.view("patronage")()
    needed = patronage["deputies_needed"]
    carry = patronage["deputies_carry_the_work"]
    block = {
        "deputies": round(deputies, 2),
        "deputy_hours_a_year": round(sim.view("staff")()["directors_extra"] * sim.view("game_config")()["director_hours_per_year"], 1),
        "deputies_needed_to_carry_the_work": needed,
        "deputies_carry_the_work": carry,
    }
    if carry:
        block["objective"] = ("train a successor: met. Your deputies carry the work "
                              "(%s hours a year) if you are lost."
                              % plain_number(sim.view("staff")()["directors_extra"] * sim.view("game_config")()["director_hours_per_year"]))
        return block
    sources = sorted(sim.view("tree_nodes")()[node_id]["name"]
                     for node_id, _scholars, _artisans, directors, _scales, _running
                     in sim.view("staff_capacity_sources")()
                     if directors > 0 and node_id in sim.view("techniques_held")())
    where = ("deputies come from institutions you keep open, such as %s"
             % ", ".join(sources) if sources
             else "deputies come from institutions that grant them; 'why' on an "
                  "institution says whether it does")
    block["objective"] = ("train a successor: your deputies are %.2f, %.2f more are "
                          "needed to carry the work without you (they work %s hours a "
                          "year now, which still counts as work). %s."
                          % (deputies, max(0.0, needed - deputies),
                             plain_number(sim.view("staff")()["directors_extra"] * sim.view("game_config")()["director_hours_per_year"]), where))
    return block
