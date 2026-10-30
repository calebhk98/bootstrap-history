"""The markets module's port over the agent economy, for engine and UI code that still reach it through the game."""
from .bridge import bridge_view


@bridge_view("legacy_economy")
def legacy_economy(sim):
    """The port over the agent economy (the markets module's `economy`)."""
    return sim.assembly.modules["markets"].economy
