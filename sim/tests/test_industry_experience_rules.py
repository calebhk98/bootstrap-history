"""What the opening seeds in each industry and what each year adds (Complaint 640): the arithmetic called on values built
here, with the labour core's tenure record, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.production.industry_depth_rules import firm_worker_years, opening_rates, opening_seed, seed_stock, society_worker_years
from sim.labour.api import add_tenure, fade_tenure, tenure_held

CONCERNS = {"mill", "forge", "kiln"}
FOUNDING = {"mill": 2.0, "forge": 3.0, "kiln": 1.0, "chapel": 4.0}


def is_concern(node_id):
    return node_id in CONCERNS


def founding(node_id):
    return FOUNDING[node_id]


# --- what the opening seeds
rates = opening_rates({"mill", "forge", "chapel"}, is_concern, {"mill": 7.5}, founding)
check("a technique the opening's producers run is seeded at their worker-years", rates["mill"] == 7.5, rates)
check("a technique nobody at the opening runs is seeded at one founding-size concern's", rates["forge"] == 3.0, rates)
check("a held technique that is not a concern is not seeded", "chapel" not in rates, rates)
check("a concern the society does not hold is not seeded", "kiln" not in rates, rates)
check("with no producers recorded every held concern takes a founding size",
      opening_rates({"mill", "kiln"}, is_concern, {}, founding) == {"mill": 2.0, "kiln": 1.0})
check("producers of a technique nobody holds seed nothing", opening_rates(set(), is_concern, {"mill": 9.0}, founding) == {})

# --- the stock the seed holds
check("the seeded stock is the yearly worker-years over the yearly fade", abs(seed_stock(6.0, 0.03) - 200.0) < 1e-9)
check("a fade of nothing reads as the whole stock fading each year", seed_stock(6.0, 0.0) == 6.0)
check("a faster fade seeds a smaller stock", seed_stock(6.0, 0.06) < seed_stock(6.0, 0.03))
plan = opening_seed({"mill", "forge", "chapel"}, is_concern, {"mill": 6.0}, founding, 0.03)
check("the opening seed pairs each held concern's yearly rate with the stock it seeds",
      sorted(plan) == ["forge", "mill"] and plan["mill"][0] == 6.0 and abs(plan["mill"][1] - 200.0) < 1e-9
      and plan["forge"] == (3.0, seed_stock(3.0, 0.03)), plan)

# --- the seeded stock holds from year to year while the producers keep running
leavers, rate = 0.04, 5.0
tenure = {}
add_tenure(tenure, "mill", {"artisan": seed_stock(rate, leavers)})
seeded = tenure_held(tenure, "mill")
for _ in range(10):
    fade_tenure(tenure, leavers)
    add_tenure(tenure, "mill", {"artisan": rate})
check("a technique the opening producers keep running holds its seeded stock from year to year",
      abs(tenure_held(tenure, "mill") - seeded) < 1e-9, (seeded, tenure_held(tenure, "mill")))
dying = {}
add_tenure(dying, "mill", {"artisan": seed_stock(rate, leavers)})
for _ in range(10):
    fade_tenure(dying, leavers)
check("with the producers gone the stock fades each year", tenure_held(dying, "mill") < seeded * 0.7, tenure_held(dying, "mill"))
check("a technique nobody runs holds no tenure", tenure_held(tenure, "kiln") == 0.0)

# --- what a year adds
held = {"mill": 7.5}
years = society_worker_years({"mill", "forge", "chapel"}, is_concern, {"mill", "forge", "chapel"}, held, founding)
check("a held concern runs at its seeded rate", years["mill"] == 7.5, years)
check("a held concern with no seeded rate runs at a founding size", years["forge"] == 3.0, years)
check("a held work that is not a concern adds nothing", "chapel" not in years, years)
years = society_worker_years({"kiln"}, is_concern, {"mill"}, held, founding)
check("a concern only the founder runs adds a founding-size concern's worker-years", years == {"kiln": 1.0}, years)
years = society_worker_years({"mill"}, is_concern, set(), held, founding)
check("a seeded rate is not used for a technique the society does not hold", years == {"mill": 2.0}, years)

# --- a firm's concern
check("a firm's concern adds a founding size times its capacity times the staffed share",
      abs(firm_worker_years(2.0, 3.0, 0.5) - 3.0) < 1e-12)
check("a firm's unstaffed concern adds nothing", firm_worker_years(2.0, 3.0, 0.0) == 0.0)
check("a larger capacity adds more", firm_worker_years(2.0, 4.0, 0.5) > firm_worker_years(2.0, 3.0, 0.5))
