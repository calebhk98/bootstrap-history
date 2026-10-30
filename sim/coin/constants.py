"""The declared numbers of the coin module."""
from sim.agents.api import edges
from sim.constants import declare

REVALUATION_YEARLY_SHARE = declare(
    "REVALUATION_YEARLY_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of the gap between the coin metal's recorded and measured value closed in a year",
    source=None, confidence="D",
    why="Coin is a stock: its value follows the metal's price as holders and mints reprice, not at once. "
        "Damping also keeps one year's market noise out of the price level. Mint behaviour would replace it.")

REVALUATION_YEARLY_CAP = declare(
    "REVALUATION_YEARLY_CAP", 1.25, kind="temporary_heuristic",
    unit="largest factor the coin's recorded value moves by in a year, either way", source=None, confidence="D",
    why="A safeguard: a mismeasured year cannot send the price level far. A mint's and holders' repricing "
        "speed would replace it.")

COIN_GUARD_HOURS_PER_TONNE_YEAR = declare(
    "COIN_GUARD_HOURS_PER_TONNE_YEAR", 60.0, kind="temporary_heuristic",
    unit="labour hours per tonne of coin per year", source=None, confidence="D",
    why="Watch-keeping and strongroom upkeep for a hoard, by its mass. Stands in for a vault built "
        "from stone, doors and a guard roster (a vault has no model yet), and is not measured. "
        "The household's purse is charged it each year.")

KEEPING_PAY_TRADE = "labourer"  # the pay that scales a foreign country's guards against the home guards
KEEPING_CAUSE = edges.EDGE_COIN_GUARDS  # paid to the guards, people in the economy
KEEPING_BASIS = ("guard hours per tonne of coin per year, a labelled heuristic "
                 "(COIN_GUARD_HOURS_PER_TONNE_YEAR), at the unskilled hour")

CARRIAGE_CAUSE = "coin carriage"
CREDIT_PURPOSES = frozenset({"interest", "loan", "loan repayment"})  # claims on a debtor: no coin changes hands
THEFT_CAUSE = "theft"
GUARDED_KINDS = ("coin",)   # coin is guarded by the keeping cost already charged; stock is watched by nobody
