"""How far the people grant the state the right to command, and what that does to what the state can do.

A work declares `mechanics.state_legitimacy = {"flat" | "per_unit" | "per_sqrt_unit": v}` (negative lowers it): a
paper that exposes officials lowers it, a paper the state licenses to print its decrees raises it. With no holder
it is exactly 1.0. The state's authority, which is what its officials can collect, enforce and borrow against, is its
capacity times this share (`sim/engine/agents_port_budget.py`).
"""
from sim.constants import declare

LEGITIMACY_FLOOR = declare(
    "LEGITIMACY_FLOOR", 0.5, kind="temporary_heuristic", unit="share of the state's capacity", source=None,
    confidence="D",
    why="The least of its capacity a state keeps however far works have eroded the people's grant of authority: "
        "force and habit still collect something. A bound so the effect cannot null the state; its size is tuned.")
LEGITIMACY_CEILING = declare(
    "LEGITIMACY_CEILING", 1.25, kind="temporary_heuristic", unit="share of the state's capacity", source=None,
    confidence="D",
    why="The most a state's capacity is raised by works that win the people's consent, so that no purchase of "
        "praise makes a state stronger than a third more than its institutions alone; tuned.")


class LegitimacyMixin:

    def state_legitimacy(self):
        """The share of its capacity that the people's consent leaves the state, between the floor and the ceiling."""
        return max(LEGITIMACY_FLOOR, min(LEGITIMACY_CEILING, self.effect_sum("state_legitimacy", 1.0)))

    def state_authority(self):
        """What the state can actually organise and compel: its capacity, held up or worn down by consent."""
        return self.state_capacity * self.state_legitimacy()
