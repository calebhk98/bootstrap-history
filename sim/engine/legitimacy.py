"""How far the people grant the state the right to command, and what that does to what the state can do.

A work declares `mechanics.state_legitimacy = {"flat" | "per_unit" | "per_sqrt_unit": v}` (negative lowers it): a
paper that exposes officials lowers it, a paper the state licenses to print its decrees raises it. With no holder
it is exactly 1.0. The state's reach is the share of what is due that the officials it pays collect over the roads
from its seat (`sim/agents/collection.py`); its authority, what it can collect, enforce and borrow against, is that
reach times this share (`sim/engine/agents_port_budget.py`). No civilisation file states either.
"""
from sim.constants import declare

LEGITIMACY_FLOOR = declare(
    "LEGITIMACY_FLOOR", 0.5, kind="temporary_heuristic", unit="share of the state's reach", source=None,
    confidence="D",
    why="The least of its capacity a state keeps however far works have eroded the people's grant of authority: "
        "force and habit still collect something. A bound so the effect cannot null the state; its size is tuned.")
LEGITIMACY_CEILING = declare(
    "LEGITIMACY_CEILING", 1.25, kind="temporary_heuristic", unit="share of the state's reach", source=None,
    confidence="D",
    why="The most a state's reach is raised by works that win the people's consent, so that no purchase of "
        "praise makes a state stronger than a third more than its institutions alone; tuned.")


class LegitimacyMixin:

    def state_legitimacy(self):
        """The share of its reach that the people's consent leaves the state, between the floor and the ceiling."""
        return max(LEGITIMACY_FLOOR, min(LEGITIMACY_CEILING, self.effect_sum("state_legitimacy", 1.0)))

    def state_authority(self):
        """What the state can actually organise and compel: its reach, held up or worn down by consent."""
        return self.state_reach() * self.state_legitimacy()

    def state_reach(self):
        """The share of what is due that the home state's paid officials collect (Complaint 620), kept for as long as
        the year, the works held, the people and the officials' unpaid share are unchanged."""
        from .agents_port import SimWorld
        world = SimWorld(self)
        unfunded = world.government().record.unfunded.get("administration", 0.0)
        key = (self.year, self.household.done_version, self.household.operating_version, round(self.population.total), unfunded)
        memo = self.__dict__.get("_state_reach_memo")
        if memo is None or memo[0] != key:
            memo = self.__dict__["_state_reach_memo"] = (key, world.collectible_share())
        return memo[1]

    def order_reach(self):
        """The share of the home people its employed guards watch over the roads from the seat (Complaint 660)."""
        return self._staff_reach("guards", "order_share")

    def inspection_reach(self):
        """The share of the home people whose claims and workings its employed inspectors check (Complaint 660)."""
        return self._staff_reach("inspectors", "inspection_share")

    def forest_reach(self):
        """The share of the home people whose woodland tenure its employed foresters keep (Complaint 660)."""
        return self._staff_reach("foresters", "forest_share")

    def _staff_reach(self, line_name, share_name):
        from .agents_port import SimWorld
        world = SimWorld(self)
        unfunded = world.government().record.unfunded.get(line_name, 0.0)
        key = (self.year, self.household.done_version, self.household.operating_version, round(self.population.total), unfunded)
        memos = self.__dict__.setdefault("_staff_reach_memo", {})
        memo = memos.get(line_name)
        if memo is None or memo[0] != key:
            memo = memos[line_name] = (key, getattr(world, share_name)())
        return memo[1]
