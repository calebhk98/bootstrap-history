"""A shortage that lasts is one standing condition; only a material change is news again."""

# Change in the share of planned work that still runs, from the last reported figure, that counts as new
# (presentation threshold, not a mechanism).
MATERIAL_THROUGHPUT_CHANGE = 0.10
# Smaller moves than this between years read as steady.
STEADY_BAND = 0.02


def note_shortage(sim, material, throughput):
    """Record this year's shortage; True when it deserves a fresh event.

    News is a new material, or a throughput that has moved materially since
    the last time it was reported."""
    holdings = sim.state.holdings
    condition = holdings.shortage_condition
    year = sim.state.scenario.year
    if not condition or condition["material"] != material:
        holdings.shortage_condition = {"material": material, "since": year, "reported": throughput,
                                      "previous": throughput, "latest": throughput}
        return True
    condition["previous"] = condition["latest"]
    condition["latest"] = throughput
    if abs(throughput - condition["reported"]) >= MATERIAL_THROUGHPUT_CHANGE:
        condition["reported"] = throughput
        return True
    return False


def clear_shortage(sim):
    """The shortage is over; the next one is news again."""
    sim.state.holdings.shortage_condition = None


def condition_rows(sim):
    """The standing shortage as rows for the state screen, empty when none."""
    condition = sim.state.holdings.shortage_condition
    if not condition:
        return []
    change = condition["latest"] - condition["previous"]
    trend = "improving" if change > STEADY_BAND else "worsening" if change < -STEADY_BAND else "steady"
    row = {"material": condition["material"], "throughput": condition["latest"],
           "years": max(1, sim.state.scenario.year - condition["since"] + 1), "trend": trend}
    deficit = sim.material_shortfall_t(condition["material"])
    if deficit > 0.0:
        row["deficit_tonnes_per_year"] = round(deficit, 1)
    return [row]


def condition_line(row):
    """One readable line for a standing condition."""
    parts = ["%s CONSTRAINED: work at %d%% of plan" % (row["material"].upper(), round(100 * row["throughput"]))]
    if row.get("deficit_tonnes_per_year"):
        parts.append("short %s t/year" % "{:,.1f}".format(row["deficit_tonnes_per_year"]))
    parts.append("year %d, %s" % (row["years"], row["trend"]))
    return ", ".join(parts)
