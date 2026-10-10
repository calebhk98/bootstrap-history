"""The successor objective `state` shows: deputies, their hours, and whether
they are enough to carry the work without the founder."""

from sim.engine.ui_port import plain_number


def succession_block(sim):
    """Deputy count, yearly hours, the threshold, and a named objective."""
    deputies = sim.state.household.directors_extra
    needed = sim.DEPUTIES_CARRY_THE_WORK_FROM
    carry = sim.deputies_carry_the_work()
    block = {
        "deputies": round(deputies, 2),
        "deputy_hours_a_year": round(sim.deputy_hours(), 1),
        "deputies_needed_to_carry_the_work": needed,
        "deputies_carry_the_work": carry,
    }
    if carry:
        block["objective"] = ("train a successor: met. Your deputies carry the work "
                              "(%s hours a year) if you are lost."
                              % plain_number(sim.deputy_hours()))
        return block
    sources = sorted(sim.nodes[node_id]["name"]
                     for node_id, _scholars, _artisans, directors, _scales, _running
                     in sim.STAFF_CAPACITY_SOURCES
                     if directors > 0 and sim.has(node_id))
    where = ("deputies come from institutions you keep open, such as %s"
             % ", ".join(sources) if sources
             else "deputies come from institutions that grant them; 'why' on an "
                  "institution says whether it does")
    block["objective"] = ("train a successor: your deputies are %.2f, %.2f more are "
                          "needed to carry the work without you (they work %s hours a "
                          "year now, which still counts as work). %s."
                          % (deputies, max(0.0, needed - deputies),
                             plain_number(sim.deputy_hours()), where))
    return block
