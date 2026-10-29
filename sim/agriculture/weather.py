"""The growing-season weather: one draw per cell of the held land, correlated by distance and pooled by arable share.

Each cell's draw comes from its own generator seeded by (civilisation, cell, year, the game's salt), so a year's weather
is the same however the game reached it. The salt is drawn once from the game's dice, at the first seed asked for
(`weather_seed`), and kept in the save."""
import random

from sim.world import agriculture, weather_pooling
from sim.world.shared_constants import GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM

from . import rules
from .constants import FARM_WEATHER_POOLED_CELL_CAP


class Weather:

    def setup_weather(self):
        self._cells = None             # built at the first read (never saved): the held land does not change
        self._cholesky = None
        self._tile_share = None

    def _build_cells(self):
        raw = rules.raw_cells(self.needs.held_tile_geometry())
        self._cells = rules.pooled_cells(raw, FARM_WEATHER_POOLED_CELL_CAP)
        self._cholesky = weather_pooling.correlation_cholesky(self._cells, GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM)
        self._tile_share = weather_pooling.tile_shares(raw)

    def weather_cells(self):
        """[WeatherCell(cell id, lat, lon, weight), ...] the harvest weather is pooled over; empty with no land."""
        if self._cells is None:
            self._build_cells()
        return self._cells

    def weather_seed(self, year, region=None):
        """The seed of one year's weather draw, for a region (a cell id) or the whole civilisation. The first call draws
        the game's salt from its dice."""
        if not self.world.weather_salt:
            self.world.weather_salt = self.needs.game_random().getrandbits(30) + 1
        return rules.weather_seed(self.needs.civilisation().get("id", "civ"), region, year, self.world.weather_salt)

    def _independent_draws(self, year, cells):
        return rules.independent_draws(cells, lambda cell_id: self.weather_seed(year, region=cell_id))

    def harvest_weather(self, year, weather_stdev_fraction=None, harmed=True):
        """This year's harvest multiplier pooled over the cells; `harmed` applies what the externalities take off the
        tiles' yield. With no cells it is one draw for the whole territory, unharmed."""
        stdev = agriculture.DEFAULT_SOIL.weather_stdev_fraction if weather_stdev_fraction is None else weather_stdev_fraction
        cells = self.weather_cells()
        if not cells:
            return agriculture.draw_weather_multiplier(random.Random(self.weather_seed(year)), stdev)
        pooled = weather_pooling.pooled_multiplier(
            cells, self._cholesky, self._independent_draws(year, cells), stdev,
            agriculture.WEATHER_FLOOR_MULTIPLIER, agriculture.WEATHER_CEILING_MULTIPLIER)
        if not harmed:
            return pooled
        return pooled * weather_pooling.harm_multiplier(self._tile_share, self.externality_yield_factors(year))

    def externality_yield_factors(self, year):
        """{tile: factor} the game's externality providers agree on for the year's harvest, each clamped to 0..1."""
        return rules.yield_factors(self.needs.externality(self.needs.provider_game(), year))

    def farm_weather(self, year):
        """{tile id: this year's multiplier on that tile's own weather cell}, from the draws the pooled multiplier averages.
        A tile merged into a pooled cell, or with no cell, is absent."""
        cells = self.weather_cells()
        if not cells:
            return {}
        multipliers = weather_pooling.cell_multipliers(
            cells, self._cholesky, self._independent_draws(year, cells), agriculture.DEFAULT_SOIL.weather_stdev_fraction,
            agriculture.WEATHER_FLOOR_MULTIPLIER, agriculture.WEATHER_CEILING_MULTIPLIER)
        return {cell.cell_id: multiplier for cell, multiplier in zip(cells, multipliers)}
