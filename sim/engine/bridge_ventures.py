"""Bridge entries the ventures module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code did, and is
never cached. Each command applies what the old code did inline."""
from sim.ventures.needed_commands import BumpInstitutionUnitsVersion

from .bridge import bridge_command, bridge_view


@bridge_view("unskilled_trade")
def unskilled_trade(sim):
    """The registry's flagged fallback trade: the one anyone can take up at once."""
    return sim.labour.unskilled_trade()


@bridge_command(BumpInstitutionUnitsVersion)
def bump_institution_units_version(sim, command):
    sim.household.bump_institution_units_version()
