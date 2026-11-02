"""The local labour market: how many people of a trade exist, how many of them this household can reach, and the
hours a year they offer."""
from sim.constants import declare

from . import trade_data, trade_supply_rules


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
        labour core's people of the trade in the tiles reached (the declared floor share of the working people where the
        core holds nobody of it) scaled by literacy, plus the small floor, plus (scholar) the people institutions train
        outright. A headcount ceiling, not an hours one; infinite for a trade that is not literate."""
        if trade not in self.trades.LITERATE_TRADES:
            return float("inf")
        cap = self.LITERATE_CAPACITY_FLOOR + self._people_of_trade_in_reach(trade) * self.trades.literacy_factor(trade)
        if trade == trade_data.scholar_trade():
            cap += self.capacity.staff_capacity()[0]
        return cap

    def _working_fraction(self):
        population = self._world.population
        return population.working_age / population.total if population.total > 0 else 0.0

    def _people_of_trade_in_reach(self, trade):
        """People of an ordinary trade in the tiles this household reaches by travel: the labour core's people of it
        there; where the core holds nobody of it (or has not opened), the declared floor share of the working people
        in the towns reached."""
        core = self.book.core_people_by_tile_and_trade()
        if core is not None:
            tiles = set(self.settlement.reachable_tiles()) | {self.settlement.base_tile()}
            people = sum(by_trade.get(trade, 0.0) for tile, by_trade in core.items() if tile in tiles)
            if people > 0.0:
                return people
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
        """Hours a year of this trade the labour core offers, as a read-only view: the core's people of it in the tiles
        reached (the literate trades: the literacy ceiling's people), less the firms' and governments' staff, plus the
        places of the trade schools. A trade only the founder teaches has the people taught."""
        if not self.trades.trade_available(trade):
            return 0.0
        hours_per_person = self._world.HOURS_PER_PERSON_YEAR
        school_hours = (self._world.workforce.trade_schools or {}).get(trade, 0.0) * hours_per_person
        if trade in self._world.trades_absent:
            return max(0.0, self._taught_trade_people(trade) - self._world.actor_staff_fte(trade)) * hours_per_person
        people = self.literate_capacity(trade) if trade in self.trades.LITERATE_TRADES else self._people_of_trade_in_reach(trade)
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
        return (self.book.employed(trade) * self.TAUGHT_TRADE_SUPPLY_MULTIPLIER
                + (workforce.trade_schools or {}).get(trade, 0.0))

    def hands_available(self, trade):
        """People of a trade a hire can draw on: the labour core's people of it in the tiles reached, or last year's idle
        hours of it if those are more; the whole working age for the unskilled pool, the people taught for a trade only
        you teach, the literacy ceiling for a literate trade."""
        if trade in self._world.trades_absent:
            return self._taught_trade_people(trade)
        if trade_data.drawn_from_unskilled_pool(trade):
            return self._world.population.working_age
        if trade in self.trades.LITERATE_TRADES:
            return self.literate_capacity(trade)
        idle, _offered = self._world.economy.agent_idle_hours_by_trade().get(trade, (0.0, 0.0))
        return max(self._people_of_trade_in_reach(trade), idle / self._world.HOURS_PER_PERSON_YEAR)

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
                        if hours > 0 and trade not in self._world.trades_absent
                        and self.trades.trade_available(trade))
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
        if not self.trades.trade_available(trade):
            return 0.0
        if trade_data.drawn_from_unskilled_pool(trade):
            return self._world.population.working_age   # any of the working age may be called up
        if trade in self._world.trades_absent:
            return self._taught_trade_people(trade)
        return (self.book.core_people_by_trade() or {}).get(trade, 0.0)
