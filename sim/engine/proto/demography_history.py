"""Shock history and recovery trajectory for the `demography` screen, read from
the yearly population record the engine keeps."""

# [heuristic: what counts as a shock; a fall of this share in one year. Replace with a
# comparison against the model's own expected variation once one is measured.]
SHOCK_FALL_SHARE = 0.03
RECENT_RATE_YEARS = 5


def recent_shocks(record):
    """Years the population fell by more than the shock threshold, with the fall."""
    shocks = []
    for before, after in zip(record, record[1:]):
        if before["population"] <= 0:
            continue
        change = after["population"] / before["population"] - 1.0
        if change < -SHOCK_FALL_SHARE:
            shocks.append({"year": after["year"], "change_share": round(change, 4),
                           "deaths": after.get("deaths"),
                           "nutrition_ratio": after.get("nutrition_ratio")})
    return shocks


def recovery(record, population_now, year_now):
    """Gap to the recorded peak and, if growing, years to regain it at the recent rate."""
    if not record:
        return None
    peak = max(record, key=lambda row: (row["population"], -row["year"]))
    window = record[-(RECENT_RATE_YEARS + 1):]
    years = window[-1]["year"] - window[0]["year"]
    rate = None
    if years > 0 and window[0]["population"] > 0 and window[-1]["population"] > 0:
        rate = (window[-1]["population"] / window[0]["population"]) ** (1.0 / years) - 1.0
    to_regain = None
    if population_now >= peak["population"]:
        to_regain = 0.0
    elif rate is not None and rate > 1e-9:
        import math
        to_regain = round(math.log(peak["population"] / population_now) / math.log(1.0 + rate), 1)
    return {"peak_population": peak["population"], "peak_year": peak["year"],
            "years_since_peak": year_now - peak["year"],
            "share_below_peak": round(max(0.0, 1.0 - population_now / peak["population"]), 4),
            "recent_growth_rate": round(rate, 4) if rate is not None else None,
            "years_to_regain_peak_at_recent_rate": to_regain,
            "basis": "extrapolates the last few recorded years at a constant rate; not a forecast "
                     "of food, disease or war"}
