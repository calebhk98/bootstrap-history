"""How established an industry is, counted from the simulation (Complaint 111).

The stock is tenure: worker-years each trade has spent running a technique, summed over every concern that
runs it (the founder's and every firm's) and held in the labour core (sim/labour/tenure.py). It fades as
people leave work (the demography's death and retirement rate) and as they leave the trade. Depth is that
stock against what a founding-size concern's own staff would take years to master, so the same stock is deep
for a small shop and shallow for a large mill. Techniques the society runs at the opening are seeded once.
Nothing is read from the tree: a technique nobody runs has no depth however old it is.

Depth shortens a concern's ramp (venture_ramp, agents_port.ramp), lowers the failure risk of a node
(effective_risk; a diagnosed failed attempt adds its staff's worker-years to the stock), lifts the scale a
firm can grow a concern to (sim/agents/firm_expansion.py) and frees a concern of its founder once its staff
hold a year's running in it (venture_hands). industry_learning.py turns the same stock into scrap, labour
per unit, plant repair and input supply.
"""
from contextlib import contextmanager

from sim.constants import declare
from sim.labour.api import add_tenure, fade_tenure, outflow_shares, tenure_by_trade, tenure_held
from sim.world.demography_turnover import working_age_turnover

from .prices import default_production_entries

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
        "most that running a technique everywhere can take off a node's risk. A diagnosed failed attempt "
        "adds to the same stock, so failing and being established are one lesson.")


def depth_risk_multiplier(depth):
    """Share of a node's bare risk left once its industry is this deep."""
    return 1.0 - (1.0 - RISK_SHARE_AT_FULL_DEPTH) * depth


def mastery_worker_years(founding_worker_years):
    """Worker-years that make an industry half established, for a concern of this staff."""
    return max(founding_worker_years, 1e-9) * YEARS_STAFF_TAKE_TO_MASTER


class IndustryDepthMixin:

    def industry_tenure(self):
        """The society's tenure, {trade: {technique: worker-years}} (labour core record)."""
        return self.state.projects.tenure

    def tenure_leavers_share(self):
        """Share of working people who leave work in a year, from the demography."""
        return working_age_turnover(self.population)[1]

    def industry_experience(self, node_id):
        """Retained worker-years spent running this technique, by anyone."""
        self.seed_opening_industry_experience()
        return tenure_held(self.industry_tenure(), node_id)

    def industry_tenure_by_trade(self, node_id):
        self.seed_opening_industry_experience()
        return tenure_by_trade(self.industry_tenure(), node_id)

    def founding_staff_by_trade(self, node_id):
        """People of each trade one founding-size concern ties up for a year (founder-staffed)."""
        scholars, craftsmen = self.venture_hands_founder_staffed(node_id)
        foreman_trade, foreman_fte = self.venture_foreman(node_id)
        staff = {"scholar": scholars, "artisan": craftsmen}
        if foreman_trade:
            staff[foreman_trade] = staff.get(foreman_trade, 0.0) + foreman_fte
        return {trade: people for trade, people in staff.items() if people > 0.0}

    def attempt_worker_years_by_trade(self, node_id):
        """Worker-years of each trade one attempt at the node's project takes (its person-hours)."""
        node = self.nodes[node_id]
        hours = {trade: hours for trade, hours in (node.get("lab") or {}).items() if hours > 0.0}
        if not hours and node.get("ph", 0.0) > 0.0:
            hours = {"artisan": node["ph"]}
        return {trade: each / self.HOURS_PER_PERSON_YEAR for trade, each in hours.items()}

    def founding_worker_years(self, node_id):
        """People of every trade one founding-size concern ties up for a year; for a project that no
        concern runs, the worker-years of one attempt at it."""
        staff = sum(self.founding_staff_by_trade(node_id).values())
        return staff if staff > 0.0 else sum(self.attempt_worker_years_by_trade(node_id).values())

    def add_industry_years(self, node_id, worker_years):
        """Put worker-years of running a technique into the stock, split by the hours each trade works in the concern."""
        weights = self.tenure_weights(node_id)
        total = sum(weights.values())
        if total <= 0.0:
            return
        add_tenure(self.industry_tenure(), node_id, {trade: worker_years * hours / total for trade, hours in weights.items()})

    def concern_runs_without_founder(self, node_id):
        """Whether the tenure the trades hold in the technique reaches the founding staff's hours for one
        year of running it: then the concern runs without its founder."""
        needed = sum(self.founding_staff_by_trade(node_id).values())
        return needed > 0.0 and self.industry_experience(node_id) >= needed

    def seed_opening_industry_experience(self):
        """Once, from the opening's own state: each technique the society already runs (granted) starts at
        the steady state of the worker-years its opening producers employ a year against the yearly fade, as
        if it had been running long. A technique no opening producer runs gets one founding-size concern's
        worker-years."""
        projects = self.state.projects
        if projects.industry_seeded or not projects.granted:
            return
        projects.industry_seeded = True
        opening = self.opening_worker_years_by_node() or {}
        fade = self.tenure_leavers_share() or 1.0
        for node_id in sorted(projects.granted):
            if self.is_venture(node_id):
                rate = opening.get(node_id, self.founding_worker_years(node_id))
                projects.industry_opening_rate[node_id] = rate
                self.add_industry_years(node_id, rate / fade)

    def opening_worker_years_by_node(self):
        """Worker-years a year the agent economy's producers put into each technique's own entries; None
        while the economy opens."""
        by_recipe = self.economy.agent_worker_years_by_recipe()
        if by_recipe is None:
            return None
        gate = {key: entry.get("requires_node") for key, entry in default_production_entries().items()}
        years = {}
        for recipe_id, worker_years in by_recipe.items():
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

    def learn_from_failed_attempt(self, node_id):
        """A diagnosed failure is the worker-years its attempt spent on the technique, and stays in the stock."""
        add_tenure(self.industry_tenure(), node_id, self.attempt_worker_years_by_trade(node_id))

    @contextmanager
    def after_failed_attempts(self, node_id, count):
        """The stock as it would stand after `count` more diagnosed failures, for quoting odds; restored on exit."""
        tenure = self.industry_tenure()
        saved = {trade: dict(held) for trade, held in tenure.items()}
        try:
            for _ in range(count):
                self.learn_from_failed_attempt(node_id)
            yield
        finally:
            tenure.clear()
            tenure.update(saved)

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

    def fade_industry_tenure(self):
        """Keep what stays: people who neither left work nor left the trade (they carry nothing)."""
        projects = self.state.projects
        leavers = self.tenure_leavers_share()
        trades = sorted(self.industry_tenure())
        counts = {trade: self.labour.people_who_exist(trade) for trade in trades}
        outflow = outflow_shares(projects.tenure_headcount, counts, leavers)
        fade_tenure(self.industry_tenure(), leavers, outflow)
        projects.tenure_headcount = counts

    def accrue_industry_experience(self):
        """Fade every trade's tenure, then add this year's worker-years of running each technique."""
        self.seed_opening_industry_experience()
        self.fade_industry_tenure()
        for node_id, worker_years in self.concern_worker_years_this_year().items():
            self.add_industry_years(node_id, worker_years)
