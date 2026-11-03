"""The local labour market: how many people of a trade exist, how many of them this household can reach, and the
hours a year they offer."""
from sim.constants import declare

from . import trade_data, trade_supply_rules
from .labour_wage_schedule import person_year_hours


class Supply:
    def __init__(self, world, book, capacity, settlement, trades):
        self._world = world
        self.book = book
        self.capacity = capacity
        self.settlement = settlement
        self.trades = trades

    LITERATE_CAPACITY_FLOOR = declare(
        "LITERATE_CAPACITY_FLOOR", 1.5, kind="temporary_heuristic",
        unit="people", source=None, confidence="D",
        why="A literate trade's hiring ceiling is ADDED to, not maxed "
            "with, this floor, so a society with almost no literate pool "
            "(Viking-age Scandinavia's rune-carvers and Latin-reading "
            "priests) still has SOMEONE findable rather than a ceiling "
            "that rounds to nobody. The rune-carver and the priest are "
            "always there; this is what makes that true numerically. "
            "Picked so the floor is real without swallowing the signal "
            "literacy_factor is supposed to carry (see this function's "
            "own docstring on why max() broke the mechanism for Norse).")

    def literate_capacity(self, trade):
        """The most people this society's literacy lets you have in a literate trade, hired and taught combined: the
        people of the trade the seat's bids reach (`_people_of_trade_in_reach`) scaled by literacy, plus the small floor, plus (scholar) the people institutions train
        outright. A headcount ceiling, not an hours one; infinite for a trade that is not literate."""
        if trade not in self.trades.LITERATE_TRADES:
            return float("inf")
        cap = self.LITERATE_CAPACITY_FLOOR + self._people_of_trade_in_reach(trade) * self.trades.literacy_factor(trade)
        if trade == trade_data.scholar_trade():
            cap += self.capacity.staff_capacity()[0]
        return cap

    def _working_fraction(self):
        population = self._world.people.population
        return population.working_age / population.total if population.total > 0 else 0.0

    def _people_of_trade_in_reach(self, trade):
        """People-equivalents of an ordinary trade the seat's bids reach: the hours the households of the base tile's labour
        area offered at the last clearing (what they keep for plot and home work is not offered) over a working year;
        where none were offered (or the core has not cleared), the declared floor share of the working people in the
        towns reached."""
        offered = self._world.economy.agent_hours_offered_at(trade, self.settlement.base_tile())
        if offered is not None and offered > 0.0:
            return offered / person_year_hours(self._world)
        return self.settlement.reach_population_estimate() * self._working_fraction() * self.NO_DEMAND_TRADE_SHARE

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
        """Hours a year of this trade the labour core offers, as a read-only view: the hours its households offer in the
        base tile's labour area (the literate trades: the literacy ceiling's people), less the firms' and governments' staff, plus the
        places of the trade schools. A trade only the founder teaches has the people taught."""
        if not self.trades.trade_available(trade):
            return 0.0
        hours_per_person = person_year_hours(self._world)
        school_hours = (self._world.workforce.trade_schools or {}).get(trade, 0.0) * hours_per_person
        if trade in self._world.trades.trades_absent:
            return max(0.0, self._taught_trade_people(trade) - self._world.actors.actor_staff_fte(trade)) * hours_per_person
        people = self.literate_capacity(trade) if trade in self.trades.LITERATE_TRADES else self._people_of_trade_in_reach(trade)
        hours = max(0.0, people - self._world.actors.actor_staff_fte(trade)) * hours_per_person + school_hours
        return trade_supply_rules.supply_hours(hours, self.people_who_exist(trade), hours_per_person)

    def market_hours_offered(self):
        """Hours a year the labour core offers across every trade the seat can hire (market_supply summed): what projects'
        hired labour may draw on in a year."""
        return sum(self.market_supply(trade) for trade in sorted(self._world.trades.wages))

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
        return self.market_supply(trade) / person_year_hours(self._world)

    def taught_trade_people(self, trade):
        """People in a trade only the founder teaches (see `_taught_trade_people`); what firms draw on too."""
        return self._taught_trade_people(trade)

    def _taught_trade_people(self, trade):
        """People in a trade only you teach: your staff, their own students
        (approximated as a multiple of your headcount) and school places."""
        workforce = self._world.workforce
        return (self.book.employed(trade) * self.TAUGHT_TRADE_SUPPLY_MULTIPLIER
                + (workforce.trade_schools or {}).get(trade, 0.0))

    def hands_available(self, trade):
        """People of a trade a hire can draw on: `_people_of_trade_in_reach`, the same figure `market_supply` offers; the whole
        working age for the unskilled pool, the people taught for a trade only
        you teach, the literacy ceiling for a literate trade."""
        if trade in self._world.trades.trades_absent:
            return self._taught_trade_people(trade)
        if trade_data.drawn_from_unskilled_pool(trade):
            return self._world.people.population.working_age
        if trade in self.trades.LITERATE_TRADES:
            return self.literate_capacity(trade)
        return self._people_of_trade_in_reach(trade)

    def people_who_exist(self, trade):
        """Hands a hire of this trade can draw on (`hands_available`), counting your own staff even if a collapse has left
        the figure below them."""
        return trade_supply_rules.people_who_exist(self.hands_available(trade), self.book.employed(trade))

    def project_staffing_shortfall(self, node):
        """A sentence when the country lacks the people this project needs at
        once, else None. Demand is the trained heads the node asks for, and at
        least one person in every trade it draws hours from; supply is the
        people who exist in those trades."""
        trades = sorted(trade for trade, hours in (node["lab"] or {}).items()
                        if hours > 0 and trade not in self._world.trades.trades_absent
                        and self.trades.trade_available(trade))
        working_age = self._world.people.population.working_age
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
        if not self.trades.trade_available(trade):
            return 0.0
        if trade_data.drawn_from_unskilled_pool(trade):
            return self._world.people.population.working_age   # any of the working age may be called up
        if trade in self._world.trades.trades_absent:
            return self._taught_trade_people(trade)
        return (self.book.core_people_by_trade() or {}).get(trade, 0.0)
