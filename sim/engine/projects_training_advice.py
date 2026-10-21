"""What it costs to teach a trade nobody here can supply: the figures a refusal quotes."""


def training_advice(labour, trade_id):
    """The facts of teaching one person `trade_id`, read from the labour market.

    `hours_each` and `years` are None when no trade here can teach it."""
    source = labour._source_trade_for(trade_id)
    return {"trade": trade_id,
            "source_trade": source,
            "hours_each": labour.training_hours_per_person(trade_id, source) if source else None,
            "years": labour.training_years_from(trade_id, source) if source else None}


def training_advice_text(advice):
    """The player's wording of `training_advice`: the train command and its cost."""
    if advice["source_trade"]:
        cost = "about %.0f of your own hours each, %.1f years" % (advice["hours_each"], advice["years"])
    else:
        cost = "no trade here to teach it from"
    return '{"cmd":"train","trade":"%s","n":1} (%s)' % (advice["trade"], cost)
