"""The founder's yearly income from concerns sold in the book, on a playtest-shaped game: `python3 -m sim.tests.income_probe`.

Opens concerns whose goods the economy trades (default two), steps a few years and prints, per year, the credits the
founder received by purpose, the forecast `revenue()` read before the year and `upkeep()`. Run it on two checkouts and compare the lines."""
import argparse


from sim.ledger.api import PayEdge, ReceiveFromEdge

from .harness import sim
from sim.ventures.api import OpenVenture

RAMPED_YEARS = 10    # opened this long ago, so no concern is still ramping or shed as a young loss


def open_book_concerns(game, count):
    """Open up to `count` concerns of the default Rome game with an output the economy trades; their ids."""
    traded = set(game.view("legacy_economy")().agent_prices_at() or {})
    game.state.household.artisans += 20.0 * count    # hands to supervise them
    world = game.view("actor_world")()
    opened = []
    for node_id, node in sorted(game.nodes.items()):
        if len(opened) >= count:
            break
        if not (node["rev"] > 0 and node["up"] > 0 and game.view("is_venture")[node_id]):
            continue
        baskets = game.view("concern_baskets_now")[node_id]
        if baskets is None or not baskets.outputs or not any(material in traded for material in baskets.outputs):
            continue
        if game.view("venture_hands")[node_id][0] > 0 or game.view("venture_real_earnings")(node_id, None, True, True) <= 0.0:
            continue
        game.state.projects.done.update(node["pre"])
        game.state.projects.done.add(node_id)
        game._done_changed()
        game.send(OpenVenture(node_id, None))
        if node_id in game.state.projects.operating:
            for trade, share in sorted(world.concern_staff(node_id).items()):
                game.view("legacy_labour")().hire(trade, int(share) + 1)    # the crew it runs with
            game.state.projects.business.set_opened_year(node_id, game.year - RAMPED_YEARS)
            opened.append(node_id)
    return opened


def tally_credits(game):
    """{purpose: coin} the founder's household receives from the edges (paid out is negative), filled as the game steps."""
    totals = {}
    sent = game.send

    def tally(command):
        if isinstance(command, ReceiveFromEdge):
            totals[command.purpose] = totals.get(command.purpose, 0.0) + command.amount
        elif isinstance(command, PayEdge):
            totals[command.purpose] = totals.get(command.purpose, 0.0) - command.amount
        return sent(command)
    game.send = tally
    return totals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--concerns", type=int, default=2)
    parser.add_argument("--years", type=int, default=3)
    args = parser.parse_args()
    game = sim(capital=1e9, manual=True)
    print("concerns", open_book_concerns(game, args.concerns))
    credits = tally_credits(game)
    for _ in range(args.years):
        credits.clear()
        forecast, upkeep = game.view("revenue_estimate")(), game.view("upkeep")()
        game.step()
        print("year %d forecast revenue %.0f upkeep %.0f credits %s"
              % (game.year, forecast, upkeep, {purpose: round(coin) for purpose, coin in sorted(credits.items())}))


if __name__ == "__main__":
    main()
