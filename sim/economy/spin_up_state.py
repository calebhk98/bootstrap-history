"""The physical state of the economy at the end of a year, for judging whether the spin-up settled."""


def spin_up_state(setup, record, outcome):
    """Real output and producers' inventories (quantities valued at the opening prices, so a price swing is not
    read as a quantity change), hours hired and idle, and unmet need (food floor units short)."""
    weight = setup.opening_prices
    held = 0.0
    for agent in record.producers:
        for good, by_tile in record.book.holdings(agent)["goods"].items():
            if good in weight:      # a good with no opening price is left out of the value
                held += weight[good] * sum(by_tile.values())
    return {"real_output": sum(weight[good] * quantity for good, quantity in outcome.output.items() if good in weight),
            "hired_hours": outcome.hired_hours, "idle_hours": outcome.idle_hours, "inventory_value": held,
            "unmet_need": sum(outcome.hunger_by_tile.values())}
