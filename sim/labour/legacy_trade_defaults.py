"""The trade ids the labour package still names in code: roles its bookkeeping counts (scholars, generic
craftsmen, the bonded, an army under arms) rather than facts about a trade. Per-trade facts (literacy,
teacher, tools, staffing resource, fatality risk) are read from the registry in data/world/trades.json.
sim/tests/test_labour_core_walls.py pins this file as the only labour module that names trades.
"""

TAUGHT_FROM_DEFAULT = "smith"   # TRANSITIONAL heuristic: the teacher of a trade that names none

# Trades that stand for a role the household's own bookkeeping counts: scholars (research and literacy
# capacity), generic craftsmen, and the bonded who are counted apart from hired staff.
SCHOLAR_TRADE = "scholar"
GENERIC_CRAFT_TRADE = "artisan"
BONDED_PSEUDO_TRADE = "slave"

# Staff the ledger reports as interchangeable hands rather than specialists.
GENERIC_STAFF_TRADES = ("artisan", "scholar", "labourer", "slave")

# Trades whose people are drawn from the unskilled pool while they serve (an army under arms).
DRAWN_FROM_UNSKILLED_POOL = frozenset({"soldier"})

# Trades that need letters but not reading as their practice, so literacy does not cap them.
LETTERED_BUT_NOT_LITERATE = frozenset({"merchant"})

# The trade whose hours the farm-labour logic owns (its recipe hours are kept out of the non-farm
# split). It is the fallback trade of the shipped registry; workforce_spinup.py has no registry to ask.
FARM_TRADE = "labourer"

# The family whose trades count as the household's craftsmen.
CRAFT_FAMILY = "craft"
