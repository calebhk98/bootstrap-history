"""The commands that raise cash or cut costs, each quoted with the amount the
command itself uses, for refusals to list. Any actor with a household,
material stock, concerns, mines and staff can be asked."""

from sim.living_stock.api import stock_rates
from .units_prose import money_text

REMEDY_LIMIT = 6


def cash_remedies(actor):
    """Lines like "sell iron 40 (brings 1,200 now)", largest amount first."""
    found = []
    # Living stock is the means of breeding more; it is not offered as cash.
    breeding_stock = {actor.view("material_commodity")[material] for material in stock_rates()}
    for material in sorted(actor.view("held_goods")()):
        if material in breeding_stock:
            continue
        stock = actor.view("goods_stock")[material]
        _key, tonnes, money = actor.view("legacy_goods_market")().quote_sell(material, stock)
        if money > 0:
            found.append((money, "sell %s %s (brings %s now)" % (
                material, "{:,.1f}".format(tonnes), money_text(money, actor, grouped=True))))
    projects = actor.state.projects
    held, granted = actor.view("techniques_held")(), actor.view("techniques_granted")()
    for node_id in sorted(projects.operating):
        if node_id in held and node_id not in granted:
            saving = actor.view("venture_real_upkeep")(node_id)
            if saving > 0.5:
                found.append((saving, "mothball %s (stops %s a year of upkeep)" % (
                    node_id, money_text(saving, actor, grouped=True))))
    for material in sorted(actor.view("mine_capacity")()):
        saving = sum(actor.view("mine_working_cost")(working)
                     for working in actor._workings_of(material))
        if saving > 0.5:
            found.append((saving, "close %s (stops %s a year of mine costs)" % (
                material, money_text(saving, actor, grouped=True))))
    for trade, count in sorted(actor.view("staff")()["employees"].items()):
        wage = actor.labour.market.quote_annual(trade)
        if count > 0 and wage > 0.5:
            found.append((wage, "fire %s (stops %s a year per person)" % (
                trade, money_text(wage, actor, grouped=True))))
    found.sort(key=lambda entry: -entry[0])
    return [line for _amount, line in found[:REMEDY_LIMIT]]
