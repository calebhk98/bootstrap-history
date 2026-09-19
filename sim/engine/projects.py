"""Starting, stopping, finishing and abandoning a piece of work.

These are methods of Sim; they are a mixin only so that they can live in
a file of their own.

This file is a pure composition point, in the shape sim/engine/society.py
and sim/engine/economy.py already establish for the same reason: one file
holding all of a household's project mechanics becomes a file nobody can
edit without colliding with everyone else touching them, so the 46
methods live in six sibling modules, grouped by subject rather than by
size, and this file's only job is to compose them back into the single
ProjectsMixin sim/engine/core.py's `class Sim(...)` already expects,
unchanged, to inherit from:

    projects_capability.py  is_venture/running/institution_units and the
                             rest of what a capability or scalable
                             institution IS, built and scaled and still
                             running (CapabilityMixin)
    projects_ventures.py    the cost and staff of a venture, and the two
                             player-typed verbs that open or close one by
                             hand (VenturesMixin)
    projects_staffing.py    the automatic, year-by-year counterpart of
                             those two verbs - closing what staffing can no
                             longer cover, reopening it, warning first, and
                             auto-opening what plainly pays - plus
                             mothballing and restoring a completed work
                             (StaffingMixin)
    projects_starting.py    whether a project may begin (start_reason,
                             can_start), the money-for-progress levers and
                             substitution rule that change that answer
                             (bribe, bounty, substitution_quality), and
                             starting/stopping one (StartingMixin)
    projects_progress.py    what happens to an ACTIVE project every further
                             year: hired-labour hours, failure risk, and
                             calendar time (ProgressMixin)
    projects_completion.py  what finishing (or failing) a project actually
                             does, and the hazard-mitigation table that
                             lists which finished technologies blunt which
                             hazard (CompletionMixin)

No method appears in more than one of the six; see each module's own
docstring for exactly which methods it holds and why they sit together.

A handful of constants (CAPABILITY_INSTITUTIONS, SCALABLE_INSTITUTIONS,
FOUNDER_IS_WORTH, STARTER_FOUNDING_MIN_UNITS, STAFF_CLOSURE_DISCOUNT,
STAFF_CLOSURE_GRACE, RESTORE_COST_SHARE_OF_BUILD) are genuinely read from
more than one of the six sub-mixins - CAPABILITY_INSTITUTIONS and
SCALABLE_INSTITUTIONS from projects_capability.py, projects_ventures.py and
projects_staffing.py; the other five across whichever two of projects_
ventures.py/projects_staffing.py/projects_starting.py actually share them;
see each constant's own comment for the specific pair. Moving any one of
them into a single sub-mixin would leave the others reaching across module
boundaries for a constant that isn't theirs, the same reasoning economy.py
already gives for keeping its own cross-cutting constants on ITS
composition point rather than in one of ITS four sub-mixins - so these stay
here, on the composition point all six inherit from, instead.
"""
from .projects_capability import CapabilityMixin
from .projects_ventures import VenturesMixin
from .projects_staffing import StaffingMixin
from .projects_starting import StartingMixin
from .projects_progress import ProgressMixin
from .projects_completion import CompletionMixin
from constants import declare


class ProjectsMixin(CapabilityMixin, VenturesMixin, StaffingMixin,
                     StartingMixin, ProgressMixin, CompletionMixin):
    """Composition point only: every method below is defined in one of the
    six sibling modules above, not here - what IS defined directly here is
    the handful of constants read from more than one of them (see this
    file's own module docstring for which, and why). sim/engine/core.py's
    `class Sim(..., ProjectsMixin, ...)` keeps working unmodified: Sim, and
    everything that calls a project method on it, neither knows nor needs
    to know that the 46 methods it sees on ProjectsMixin are spread across
    six files rather than gathered in one.
    """

    # Concerns whose whole point is what they let you DO - scholars a school
    # supports, household places a workshop adds, credit a patron's name
    # unlocks, knowledge a corpus preserves - as opposed to what they take at
    # the door. Every one of these is gated through running() somewhere in this
    # engine, and several of them lose money outright, so the margin test in
    # auto_open_ventures would leave them shut for ever. Kept honest by a
    # regression check that greps the engine for running() gates and fails if
    # any node named in one is missing from this set.
    # fin_company_town and fin_chain_store joined this set together with the
    # STAFF_CAPACITY_SOURCES entries that run() -gate them (labour.py): both
    # are going concerns whose entire point is the household places they
    # support, exactly like a school or a workshop, and both run at a loss on
    # the books by design (fin_chain_store: upkeep 2,000 against revenue
    # 1,500) - the intended shape of the trade, not a mistake to be flagged
    # the way an ordinary money-losing venture is. fin_societas and
    # fin_trial_balance are NOT here: neither has any revenue or upkeep of
    # its own (is_venture() is false for both), so neither is ever opened,
    # closed, or capable of losing money - there is nothing for this set to
    # protect.
    CAPABILITY_INSTITUTIONS = frozenset((
        "academy_network", "blast_furnace", "collegium_licensed",
        "corpus_dispersed", "corpus_written", "crucible_steel",
        "endowment_land", "exp_trade_route_extend", "fin_argentarii",
        "fin_chain_store", "fin_company_town", "fin_university",
        "freedman_staff", "identity_cover",
        "interchangeable_parts", "patron_imperial", "patron_local",
        "patron_senatorial", "plague_preparedness", "power_grid", "railway",
        "sanitation_antisepsis", "school_founded", "steam_high_pressure",
        "telegraph_electric", "workshop_first"))
    # ---- AN INSTITUTION IS A QUANTITY, WHERE A SECOND ONE MEANS ANYTHING --
    # "Can you have multiple things? What if I wanted to raise literacy to
    # 90%+, and wanted to open 5,000 schools?" is the question that exposed
    # the asymmetry running()'s own parked comment names: a mine is
    # open_mine(material, tonnes_per_year) and a forest is forest_ha, both
    # quantities you sink more into as the money and the people to staff them
    # turn up, while school_founded, workshop_first and their kind are one
    # boolean, ever, however rich or literate the household becomes.
    #
    # Not every CAPABILITY_INSTITUTIONS entry gets this. A patronage
    # (patron_local/senatorial/imperial) is one man's opinion of you, not a
    # building - "five imperial patrons" is not a richer version of one, it is
    # nonsense. A singular achievement (endowment_land, corpus_written,
    # sanitation_antisepsis, identity_cover, the heavy-industry techniques)
    # is a state the whole household is in, not a count of sites. What a
    # school, a workshop, a licensed collegium, an academy and a freedman
    # staff have that those do not is exactly the thing the parked comment
    # points at: each is a PLACE that supports a number of people
    # (institution_places, economy.py), and a second school built across town
    # supports more people for a reason a second emperor's goodwill does not.
    # fin_chain_store joined this set for the same reason school_founded is
    # in it: "a second school built across town" IS the model this node's own
    # note already describes ("operates identical stores in multiple
    # cities"), a second unit is simply a second town rather than a second
    # schoolroom. It falls through to this function's own generic ceiling
    # below (population, not literacy - a branch network draws on merchants
    # and clerks, not the lettered few a second academy needs), so nothing
    # else here had to change to seat it.
    SCALABLE_INSTITUTIONS = frozenset((
        "workshop_first", "school_founded", "academy_network",
        "freedman_staff", "collegium_licensed", "fin_chain_store"))
    # YOU ARE A PAIR OF HANDS TOO. Requiring staff for every concern, however
    # small, meant a founder with nobody could open nothing at all - not a
    # bottling shed, not an inn - and since revenue now follows what you RUN,
    # that closed the only door out of an empty household: no hands, so no
    # concern; no concern, so no income; no income, so no hands. Rome ran to
    # year 800 with 270 technologies, no craftsmen and one open concern, and
    # Norse sat solvent at 317 in hand with none. One person can keep an eye on
    # one small shop, which is exactly how every one of these fortunes started.
    FOUNDER_IS_WORTH = declare(
        "FOUNDER_IS_WORTH", 1.0, kind="temporary_heuristic",
        unit="craftsman-equivalent FTE", source=None, confidence="D",
        why="The founder counts as one ordinary pair of hands for "
            "purposes of running a small concern themselves, so an empty "
            "household is never locked out of opening its first shop (see "
            "this constant's own comment: 'no hands, so no concern; no "
            "concern, so no income; no income, so no hands'). A modelling "
            "necessity rather than a measured claim about one person's "
            "output.")
    STARTER_FOUNDING_MIN_UNITS = declare(
        "STARTER_FOUNDING_MIN_UNITS", 0.2, kind="temporary_heuristic",
        unit="units", source=None, confidence="D",
        why="The smallest a first founding of a scalable institution may "
            "be asked for - below a fifth of the ordinary size there would "
            "be nothing left standing between 'a schoolroom' and 'no "
            "school at all'. A floor on the bridge that let a founder open "
            "a place smaller than the full historically-calibrated size "
            "when they could not yet afford the whole of it (see this "
            "table's own history in running()'s docstring); tuned, not "
            "measured.")
    STAFF_CLOSURE_DISCOUNT = declare(
        "STAFF_CLOSURE_DISCOUNT", 0.1, kind="temporary_heuristic",
        unit="fraction of the full fee", source=None, confidence="D",
        why="What reopening a concern costs, within STAFF_CLOSURE_GRACE "
            "years of the staffing rule shutting it, relative to the full "
            "capex or restoration fee - the premises are still standing "
            "and the stock is still on the shelves, so only a tenth is "
            "owed, not the whole thing. Shared between open_venture and "
            "restore_work so a player is quoted the same discount from "
            "either verb. Tuned figure, not measured against any real "
            "cost of re-staffing an idle shop.")
    # Years a shop stands with its stock and its lease while you find somebody
    # to keep an eye on it. Past that it really has been given up.
    STAFF_CLOSURE_GRACE = declare(
        "STAFF_CLOSURE_GRACE", 6, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="How long a concern the staffing rule shut stands with its "
            "stock and lease intact before it counts as truly abandoned "
            "rather than merely unstaffed - past this, reopening costs "
            "the full price rather than STAFF_CLOSURE_DISCOUNT's tenth. "
            "Declared as the INT the source wrote, not 6.0: it is "
            "compared against and printed alongside self.year - _shut[k] "
            "(whole years) with %d formatting, so there is no reason to "
            "widen it to a float. Tuned game-balance window, not measured "
            "against any real reopening timeline.")
    RESTORE_COST_SHARE_OF_BUILD = declare(
        "RESTORE_COST_SHARE_OF_BUILD", 0.3, kind="temporary_heuristic",
        unit="fraction of project_cost", source=None, confidence="D",
        why="What restoring a mothballed work (or hinting at its cost in "
            "start_reason's mothball message) costs relative to building "
            "it from nothing - you already know how, so it is cheaper "
            "than starting over. Shared between restore_work and "
            "start_reason's own mothball hint so the two can never quote "
            "different figures for the same thing. Tuned discount, not "
            "measured.")
