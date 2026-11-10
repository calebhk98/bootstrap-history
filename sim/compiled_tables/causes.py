"""Problem codes: a kernel cannot usefully build a string, so it returns a small whole number and the boundary names it.

    CAUSES = Causes(("table_full", "unknown_borrower"))     # code 0 is OK; these are codes 1 and 2
    TABLE_FULL = CAUSES.code("table_full")                  # a module constant a kernel can return
    refusal = CAUSES.refusal(code, "text", row=row)         # a sim.refusal.Refusal whose `cause` is the name

Declare the constants from the one tuple so a code and its name cannot drift apart."""
from typing import Tuple

from sim.refusal import Refusal

OK = 0


class Causes:
    """An ordered list of cause names; a name's code is its place in the list plus one."""

    def __init__(self, names: Tuple[str, ...]):
        if len(set(names)) != len(names):
            raise ValueError("a cause name is repeated")
        self.names = tuple(names)

    def code(self, name: str) -> int:
        return self.names.index(name) + 1

    def name(self, code: int) -> str:
        if code == OK:
            raise ValueError("code 0 is OK and has no cause")
        return self.names[code - 1]

    def refusal(self, code: int, text: str, **facts) -> Refusal:
        """The player-facing refusal for a code, carrying the figures (`facts`) the text states."""
        return Refusal(self.name(code), text, **facts)
