"""The reply of `hire`: the places posted in the labour market and the staff the last clearing found."""


def hire_reply(posted, trade, you_now_employ, places_posted_in_all, annual_wage_bill, outcome):
    """`outcome` is what the hire returned (the text of what was posted)."""
    return {"ok": True, "posted": posted, "trade": trade, "n": posted,
            "you_now_employ": round(you_now_employ, 2),
            "places_posted_in_all": round(places_posted_in_all, 2),
            "annual_wage_bill": round(annual_wage_bill, 1),
            "what_happened": outcome,
            "note": "the labour market fills the places at the year's clearing and pays them from your purse at its wage"}
