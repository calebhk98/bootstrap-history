"""The arithmetic of industry experience: what the opening seeds and what each year adds, on values given."""


def opening_rates(granted, is_concern, opening, founding_years_of):
    """{technique: worker-years a year} for each concern the society already runs. A technique the opening's own
    producers run takes their worker-years; any other takes one founding-size concern's."""
    rates = {}
    for node_id in sorted(granted):
        if is_concern(node_id):
            rates[node_id] = opening.get(node_id, founding_years_of(node_id))
    return rates


def seed_stock(rate, fade):
    """The steady-state stock of a technique run at `rate` worker-years a year against a yearly fade (a fade of
    nothing is read as the whole stock fading, one a year)."""
    return rate / (fade or 1.0)


def society_worker_years(candidates, is_concern, granted, opening_rate, founding_years_of):
    """{technique: worker-years this year} of the founder's and the society's own concerns. A technique the
    society holds at the opening runs at its seeded rate; one with no seeded rate (only the founder runs it) runs
    at one founding-size concern's."""
    years = {}
    for node_id in sorted(candidates):
        if is_concern(node_id):
            seeded = opening_rate.get(node_id) if node_id in granted else None
            years[node_id] = years.get(node_id, 0.0) + (founding_years_of(node_id) if seeded is None else seeded)
    return years


def firm_worker_years(founding_years, capacity, staffed_share):
    """Worker-years a firm's concern puts in this year: a founding-size concern's, times its capacity and the
    share of it that is staffed."""
    return founding_years * capacity * staffed_share


def opening_seed(granted, is_concern, opening, founding_years_of, fade):
    """{technique: (worker-years a year, the steady-state stock they seed)} for each concern the society already runs."""
    return {node_id: (rate, seed_stock(rate, fade))
            for node_id, rate in opening_rates(granted, is_concern, opening, founding_years_of).items()}
