"""The reply of `hire`: how many were taken on of how many asked, and why fewer when fewer."""


def hire_reply(hired_count, asked, trade, you_now_employ, annual_wage_bill, paid_now, from_next_year_per_year, capital,
               outcome):
    """`outcome` is what the hire returned: a refusal carrying a cause when the search found fewer than asked."""
    reply = {"ok": True, "hired": hired_count, "trade": trade, "n": hired_count, "asked": asked,
             "you_now_employ": round(you_now_employ, 2),
             "annual_wage_bill": round(annual_wage_bill, 1),
             "paid_now": round(paid_now, 1),
             "from_next_year_per_year": round(from_next_year_per_year, 1),
             "capital": round(capital, 1)}
    if hired_count < asked:
        reply["cause"] = getattr(outcome, "cause", "search_found_fewer")
    return reply
