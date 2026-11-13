"""The size below which a holding is rounding residue, not stock."""
from sim.constants import declare

STOCK_RESIDUE_UNITS = declare(
    "STOCK_RESIDUE_UNITS", 1e-9, kind="temporary_heuristic",
    unit="units of a good below which a holding is rounding residue and is removed",
    source=None, confidence="D",
    why="A stock that loses a share each year never reaches zero, and the dust left (far below any physical amount) made a "
        "market of an offer nobody could fill. The value is many orders of magnitude below the smallest real holding of any "
        "good in the data (a household's smallest ration is of the order of grams, a thousandth of a unit), so it cannot bind "
        "on a real holding; only a remainder that small after a year's loss is taken whole.",
    retire="Complaint 473: goods in whole lots, or a residue relative to the good's unit mass")
