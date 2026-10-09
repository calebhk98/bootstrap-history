"""How established an industry is, counted from the simulation (Complaint 111).

The stock is worker-years spent running a technique, summed over every concern that runs it (the founder's
and every firm's), and it fades each year. Depth is that stock against what a founding-size concern's own
staff would take years to master, so the same stock is deep for a small shop and shallow for a large mill.
Techniques the society runs at the opening are seeded once. Nothing is read from the tree: a technique nobody runs has no depth however old it is.

The stock shortens a concern's ramp (venture_ramp, agents_port.ramp), lowers the failure risk of a node
(effective_risk) and lifts the scale a firm can grow a concern to (sim/agents/firm_expansion.py). The labour
core keeps hours by trade but no tenure, so a worker-year here is a year of staff employed in the concern.
"""
from sim.constants import declare

from .prices import default_production_entries

EXPERIENCE_RETENTION_PER_YEAR = declare(
    "EXPERIENCE_RETENTION_PER_YEAR", 0.61, kind="temporary_heuristic",
    unit="share of the experience stock kept after one year", source="Benkard 2000, NBER w7127, section 5",
    confidence="D",
    why="Organisational experience depreciates; Benkard's aircraft programme keeps about three fifths of it "
        "after a year (0.96 a month). One plant's rate, applied to every technique until a per-trade "
        "tenure record in the labour core replaces it.")
YEARS_STAFF_TAKE_TO_MASTER = declare(
    "YEARS_STAFF_TAKE_TO_MASTER", 5.0, kind="temporary_heuristic",
    unit="years of a founding-size concern's whole staff", source=None, confidence="D",
    why="Experience equal to this many years of one founding-size concern's staff makes depth one half. "
        "Skill with a new technique is learned on the job over years (Bessen 2003, Lowell weaving), and the "
        "figure scales with the concern's own staff so it is not a per-technology value; the years are a "
        "round guess, not a measurement.")
RAMP_SHARE_AT_FULL_DEPTH = declare(
    "RAMP_SHARE_AT_FULL_DEPTH", 0.34, kind="temporary_heuristic",
    unit="share of the configured ramp years left", source=None, confidence="D",
    why="A concern opened where the technique is fully established still has to find its custom, so its ramp "
        "never vanishes; a third of the first-of-its-kind ramp is a guess at the customer-finding part.")
RISK_SHARE_AT_FULL_DEPTH = declare(
    "RISK_SHARE_AT_FULL_DEPTH", 0.5, kind="temporary_heuristic",
    unit="share of the bare node risk left", source="Levitt, List and Syverson 2013, NBER w18017",
    confidence="D",
    why="Defects halve for each tenfold of cumulative output in the car plant they studied; taken as the "
        "most that running a technique everywhere can take off a node's risk. Shares the retry learning's "
        "ground, so the two are not multiplied.")


def depth_risk_multiplier(depth):
    """Share of a node's bare risk left once its industry is this deep."""
    return 1.0 - (1.0 - RISK_SHARE_AT_FULL_DEPTH) * depth


def mastery_worker_years(founding_worker_years):
    """Worker-years that make an industry half established, for a concern of this staff."""
    return max(founding_worker_years, 1e-9) * YEARS_STAFF_TAKE_TO_MASTER


class IndustryDepthMixin:

    def industry_experience(self, node_id):
        """Retained worker-years spent running this technique, by anyone."""
        self.seed_opening_industry_experience()
        return self.state.projects.industry_years.get(node_id, 0.0)

    def seed_opening_industry_experience(self):
        """Once, from the opening's own state: each technique the society already runs (granted) starts at
        the steady state of the worker-years its opening producers employ a year against the yearly fade, as
        if it had been running long. Without an agent economy there are no opening producers, so one
        founding-size concern stands in (the scale ceiling is then off, see agents_port.scale_ceiling).
        A technique nobody runs starts at zero."""
        projects = self.state.projects
        if projects.industry_seeded or not projects.granted:
            return
        projects.industry_seeded = True
        opening = self.opening_worker_years_by_node() or {}
        for node_id in sorted(projects.granted):
            if self.is_venture(node_id):
                rate = opening.get(node_id, self.founding_worker_years(node_id))
                projects.industry_opening_rate[node_id] = rate
                projects.industry_years[node_id] = rate / (1.0 - EXPERIENCE_RETENTION_PER_YEAR)

    def opening_worker_years_by_node(self):
        """Worker-years a year the agent economy's producers put into each technique's own entries; None
        while there is no agent economy."""
        agent = self.economy.agent
        if agent is None:
            return None
        gate = {key: entry.get("requires_node") for key, entry in default_production_entries().items()}
        years = {}
        for recipe_id, worker_years in agent.worker_years_by_recipe().items():
            node_id = gate.get(recipe_id)
            if node_id is not None:
                years[node_id] = years.get(node_id, 0.0) + worker_years
        return years

    def industry_depth(self, node_id):
        """0 for a technique nobody has run, approaching 1 as it becomes established."""
        experience = self.industry_experience(node_id)
        return experience / (experience + mastery_worker_years(self.founding_worker_years(node_id)))

    def industry_scale_ceiling(self, node_id):
        """The most founding sizes one concern can be run at: one, plus the experience in masters' worth of staff."""
        return 1.0 + self.industry_experience(node_id) / mastery_worker_years(self.founding_worker_years(node_id))

    def founding_worker_years(self, node_id):
        """People of every trade one founding-size concern ties up for a year."""
        scholars, craftsmen = self.venture_hands(node_id)
        foreman_trade, foreman_fte = self.venture_foreman(node_id)
        return scholars + craftsmen + (foreman_fte if foreman_trade else 0.0)

    def concern_worker_years_this_year(self):
        """Worker-years each technique's operating concerns employed this year, the founder's and the firms'."""
        years = {}
        projects = self.state.projects
        for node_id in sorted(projects.granted | projects.operating):
            if self.is_venture(node_id):
                held_by_society = projects.industry_opening_rate.get(node_id) if node_id in projects.granted else None
                years[node_id] = years.get(node_id, 0.0) + (
                    self.founding_worker_years(node_id) if held_by_society is None else held_by_society)
        if self.state.actors is not None and self.state.actors.records:
            for firm in self.actors.active_firms():
                for node_id in firm.concerns:
                    staffed = firm.record.staffing.get(node_id, 1.0)
                    years[node_id] = (years.get(node_id, 0.0)
                                      + self.founding_worker_years(node_id) * firm.capacity_of(node_id) * staffed)
        return years

    def accrue_industry_experience(self):
        """Fade every technique's stock, then add this year's worker-years of running it."""
        stock = self.state.projects.industry_years
        for node_id in list(stock):
            stock[node_id] *= EXPERIENCE_RETENTION_PER_YEAR
        for node_id, worker_years in self.concern_worker_years_this_year().items():
            stock[node_id] = stock.get(node_id, 0.0) + worker_years
