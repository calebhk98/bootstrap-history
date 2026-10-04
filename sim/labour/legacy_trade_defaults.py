"""Every trade fact the labour package still holds in code rather than reads from the trade registry.

Each table here answers a question the registry should answer, and is used only for trades whose
registry entry does not state the field (trade_data.py reads the registry first). A mod's trade is never
in these tables, so it gets the generic answer until it states the field. The engine's trade record does
not yet carry these fields (Complaints/402); when it does, each table moves into data/world/trades.json
and is deleted here. sim/tests/test_labour_core_walls.py pins this file as the only labour module that
names trades.
"""
from sim.constants import declare

LEGACY_TRADE_TABLES = declare(
    "LEGACY_TRADE_TABLES", 1, kind="temporary_heuristic", unit="marker", source=None, confidence="D",
    why="Marks the hand-written trade tables below as transitional: the registry field for each "
        "(`literate`, `taught_from`, `tool_basket`, `staff_resource`) replaces it once the engine's trade "
        "record keeps unknown fields (Complaints/402).")

# Trades whose practice is reading and writing, so the civilisation's literacy caps how many there are.
LITERATE = frozenset({"scholar", "scribe", "engineer", "chemist", "machinist", "optician", "electrician"})

# The trade a new trade is taught from when the player names none.
TAUGHT_FROM = {"machinist": "smith", "engineer": "smith", "optician": "glassblower", "chemist": "scribe"}
TAUGHT_FROM_DEFAULT = "smith"

# Materials a self-equipped worker of the trade replaces to stay in it (tools, fuel, consumables).
TOOL_BASKETS = {
    "artisan": ("timber", "iron"), "carpenter": ("timber", "iron"),
    "chemist": ("glass", "charcoal"), "electrician": ("copper",),
    "engineer": ("iron", "paper"), "engraver": ("iron",),
    "furnaceman": ("charcoal",), "glassblower": ("glass", "charcoal"),
    "machinist": ("iron",), "mason": ("stone", "timber"),
    "millwright": ("timber", "iron"), "miner": ("iron", "timber"),
    "optician": ("glass",), "plumber": ("lead",), "potter": ("clay", "charcoal"),
    "scribe": ("paper",), "smith": ("iron", "charcoal"),
}

# Generic staffing resources a concern asks for, and the trade that fills each.
STAFF_RESOURCE_TRADES = {"scholars": "scholar", "craftsmen": "artisan"}

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
