"""Scenario (Complaint 640): in a running game the market output of a herd good is a number, not a map error (Complaints/532).
The rule that a herd good names no deposit is in test_herd_stock_is_no_deposit.py."""
from .harness import *  # noqa: F401,F403

founder = sim(civ="rome_100ad", capital=1e6)
for material in ("cattle_kg", "sheep_kg", "goat_kg"):
    check("the market output of %s is a number, not a map error" % material,
          founder._national_output_tonnes(material) >= 0.0, None)
