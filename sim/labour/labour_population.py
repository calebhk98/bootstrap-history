"""The local labour market: who is out there, how much of them this
household can reach.

Split out of labour.py (see that file's own docstring for why). These are
methods of Labour; they are a mixin only so that they can live in a file of
their own. 
What leaning on a trade does to its price lives in labour_market_api.py.
trade_available and found_trade_school decide whether a trade can be had here
AT ALL; market_supply, reachable_trade_population and national_trade_population
give the depth of that market, this household's reach into it, and the whole
country's total. A trade's people are the labour core's people of it (in the
tiles reached, or in the country); NO_DEMAND_TRADE_SHARE covers a trade the core
holds nobody of. The hands a hire can draw on (`hands_available`) are the core's
people of the trade in reach and last year's idle hours.
population_report and home_town_population_estimate are what the 'population'
command shows, built from the numbers above.
effective_scholars and scholar_hands_available answer "how many scholars
can this household actually put to work this year", the population-side
half of the same question hours_you_can_call_on (labour_training.py)
answers for craft hours.
"""
from sim.constants import declare, REGISTRY

from . import trade_data, trade_supply_rules
from .hands import contracted_hours_of, hands_available
from sim.ledger.api import PayEdge


class PopulationMixin:
    """The labour market this household draws on: its depth and the
    population estimates behind it -
    see this module's own docstring for why these subjects sit together.
    """


    def effective_scholars(self):
        """You are your own natural philosopher; everyone else is hired."""
        return hands_available(self._world.workforce.scholars, self._world.founder_alive, 0.0, 1.0)

    def scholar_hands_available(self):
        """Scholars you can actually put on a project this year: the ones on
        your own staff, yourself, plus the ones whose time you have already
        bought under contract.

        THE SAME FIX craft_hands_available() GOT, ARRIVING LATE. That
        function's own comment records the bug: a gate that read the payroll
        alone, so work you had already paid an outside shop to do could not
        satisfy the requirement - and the refusal's advice was to go and
        commission it. `commission` could not unblock the gate that
        recommended commission.

        It was fixed for craft trades and never extended to scholars, so the
        identical defect survived for them and was reported as
        Complaints/34: buying labourer hours works, buying SCHOLAR hours
        does nothing. Reproduced against the live protocol - a 2,000-hour
        scholar commission succeeded, took the money, and left the refusal
        byte-identical.

        A year of a scholar's time IS a scholar, for the purpose of whether
        you may attempt a thing that needs one. Buying the work rather than
        the person is the whole point of `commission`, and it is what
        somebody in this position actually did.
        """
        scholar_family = self._world.trade_family(trade_data.scholar_trade())
        contracted = contracted_hours_of(self._world.workforce.contract_hours,
                                         lambda trade: self._world.trade_family(trade) == scholar_family)
        return (self.effective_scholars()
                + contracted / self._world.HOURS_PER_PERSON_YEAR)

    def trade_available(self, trade):
        """Can this trade be had here at all, at any price?

        Rome has masons and plumbers in abundance and no machinists whatever.
        An absent trade is not expensive, it is absent, and the only way to have
        one is to teach somebody the trade yourself.
        """
        if trade not in self._world.trades_absent:
            return True
        workforce = self._world.workforce
        return (trade in workforce.trades_created
                or (workforce.trade_schools or {}).get(trade, 0.0) > 0)

    def found_trade_school(self, trade, seats):
        """Create durable local training capacity for one named trade."""
        if trade not in self._world.wages or not self.trade_available(trade):
            return False, ("the trade must exist before a school can reproduce "
                           "it; teach or discover %s first" % trade)
        seats = float(seats)
        cost = seats * self._world.trade_school_price_per_seat()
        workforce = self._world.workforce
        if seats <= 0 or cost > self._world.balance:
            return False, "cannot afford that trade school"
        self._world.send(PayEdge(self._world.EDGE_WORKERS, cost, "trade schools"))
        schools = workforce.trade_schools
        if schools is None:
            schools = workforce.trade_schools = {}
        schools[trade] = schools.get(trade, 0.0) + seats
        workforce.trades_created.add(trade)
        return True, None

    def _working_fraction(self):
        population = self._world.population
        return population.working_age / population.total if population.total > 0 else 0.0

    def _people_of_trade_in_reach(self, trade):
        """People of an ordinary trade in the tiles this household reaches by travel: the labour core's people of it
        there; where the core holds nobody of it (or has not opened), the declared floor share of the working people
        in the towns reached."""
        core = self.core_people_by_tile_and_trade()
        if core is not None:
            tiles = set(self.reachable_tiles()) | {self.base_tile()}
            people = sum(by_trade.get(trade, 0.0) for tile, by_trade in core.items() if tile in tiles)
            if people > 0.0:
                return people
        return self.reach_population_estimate() * self._working_fraction() * self.NO_DEMAND_TRADE_SHARE

    def _trade_density_source(self, trade):
        """Name of the declared constant this trade's people in reach rest on, None when it is the labour core's count or
        unavailable. Used by population_report and _density_is_placeholder to look up metadata."""
        if not self.trade_available(trade) or trade in self._world.trades_absent or trade in self.LITERATE_TRADES:
            return None
        if not (self.core_people_by_trade() or {}).get(trade):
            return "NO_DEMAND_TRADE_SHARE"
        return None

    def _density_is_placeholder(self, trade):
        """Whether a trade's population estimate is a placeholder
        (temporary_heuristic) or a cited estimate (engineering_estimate).
        Looks up the constant name in REGISTRY rather than hard-coding which
        trades are placeholders, so the answer stays consistent with the
        declaration itself.
        """
        source_name = self._trade_density_source(trade)
        if source_name is None:
            return False
        if source_name not in REGISTRY:
            return False
        return REGISTRY[source_name].get("kind") == "temporary_heuristic"

    NO_DEMAND_TRADE_SHARE = declare(
        "NO_DEMAND_TRADE_SHARE", 0.00005, kind="temporary_heuristic",
        unit="fraction of the working people", source=None,
        confidence="D", retire="Complaints/964: people by trade are the labour core's; this floor stands in only where the core holds nobody of a trade or has not opened",
        why="Share of the working people who practise a trade the labour core holds nobody of (or "
            "before the core opens): a few people always do. An order-of-magnitude placeholder.")

    TAUGHT_TRADE_SUPPLY_MULTIPLIER = declare(
        "TAUGHT_TRADE_SUPPLY_MULTIPLIER", 1.5, kind="temporary_heuristic",
        unit="dimensionless multiplier on your own employees' hours",
        source=None, confidence="D",
        why="For a trade this society had no word for until you taught it "
            "(TRADES_ABSENT), the market this household reaches is only "
            "the people you trained plus the ones they have since trained "
            "themselves - approximated as half again your own headcount's "
            "hours, standing in for that second generation, rather than "
            "modelling who-taught-whom explicitly.")
    def market_supply(self, trade):
        """Hours a year of this trade the labour core offers, as a read-only view: the core's people of it in the tiles
        reached (the literate trades: the literacy ceiling's people), less the firms' and governments' staff, plus the
        places of the trade schools. A trade only the founder teaches has the people taught."""
        if not self.trade_available(trade):
            return 0.0
        hours_per_person = self._world.HOURS_PER_PERSON_YEAR
        school_hours = (self._world.workforce.trade_schools or {}).get(trade, 0.0) * hours_per_person
        if trade in self._world.trades_absent:
            return max(0.0, self._taught_trade_people(trade) - self._world.actor_staff_fte(trade)) * hours_per_person
        people = self.literate_capacity(trade) if trade in self.LITERATE_TRADES else self._people_of_trade_in_reach(trade)
        hours = max(0.0, people - self._world.actor_staff_fte(trade)) * hours_per_person + school_hours
        return trade_supply_rules.supply_hours(hours, self.people_who_exist(trade), hours_per_person)

    def market_hours_offered(self):
        """Hours a year the labour core offers across every trade the seat can hire (market_supply summed): what projects'
        hired labour may draw on in a year."""
        return sum(self.market_supply(trade) for trade in sorted(self._world.wages))

    def reachable_trade_population(self, trade):
        """What this household's own labour market actually holds of this
        trade, your own employees included - the 'population' command's
        "within your reach" column; see national_trade_population for the
        other half of the same question.

        scholar and scribe read literate_capacity() INSTEAD OF market_
        supply(): that is the real wall hire() and train() enforce for
        them (see _literate_wall_refusal - "this household's reach into
        the labour market for %ss will not stretch past %.1f"), floored
        at 1.5 so a literate person always exists somewhere, which market_
        supply's own formula is not floored to. Showing the smaller,
        unfloored market_supply figure here would make Norse scribes read
        as "0.2 within your reach" when the game will in fact let a
        player hire one - exactly the kind of false "nobody's there"
        reading literate_capacity's own floor exists to prevent.
        """
        if trade_data.literate_trades(trade_data.registry_of(self._world), (trade,)):
            return self.literate_capacity(trade)
        return self.market_supply(trade) / self._world.HOURS_PER_PERSON_YEAR

    def taught_trade_people(self, trade):
        """People in a trade only the founder teaches (see `_taught_trade_people`); what firms draw on too."""
        return self._taught_trade_people(trade)

    def _taught_trade_people(self, trade):
        """People in a trade only you teach: your staff, their own students
        (approximated as a multiple of your headcount) and school places."""
        workforce = self._world.workforce
        return (self.employed(trade) * self.TAUGHT_TRADE_SUPPLY_MULTIPLIER
                + (workforce.trade_schools or {}).get(trade, 0.0))

    def hands_available(self, trade):
        """People of a trade a hire can draw on: the labour core's people of it in the tiles reached, or last year's idle
        hours of it if those are more; the whole working age for the unskilled pool, the people taught for a trade only
        you teach, the literacy ceiling for a literate trade."""
        if trade in self._world.trades_absent:
            return self._taught_trade_people(trade)
        if trade_data.drawn_from_unskilled_pool(trade):
            return self._world.population.working_age
        if trade in self.LITERATE_TRADES:
            return self.literate_capacity(trade)
        idle, _offered = self._world.economy.agent_idle_hours_by_trade().get(trade, (0.0, 0.0))
        return max(self._people_of_trade_in_reach(trade), idle / self._world.HOURS_PER_PERSON_YEAR)

    def people_who_exist(self, trade):
        """Hands a hire of this trade can draw on (`hands_available`), counting your own staff even if a collapse has left
        the figure below them."""
        return trade_supply_rules.people_who_exist(self.hands_available(trade), self.employed(trade))

    def available_trades(self):
        """Every trade this society has that the labour market can supply."""
        return [trade for trade in sorted(self._world.wages) if self.trade_available(trade)]

    def project_staffing_shortfall(self, node):
        """A sentence when the country lacks the people this project needs at
        once, else None. Demand is the trained heads the node asks for, and at
        least one person in every trade it draws hours from; supply is the
        people who exist in those trades."""
        trades = sorted(trade for trade, hours in (node["lab"] or {}).items()
                        if hours > 0 and trade not in self._world.trades_absent
                        and self.trade_available(trade))
        working_age = self._world.population.working_age
        craft_supply = sum(self.people_who_exist(trade) for trade in trades)
        scholar_supply = self.people_who_exist(trade_data.scholar_trade())
        empty = [trade for trade in trades if self.people_who_exist(trade) < 1.0]
        craft_need = float(node["art"])
        scholar_need = float(node["sch"])
        short = []
        if empty:
            short.append("no %s left to do the %s" % (
                "one" if len(empty) == 1 else "people",
                ", ".join(empty) + " work"))
        if craft_need > (craft_supply if trades else working_age):
            short.append("%d craftsmen against about %.1f" % (
                craft_need, craft_supply if trades else working_age))
        if scholar_need > scholar_supply:
            short.append("%d scholars against about %.1f" % (scholar_need, scholar_supply))
        if craft_need + scholar_need > working_age:
            short.append("%d workers against %.0f of working age" % (
                craft_need + scholar_need, working_age))
        if not short:
            return None
        return ("there are not enough people in this country to staff it: %s. "
                "Only about %.0f people of working age exist, and a project "
                "needing more workers than exist cannot be staffed at any price."
                % ("; ".join(short), working_age))

    def national_trade_population(self, trade):
        """How many people ply this trade across the whole country, not this household's reach: the labour core's count
        of it (nobody where the core holds nobody of it or has not opened); the working age for the unskilled pool, the
        people taught for a trade only you teach. 0.0 for a trade this society does not have (trade_available says so)."""
        if not self.trade_available(trade):
            return 0.0
        if trade_data.drawn_from_unskilled_pool(trade):
            return self._world.population.working_age   # any of the working age may be called up
        if trade in self._world.trades_absent:
            return self._taught_trade_people(trade)
        return (self.core_people_by_trade() or {}).get(trade, 0.0)

    def population_report(self):
        """Everything the 'population' command (protocol.py) shows, worked
        out here rather than in the command layer: the country's own
        numbers (population, urban_fraction - already loaded for
        pop_scale, see core.py), the size of the one town this household
        actually reaches, and - per trade - the three-way comparison that
        is the whole point of this command: how many exist in the
        country, how many are within reach, how many you employ, and what
        share of the reachable pool that is.

        This has to say both at once: a bare "market can supply 22,500
        hours" says nothing about whether that is most of the trade or a
        rounding error against it, and leaves "the labour market is the
        size of a village" unanswered.
        """
        # self.population.total (the age-cohort model) is the direct
        # answer for `pop`, not a reconstruction-by-ratio (see
        # national_trade_population's own comment, just above).
        # `reference_pop`/`scale_from_baseline` are kept as the screen's
        # own "before simulated changes" comparison, not as inputs to
        # `pop`.
        reference_pop = float(self._world.civ.get("population", 0.0))
        pop = self._world.population.total
        scale_from_baseline = (pop / reference_pop) if reference_pop else 1.0
        urban_frac = self._world.urban_fraction()
        trades = []
        for trade in sorted(self._world.wages):
            national = self.national_trade_population(trade)
            reach = self.reachable_trade_population(trade) if self.trade_available(trade) else 0.0
            have = self.employed(trade)
            trades.append({
                "trade": trade,
                "exists_here": self.trade_available(trade),
                "estimated_in_the_country": round(national, 1),
                "within_your_reach": round(reach, 2),
                "you_employ": round(have, 2),
                "share_of_the_reachable_pool_you_employ":
                    round(have / reach, 4) if reach > 1e-9 else None,
                "is_placeholder": self._density_is_placeholder(trade),
            })
        return {
            "civilisation": self._world.civ.get("short_name", self._world.civ.get("name", self._world.civ.get("id", ""))),
            "population": round(pop),
            "reference_population_before_simulated_changes": round(reference_pop),
            "population_change_from_reference": round(scale_from_baseline - 1.0, 4),
            "urban_fraction": round(urban_frac, 3),
            "urban_population_estimate": round(pop * urban_frac),
            "the_town_you_actually_operate_in": {
                "estimated_population": round(self.home_town_population_estimate()),
                "note": ("an ESTIMATE, not a place this game names: you are one "
                        "household drawing on one town's labour market, not the "
                        "whole of the country above - see what_this_means, below."),
            },
            "trades": trades,
            "what_this_means": (
                "Every hiring limit and every wage move in this game is sized "
                "to ONE household's reach into ONE town's labour market, not "
                "to the %s people counted above. A trade's 'within your "
                "reach' figure is what that market can actually supply you; "
                "'estimated in the country' is the whole civilisation's rough "
                "total, for scale. Both are explicit ESTIMATES, not a census - "
                "some trade counts are based on historical records, others are "
                "rough placeholders. Buying people (a slave, a freedman) is bounded "
                "separately, by this household's own room to feed, house and "
                "supervise them ('labour' shows that ceiling) - NOT by how "
                "deep any market runs. One thing the two columns will look "
                "like they disagree about, and do not: for a SPECIALISED "
                "trade - an engraver, a glassblower, a millwright - the "
                "reachable figure is far tighter than the country total "
                "divided by the number of towns would suggest, because a "
                "specialist does not practise in every town and the ones who "
                "do are not all for hire. The common crafts are the ones "
                "sized straight off a town's own population."
                % self._world.plain_number(pop)),
        }