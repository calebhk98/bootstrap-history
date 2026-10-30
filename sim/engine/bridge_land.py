"""Bridge entries the land module reads until the owners behind them move into modules.

The mods directory the game is built over (the content module is given it; Complaint 840)."""
import os

MODS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mods")
