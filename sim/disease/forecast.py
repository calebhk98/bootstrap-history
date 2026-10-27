"""What the model expects of the coming year, and what the diseases take from a tile in a year."""
from sim.geography.api import endemic_people_loss, settlement

from . import metapopulation as spread, nation, rules
from .epidemics import pathogens
from .technology_effects import working_age_death_share


class Forecast:

    def epidemic_forecast(self, food_kcal_per_day=None):
        """The model's own forecast of the coming year from the infections now and the contact between tiles,
        with no new arrival: {"expected_deaths", "expected_working_age_share", "by_pathogen": [{pathogen, name,
        infected, expected_deaths}], "expected_deaths_by_tile": {tile: {band: deaths}}, "arrival_chances":
        {pathogen: chance of reaching the nation this year}}. Nothing is drawn and nothing changes; kept until the
        next disease year."""
        if self._forecast is not None:
            return self._forecast
        state = self.world
        year = self.needs.year()
        people = self.people_by_tile()
        by_pathogen, by_tile = [], {}
        if state.records:
            nutrition_ratio = (self.needs.nutrition_ratio(food_kcal_per_day) if food_kcal_per_day is not None else 1.0)
            fatality_by_pathogen, transmission = self.technology_scales(sorted(state.records))
            forecast = spread.forecast_year(
                pathogens(), state.records, people, self.contacts(people), self.crowding_by_tile(people),
                self.fatality_scale_by_band(nutrition_ratio), self.seed_text(), year,
                fatality_factor=fatality_by_pathogen, transmission_scale=transmission)
            for pathogen_id, row in forecast.items():
                killed = sum(sum(bands.values()) for bands in row["expected_deaths_by_tile"].values())
                by_pathogen.append({"pathogen": pathogen_id, "name": pathogens()[pathogen_id].name,
                                    "infected": row["infected"], "expected_deaths": round(killed)})
                for tile, bands in row["expected_deaths_by_tile"].items():
                    for band, count in bands.items():
                        by_tile.setdefault(tile, {}).setdefault(band, 0.0)
                        by_tile[tile][band] += count
        expected = spread.deaths_by_band(by_tile)
        chances = nation.arrival_chances(self.contact_sources(), year, self.contact_weight)
        result = {"expected_deaths": round(sum(expected.values())),
                  "expected_working_age_share": working_age_death_share(expected, float(self.needs.working_age())),
                  "by_pathogen": by_pathogen, "expected_deaths_by_tile": by_tile,
                  "arrival_chances": {pathogen_id: round(chance, 4) for pathogen_id, chance in sorted(chances.items())
                                      if not spread.is_circulating(state.records, pathogen_id)}}
        self._forecast = result
        return result

    def regional_disease_loss(self, tile):
        """The share of a working-age person on `tile` the diseases there take in a year: the endemic death rate
        of the tile's land plus the model's forecast of this year's epidemics on it (the nation's share on a tile it
        does not hold, where no infection is followed). Over a year, so a party's losses on arrival follow from it."""
        endemic = endemic_people_loss([tile], self.needs.legacy_world_map()).get("working_age", 0.0)
        forecast = self.epidemic_forecast()
        return rules.regional_loss(endemic, forecast["expected_deaths_by_tile"], forecast["expected_working_age_share"],
                                   self.people_by_tile(), tile)

    def frontier_disease_loss(self):
        """The mean `regional_disease_loss` over the tiles held that border a tile not held: where a campaign
        in the field meets the country's neighbours."""
        held = self.held_tiles()
        frontier = rules.frontier_tiles(held, settlement.borders_among(sorted(set(held)), self.needs.legacy_world_map()))
        if not frontier:
            return 0.0
        return sum(self.regional_disease_loss(tile) for tile in frontier) / len(frontier)

    def epidemic_risk(self):
        """What the model forecasts for the coming year, without the deaths tile by tile: infections now, contact between
        tiles, and the chance each pathogen reaches the nation. The risk of epidemics read from the model, not from a dated list."""
        return {key: value for key, value in self.epidemic_forecast().items() if key != "expected_deaths_by_tile"}
