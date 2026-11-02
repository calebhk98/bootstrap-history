"""Refusals that hiring, teaching and commissioning share, so the verbs cannot drift apart."""
from sim.refusal import Refusal

from . import trade_data
from .staff_moves import whole_people_under_wall


def cash_in_hand_refusal(world, what, fee):
    """Refusal of a wage, an apprentice's keep or a job's fee for want of money. A wage or fee is spent outright, so it
    draws on the purchase budget; purchase_rule states that rule, the budget and the shortfall, the same text `start`
    and `buy` give."""
    return Refusal("cash_short", world.refusal_text(what, fee))


def economy_lacks(world, trade):
    """Whether the open economy holds no market for the trade, so a place or order for it would not be posted."""
    held = world.economy.agent_trades()
    return held is not None and trade not in held


def economy_lacks_refusal(trade):
    return Refusal("trade_not_in_economy", "the economy holds no %s market, so work in it cannot be posted to the labour market. "
                   "Nothing was changed." % trade)


def literate_wall_refusal(trade, cap, have):
    """The refusal hire() and train() give when literate_capacity() bites.

    SAY HOW MANY YOU CAN HAVE, NOT ONLY THAT YOU CANNOT HAVE SIX: a
    ceiling quoted as "will not supply more than 5.9 in total, ever, at
    any price" reads as being capped out entirely, even when the
    requester holds none and a smaller request would succeed. Say the
    number they should type.

    AND DO NOT BLAME LITERACY FOR A WALL IT DID NOT BUILD: "this
    society's literacy will not supply more than X" for every trade
    alike is a real description of the Norse scribe case and a false
    one of the Rome scholar case. Rome's literacy_elite starts at
    0.900 against a field capped at 1.0, so literacy itself can never
    move this ceiling by more than about eight per cent, while the
    quantity doing the work is the labour core's people of the
    trade in reach and, for scholar, the institutional pool literate_capacity() folds in. Both matter; only one is literacy, and saying only
    "literacy" when the market-reach term is doing most of the work
    misleads a player into pulling the wrong lever.
    """
    _whole = whole_people_under_wall(cap, have)
    lever = (
        "Building the institutions that train scholars outright - a "
        "school, an academy, an imperial patron - is what actually "
        "moves this number; printing, paper and libraries raise "
        "literacy itself, which by itself is the smaller of the two."
        if trade == trade_data.scholar_trade() else
        "Printing, paper, schools and academies widen the pool - they "
        "raise how many people here can read, and this ceiling rises "
        "with it.")
    return Refusal("literacy_wall", "this household's reach into the labour market for %ss "
                   "will not stretch past %.1f in total, hired and taught "
                   "together - not \"this society's literacy\" alone, which "
                   "only narrows an already-limited reach further - and you "
                   "have %.1f already (hired and still being taught). %s %s"
                   % (trade, cap, have,
                      ("%d more is the most you can take right now." % _whole)
                      if _whole >= 1 else "There is no room for even one more.",
                      lever))
