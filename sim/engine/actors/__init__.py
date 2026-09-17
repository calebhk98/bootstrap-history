"""Economic actors: things that can own money, knowledge, staff and plant.

Today there is exactly one, `Household` - the founder and their family, as an
economic actor distinct from the world they arrived in. It exists as its own
package (rather than one more class tacked onto `sim/engine/`) because the
whole point of pulling it out of `Sim` is that a government, a firm or a
second household should be able to import the same class later without
importing the simulation engine along with it. See
`docs/architecture/HOUSEHOLD_EXTRACTION.md` for why this move happened and
`docs/architecture/SIM_STATE_INVENTORY.md` for exactly which fields it holds
and which stayed on `Sim`.
"""
from .household import Household

__all__ = ["Household"]
