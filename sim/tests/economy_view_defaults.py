"""The lookups of a `MarketView` that a stub view built on `price`, `wage` and `area_of` gets without writing them out."""
import types


def setup_of(*trades):
    """The trades and opening wages a stub view's `setup` holds (the first trade is the unskilled one; each opened at 1.0)."""
    return types.SimpleNamespace(opening_wages={trade: 1.0 for trade in trades}, unskilled_trade=trades[0], currency_id="coin",
                                 trades={trade: types.SimpleNamespace(training_years=0.0) for trade in trades})


class _EveryTrade(dict):
    """A trades table that knows any trade, untrained, for a stub view whose recipes name trades freely."""

    def __contains__(self, trade):
        return True

    def __getitem__(self, trade):
        return types.SimpleNamespace(training_years=0.0)


class ViewDefaults:
    setup = types.SimpleNamespace(opening_wages={"labour": 1.0}, unskilled_trade="labour", currency_id="coin", trades=_EveryTrade())

    def offered_price(self, good, area):
        return self.price(good, area)

    def price_kind(self, good, area):
        return None

    def cleared_price(self, good, area):
        return None

    def observed_inflation(self, currency):
        return None

    def opening_wage_level(self, currency):
        return 1.0

    def wage_held_anywhere(self, trade):
        return True

    def equity(self, agent):
        return 0.0

    def claims(self, agent, currency):
        return 0.0

    def loss_rate(self, agent, currency):
        return 0.0

    def prices_across(self, good, areas):
        return [self.price(good, each.area_id) for each in areas]

    def present_prices_at(self, names, tile):
        found = {}
        for name in names:
            figure = self.price(name, self.area_of(name, tile))
            if figure is not None:
                found[name] = figure
        return found
