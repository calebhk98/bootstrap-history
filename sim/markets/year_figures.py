"""Figures read from the live economy and kept until its state changes. Part of the port.

Every field is a pure function of the economy (itself rebuilt from the saved record), so none is saved: a loaded
game rebuilds each on its first read. `forget` is the one place they are reset."""


class YearFigures:

    def __init__(self):
        self.forget()

    def forget(self):
        self.answers = None             # (prices by good, wage by trade, rate) of the home country, in coin
        self.stale = set()              # goods whose shown price is not a market's, read with `answers`
        self.country_answers = {}       # the same for a partner country, by country
        self.kinds = None               # (the answers they belong to, {good: kind of its shown price})
        self.floor_costs = {}           # need floors by country scope
        self.floor_costs_of = None      # the economy object they were read from
        self.tile_prices = None         # (the answers they belong to, {tile: prices})
