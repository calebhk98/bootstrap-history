"""The craft-trade lists the supervision check uses."""


def craft_trades_report(trades, is_craft):
    """The trades that supervise as craft and those that do not, by the test `is_craft` applies."""
    trades = sorted(trades)
    return {"craft": [trade for trade in trades if is_craft(trade)],
            "not_craft": [trade for trade in trades if not is_craft(trade)]}
