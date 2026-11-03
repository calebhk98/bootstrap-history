"""The lookups of a `MarketView` that a stub view built on `price`, `wage` and `area_of` gets without writing them out."""


class ViewDefaults:
    def offered_price(self, good, area):
        return self.price(good, area)

    def price_kind(self, good, area):
        return None

    def cleared_price(self, good, area):
        return None

    def prices_across(self, good, areas):
        return [self.price(good, each.area_id) for each in areas]

    def present_prices_at(self, names, tile, wages=False):
        found = {}
        for name in names:
            figure = self.wage(name, self.area_of(name, tile)) if wages else self.price(name, self.area_of(name, tile))
            if figure is not None:
                found[name] = figure
        return found
