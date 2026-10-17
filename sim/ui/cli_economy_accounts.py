"""`economy-check --accounts`: play years of a game (or resume a saved session) and print the agent economy's
yearly accounts: production, use, consumption, investment and stock per good, food eaten against need by tile and
cohort, and the real wage against the opening's basket (sim/economy/year_accounts.py, Complaint 554)."""
import random

from sim.engine import saveload
from sim.engine.ui_port import Sim, load, load_civ

GOOD_COLUMNS = (("production", "made"), ("production_grown", "grown"), ("intermediate_use", "inputs"),
                ("final_consumption_bought", "eaten bought"), ("final_consumption_grown", "eaten grown"),
                ("durable_wear", "wear"), ("investment", "built"), ("spoilage", "spoiled"),
                ("stock_change", "stock chg"), ("market_turnover", "turnover"))


def format_accounts(accounts, quiet_below=0.0):
    """One year's accounts as text. Goods with nothing made, used or held are left out."""
    lines = ["year %d" % accounts.year,
             "  %-22s" % "good" + "".join(" %12s" % label for _field, label in GOOD_COLUMNS) + " %12s" % "unexplained"]
    for good, account in accounts.goods.items():
        values = [getattr(account, name) for name, _label in GOOD_COLUMNS]
        if all(abs(value) <= quiet_below for value in values):
            continue
        lines.append("  %-22s" % good + "".join(" %12.5g" % value for value in values) + " %12.3g" % account.residual())
    if accounts.plant_wear:
        lines.append("  plant worn out, in the goods it is built of: " + ", ".join(
            "%s %.5g" % (good, quantity) for good, quantity in accounts.plant_wear.items()))
    lines.append("  food eaten per head against need, by tile (need units, share of the floor)")
    for tile in accounts.tiles:
        lines.append("    %-20s people %10.5g  eaten %10.5g  need %10.5g  share %6.3f" % (
            tile.tile, tile.people, tile.eaten_per_head, tile.need_per_head, tile.eaten_over_need))
    lines.append("  by cohort (bought and own-plot per head; real income per head in opening baskets)")
    for cohort in accounts.cohorts:
        lines.append("    %-20s eaten %10.5g  bought %10.5g  own plot %10.5g  share %6.3f  real income %8.4g" % (
            cohort.cohort, cohort.eaten_per_head, cohort.bought_per_head, cohort.own_plot_per_head,
            cohort.eaten_over_need, cohort.real_income_per_head))
    lines.append("  real wage against the opening's basket")
    for wage in accounts.real_wages.values():
        lines.append("    %-20s wage %9.4g  opening wage %9.4g  index %8.4g  baskets per working year %8.4g" % (
            wage.trade, wage.wage_per_hour, wage.wage_per_hour_opening, wage.real_wage_index,
            wage.baskets_per_working_year))
    return "\n".join(lines)


def play_for_accounts(args):
    """The accounts of each year played: a fresh game of the civilisation, or the saved session `args.session`
    resumed (not written back)."""
    _tree, _prices, nodes, _wages, _goods = load()
    session = getattr(args, "session", None)
    if session:
        game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(saveload.civ_of_save(session)))
        saveload.load_state(game, session)
    else:
        from sim.engine.ui_port import default_civilisation_id
        game = Sim(nodes, [], random.Random(1), events=False, manual=True,
                   civ=load_civ((getattr(args, "civs", "") or default_civilisation_id()).split(",")[0]))
        game.done_year = {}
    outcomes = []
    for _year in range(args.years):
        game.step()
        outcomes.append(game.economy.agent.outcomes[-1])
    return [outcome.accounts for outcome in outcomes]


def cmd_economy_accounts(args):
    for accounts in play_for_accounts(args):
        print(format_accounts(accounts))
    return 0
