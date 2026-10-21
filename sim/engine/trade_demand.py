"""What a portfolio of active projects asks of each hired trade against what the trade can supply, and what one more
start would add. Plain arithmetic over tables; reads no game."""


def trade_demand_table(desired_hours_by_project, supply_of):
    """{trade: {demand_hours_this_year, supply_hours_this_year, oversubscribed, projects_drawing_on_it}}.

    `desired_hours_by_project` is {project id: {trade: hours it wants this year}}; `supply_of(trade)` is what the
    trade can supply. Projects and trades are walked in sorted order because the sums are floats and the dicts' key
    order depends on the string hash seed."""
    demand = {}
    drawing = {}
    for node_id in sorted(desired_hours_by_project):
        for trade_id, hours in sorted(desired_hours_by_project[node_id].items()):
            demand[trade_id] = demand.get(trade_id, 0.0) + hours
            drawing.setdefault(trade_id, []).append(node_id)
    out = {}
    for trade_id in sorted(demand):
        supply = supply_of(trade_id)
        out[trade_id] = {"demand_hours_this_year": round(demand[trade_id], 1),
                         "supply_hours_this_year": round(supply, 1),
                         "oversubscribed": bool(demand[trade_id] > supply + 1e-6),
                         "projects_drawing_on_it": sorted(drawing[trade_id])}
    return out


def oversubscription_notes(demand_now, own_plan, supply_of, impossible_trades, number_words):
    """One sentence for each trade that a project about to start would push past what the trade supplies.

    Oversubscribed is not the same as impossible: the society may be able to field the trade the project wants and
    still not have enough left once the other active work draws on it. `demand_now` is the portfolio's table before
    the start (`trade_demand_table`), `own_plan` is {trade: {"desired": hours}} for the new project, and trades in
    `impossible_trades` were already reported more plainly. `number_words` writes a number for the player."""
    notes = []
    for trade, plan in own_plan.items():
        if trade in impossible_trades:
            continue
        supply = supply_of(trade)
        if supply <= 0:
            continue
        existing = demand_now.get(trade, {}).get("demand_hours_this_year", 0.0)
        competitors = len(demand_now.get(trade, {}).get("projects_drawing_on_it", ()))
        new_total = existing + plan["desired"]
        if new_total > supply + 1e-6:
            notes.append(
                "%s: this portfolio would want %s hours a year against %s this society can supply (%d other active "
                "project%s already drawing on it); this one competes for what is left, it does not get %s to itself"
                % (trade, number_words(new_total), number_words(supply), competitors, "" if competitors == 1 else "s",
                   number_words(plan["desired"])))
    return notes
