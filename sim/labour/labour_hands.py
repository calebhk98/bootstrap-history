"""The hands and hours a project can draw on this year: scholars, craftsmen, the hours of a trade, and what a
technology makes an hour worth once bought."""
from sim.constants import declare

from . import trade_data
from .hands import contracted_hours_of, hands_available
from sim.workforce.api import ONCE_COMMISSION


class Hands:
    def __init__(self, world, supply, trades):
        self._world = world
        self.supply = supply
        self.trades = trades

    def effective_scholars(self):
        """You are your own natural philosopher; everyone else is hired."""
        return hands_available(self._world.workforce.scholars, self._world.founder_alive, 0.0, 1.0)

    def scholar_hands_available(self):
        """Scholars you can actually put on a project this year: your staff, yourself, and a scholar for every year of
        scholar hours you have bought, delivered or still on order (the one rule `_hands_with_commissioned` states)."""
        scholar_family = self._world.trades.trade_family(trade_data.scholar_trade())
        return self._hands_with_commissioned(self._world.workforce.scholars,
                                             lambda trade: self._world.trades.trade_family(trade) == scholar_family)

    def wage_fallback_trade(self):
        """The trade a founder with no work sells his hours in: the scholar trade once he has a scholar's hands to spare, else
        the trade the registry says a scholar is taught from."""
        if self.effective_scholars() >= 1:
            return trade_data.scholar_trade()
        return trade_data.taught_from(trade_data.registry_of(self._world), trade_data.scholar_trade())

    def _hands_with_commissioned(self, staff, counts_trade):
        """Staff on the payroll, the founder while alive, and a person for every full year of commissioned hours in the
        trades `counts_trade` accepts. A year of a trade's time is a person of it for whether a thing that needs one may
        be attempted, and buying a job rather than a person is the point of `commission`, so a gate that read the payroll
        alone could not be unblocked by the advice to commission."""
        return hands_available(staff, self._world.founder_alive,
                               contracted_hours_of(self.commissioned_hours(), counts_trade),
                               self._world.trades.HOURS_PER_PERSON_YEAR)

    # ---- a technology can make the SAME worker do more, without replacing
    # them ------------------------------------------------------------------
    # THE SECOND QUESTION: everything market_supply() and the labour market pressure
    # model is about how many HOURS a trade can supply and what hiring more
    # of them costs; neither asks an hour, once bought, to be worth more
    # than any other hour of the same trade. A flying shuttle does not hire
    # a second weaver or replace the first one - the tree's own note on
    # tex_flying_shuttle says so ("one weaver now handles wide looms...
    # triples weaving speed"). This is what represents that: a real
    # technology effect the hiring/hours mechanism alone cannot capture.
    #
    # WIRED TO NODES THAT ARE ALREADY IN THE TREE, each cited from its own
    # note, not invented for this. Deliberately conservative and deliberately
    # narrow: only nodes whose own note describes making an existing trade's
    # hour do more work, not nodes that reduce how many people are needed
    # (that is automation, and the tree already has a separate, correctly
    # different mechanism for it - see tex_power_loom in commodities.py,
    # which raises national cloth OUTPUT, not weaver PRODUCTIVITY, and is
    # deliberately left out of this table). The bonus for each node is a
    # fraction of what its own note claims, because these numbers compound
    # with one another and with everything else in the economy, and a
    # technology tree with forty of these stacked at face value would make
    # the whole game about which order you build them in rather than what
    # they cost.
    #
    # (node, trade, bonus). Sourced, node by node:
    #   tex_treadle_loom    "speeds weaving noticeably" - the weakest claim in
    #                       the chain (the note itself says the weaver still
    #                       works the shuttle by hand), so the smallest bonus.
    #   tex_flying_shuttle  "triples weaving speed" - but weaving is a slice
    #                       of what the `artisan` trade covers in this model
    #                       (there is no dedicated weaver trade), so the
    #                       tripling is scaled down hard rather than applied
    #                       to the whole trade.
    #   tex_spinning_wheel  "roughly tripling output per spinner" - same
    #                       dilution reasoning as the shuttle.
    #   met_trip_hammer     "much faster than hand hammering... foundation of
    #                       heavy forge work" - smith.
    #   met_water_ore_stamp "crush ore... far faster than hand crushing" -
    #                       miner, who does the crushing this replaces.
    #   met_three_high_mill "doubles throughput" of a rolling mill - smith.
    #   met_converter_furnace "speed and low labour cost per ton is the
    #                       payoff" - furnaceman.
    #   bellows_water_blown "the single highest-leverage mechanical change
    #                       available... continuous high-volume blast" - a
    #                       non-automating speed-up; furnaceman.
    #   mfg_rake_clearance  "saves 30 percent power and doubles tool life" -
    #                       machinist.
    #   mfg_hss_development "cuts three times faster than Mushet steel" - the
    #                       most direct per-hour claim of the set; machinist.
    #   prc_capstan_turret_lathe "unskilled operator can repeat production" -
    #                       still an operator, still a machinist, just a much
    #                       faster one per hour; machinist.
    # LABOUR_PRODUCTIVITY_SOURCES: [(node, trade, bonus)] from each node's `labour_productivity`, as the mechanics module's view gives them.
    # NEVER MORE THAN HALF AGAIN, however many of the above a run has built.
    # Every other saturating multiplier in this file (labour market price_factor,
    # literacy_factor) is capped for the same reason: an uncapped sum of
    # small, individually-defensible bonuses is still an uncapped sum, and
    # this compounds with hired_cap, market_supply's own institutional
    # multipliers, and the project pacing built on top of both.
    LABOUR_PRODUCTIVITY_CAP = declare(
        "LABOUR_PRODUCTIVITY_CAP", 1.5, kind="temporary_heuristic",
        unit="dimensionless multiplier", source=None, confidence="D",
        why="However many productivity-raising technologies a run has "
            "built, no trade's hour may be worth more than half again its "
            "base value. Every other saturating multiplier in this file "
            "(labour market price_factor, literacy_factor) is capped for the "
            "same reason: an uncapped sum of small, individually-"
            "defensible bonuses is still an uncapped sum, and this "
            "compounds with hired_cap and market_supply's own "
            "institutional multipliers. The cap value itself is tuned, "
            "not derived from any real productivity ceiling.")

    def labour_productivity(self, trade):
        """How much MORE a real hour of this trade is worth this year, from
        technology that makes the worker faster rather than replacing them.

        1.0 with nothing built (an hour is an hour, exactly the old
        behaviour). Multiplies the HOURS a project can draw, in
        hours_you_can_call_on - not market_supply, and not the wage bill: the
        workforce is not bigger and is not paid differently, it simply gets
        more done. See LABOUR_PRODUCTIVITY_SOURCES for what is wired in and
        why each figure is what it is.
        """
        bonus = 0.0
        projects = self._world.projects
        for node, row_trade, add in self._world.knowledge.LABOUR_PRODUCTIVITY_SOURCES:
            if row_trade == trade and node in projects.done:
                bonus += add
        productivity = min(self.LABOUR_PRODUCTIVITY_CAP, 1.0 + bonus)
        if trade == trade_data.scholar_trade():
            productivity *= self._world.knowledge.research_productivity()
        return productivity

    def hours_you_can_call_on(self, trade):
        """Hours of this trade a project can actually draw on this year.

        COMMISSIONED HOURS ARE PART OF THE CEILING, NOT ON TOP OF IT: a
        commission buys a job from somebody else's shop, but it is the same
        scribes drawing on the same local pool market_supply already
        bounds, not a second pool stacked on top of it. What it really buys
        is certainty: hours reserved for your work rather than competed
        for.
        """
        # TWO CHANNELS, AND BOTH HAVE TO BE SAID. Hiring draws on the people
        # who live here, and that pool is what market_supply bounds. A
        # commission is a job placed with somebody else's shop, and a shop
        # subcontracts: it is a second channel, dearer per hour, bounded in
        # turn by what the local trade can spare (see commission()).
        # Collapsing the two into one indistinguishable pool would make
        # commissioning pointless, since it would just be spending money to
        # buy the same hours market_supply already counts. Two channels,
        # each bounded, each named wherever the number is printed.
        #
        # PRODUCTIVITY MULTIPLIES THE RESULT, NOT market_supply ITSELF. This
        # is what turns "the same crew gets more done" into "the market can
        # supply more people" if it were applied upstream instead - the wall
        # a project's labour draw actually runs into is how much WORK gets
        # out of the hours it can call on, which is this number, not how
        # many people the town could in principle hire (market_supply, still
        # unchanged, still governs hiring capacity and labour market price_factor).
        return ((self.supply.market_supply(trade) + self._world.workforce.contract_hours.get(trade, 0.0))
                * self.labour_productivity(trade))

    def commissioned_hours(self):
        """{trade: hours} bought from outside shops: the contracts the clearing delivered and the orders it has not yet filled."""
        workforce = self._world.workforce
        hours = dict(workforce.contract_hours)
        for trade, ordered in workforce.hours_wanted_once.get(ONCE_COMMISSION, {}).items():
            hours[trade] = hours.get(trade, 0.0) + ordered
        return hours

    def hours_reserved(self, trade):
        """Hours of this trade you have already bought from an outside shop."""
        return self.commissioned_hours().get(trade, 0.0)

    def craft_hands_available(self):
        """Craftsmen you can actually put on a job this year: your staff, yourself, and a craftsman for every year of craft
        hours you have bought (the one rule `_hands_with_commissioned` states)."""
        return self._hands_with_commissioned(self._world.workforce.artisans, self.trades.is_craft_trade)
