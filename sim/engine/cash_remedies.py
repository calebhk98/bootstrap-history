"""The commands that raise cash or cut costs, each quoted with the amount the
command itself uses, for refusals to list. Any actor with a household,
material stock, concerns, mines and staff can be asked."""

REMEDY_LIMIT = 6


def cash_remedies(actor):
    """Lines like "sell iron 40 (brings 1,200 now)", largest amount first."""
    found = []
    for material in sorted(actor._material_stock()):
        stock = actor.material_stock_t(material)
        _key, tonnes, money = actor.goods_market.quote_sell(material, stock)
        if money > 0:
            found.append((money, "sell %s %s (brings %s now)" % (
                material, "{:,.1f}".format(tonnes), "{:,.0f}".format(money))))
    projects = actor.state.projects
    for node_id in sorted(projects.operating):
        if node_id in projects.done and node_id not in projects.granted:
            saving = actor.venture_real_upkeep(node_id)
            if saving > 0.5:
                found.append((saving, "mothball %s (stops %s a year of upkeep)" % (
                    node_id, "{:,.0f}".format(saving))))
    for material in sorted(actor.mine_capacity):
        saving = sum(actor.mine_operating_cost_for(working)
                     for working in actor._workings_of(material))
        if saving > 0.5:
            found.append((saving, "close %s (stops %s a year of mine costs)" % (
                material, "{:,.0f}".format(saving))))
    for trade, count in sorted(actor.state.household.employees.items()):
        wage = actor.annual_wage(trade)
        if count > 0 and wage > 0.5:
            found.append((wage, "fire %s (stops %s a year per person)" % (
                trade, "{:,.0f}".format(wage))))
    found.sort(key=lambda entry: -entry[0])
    return [line for _amount, line in found[:REMEDY_LIMIT]]
