"""What the 'population' command shows: the country's numbers, the town this household reaches, and per trade the
people in the country, in reach and employed."""
from sim.constants import REGISTRY



class PopulationReport:
    def __init__(self, world, book, settlement, supply, trades):
        self._world = world
        self.book = book
        self.settlement = settlement
        self.supply = supply
        self.trades = trades

    def _trade_density_source(self, trade):
        """Name of the declared constant this trade's people in reach rest on, None when it is the labour core's count or
        unavailable. Used by population_report and _density_is_placeholder to look up metadata."""
        if not self.trades.trade_available(trade) or trade in self._world.trades.trades_absent or trade in self.trades.LITERATE_TRADES:
            return None
        if self.supply.reach_is_placeholder(trade):
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

    def population_report(self):
        """Everything the 'population' command (protocol.py) shows, worked
        out here rather than in the command layer: the country's own
        numbers (population, urban_fraction - already loaded for
        pop_scale), the size of the one town this household
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
        reference_pop = float(self._world.scenario.civ.get("population", 0.0))
        pop = self._world.people.population.total
        scale_from_baseline = (pop / reference_pop) if reference_pop else 1.0
        urban_frac = self._world.people.urban_fraction()
        trades = []
        for trade in sorted(self._world.trades.wages):
            national = self.supply.national_trade_population(trade)
            reach = self.supply.reachable_trade_population(trade) if self.trades.trade_available(trade) else 0.0
            have = self.book.employed(trade)
            trades.append({
                "trade": trade,
                "exists_here": self.trades.trade_available(trade),
                "estimated_in_the_country": round(national, 1),
                "within_your_reach": round(reach, 2),
                "you_employ": round(have, 2),
                "share_of_the_reachable_pool_you_employ":
                    round(have / reach, 4) if reach > 1e-9 else None,
                "is_placeholder": self._density_is_placeholder(trade),
            })
        return {
            "civilisation": self._world.scenario.civ.get("short_name", self._world.scenario.civ.get("name", self._world.scenario.civ.get("id", ""))),
            "population": round(pop),
            "reference_population_before_simulated_changes": round(reference_pop),
            "population_change_from_reference": round(scale_from_baseline - 1.0, 4),
            "urban_fraction": round(urban_frac, 3),
            "urban_population_estimate": round(pop * urban_frac),
            "the_town_you_actually_operate_in": {
                "estimated_population": round(self.settlement.home_town_population_estimate()),
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
                % self._world.game.plain_number(pop)),
        }
