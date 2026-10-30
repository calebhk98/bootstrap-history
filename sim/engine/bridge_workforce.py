"""The workforce module's labour implementation, for tests and mods that still call its members (no engine or UI code reads it)."""
from .bridge import bridge_view


@bridge_view("legacy_labour")
def legacy_labour(sim):
    """The workforce module's labour implementation."""
    return sim.assembly.modules["workforce"].labour
