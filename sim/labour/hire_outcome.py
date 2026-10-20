"""What a hire reports: how many were found of how many asked, and the craft-trade lists the supervision check uses."""
from sim.refusal import Refusal

FOUND_FEWER = "search_found_fewer"
SHORT_BY = 1e-6


def unfound_note(count, asked):
    """The sentence that says a large search found only part of the crew; empty when everyone asked for was found."""
    return (" Found %g of the %g asked for; the rest must be sought next year." % (count, asked)
            if count < asked - SHORT_BY else "")


def hire_result(text, unfound, count, asked):
    """(True, the text) for a full hire; (True, a `search_found_fewer` refusal) for a hire that found fewer than asked."""
    if unfound:
        return True, Refusal(FOUND_FEWER, text, asked=float(asked), hired=float(count))
    return True, text


def craft_trades_report(trades, is_craft):
    """The trades that supervise as craft and those that do not, by the test `is_craft` applies."""
    trades = sorted(trades)
    return {"craft": [trade for trade in trades if is_craft(trade)],
            "not_craft": [trade for trade in trades if not is_craft(trade)]}
