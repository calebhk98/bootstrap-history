"""A written-out two-country economy for the country-figure rules: the parts of an `Economy` those rules read, as plain data.

Home tiles town, farms and hills; the north's tiles north_farms and north_port. Grain is one market area in each country.
Every figure is a round number a test can add up by hand."""
from types import SimpleNamespace

from sim.economy.cohort_store import CohortStore
from sim.economy.households_cohort import Cohort
from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer
from sim.economy.market_memory import MarketMemory, market_key
from sim.economy.setup import labour_area
from sim.tests.labour_record_stand_in import labour_record
from sim.labour.market.records import MarketState

HOME, NORTH = "home", "north"
HOME_TILES = ("town", "farms", "hills")
NORTH_TILES = ("north_farms", "north_port")
COIN_PER_UNIT = 3.0
HOURS_PER_YEAR = 2000.0
GRAIN_AREAS = {"grain:home": set(HOME_TILES), "grain:north": set(NORTH_TILES)}


def cohort(agent_id, tile, people, income, ownership_share=1.0):
    return Cohort(agent_id, tile, 0, people, people / 2.0, ownership_share, last_year_income=income)


def producer(agent_id, tile, recipe_id, last_runs, land_rent_per_run=0.0):
    return Producer(agent_id, "owner", recipe_id, tile, last_runs, last_runs=last_runs, land_rent_per_run=land_rent_per_run)


def wage_key(trade, tile):
    return market_key(trade, labour_area(tile))


def two_country_economy():
    """The economy as the figures read it: setup, record and the area map of grain."""
    country_of = lambda tile: HOME if tile in HOME_TILES else NORTH
    setup = SimpleNamespace(
        civ_id=HOME, tiles={tile: None for tile in HOME_TILES + NORTH_TILES}, countries=lambda: (HOME, NORTH),
        tiles_of=lambda country: {HOME: HOME_TILES, NORTH: NORTH_TILES}.get(country, ()), country_of=country_of,
        coin_per_unit=COIN_PER_UNIT, working_hours_per_year=HOURS_PER_YEAR, unskilled_trade="labourer", currency_id="coin",
        recipes={"farm": SimpleNamespace(outputs={"grain": 10.0}), "mine": SimpleNamespace(outputs={"ore": 2.0})},
        land_per_run={"farm": 1.0, "mine": 0.0})
    memory = MarketMemory(
        wages={wage_key("labourer", "town"): 1.0, wage_key("labourer", "farms"): 1.5, wage_key("miner", "hills"): 3.0,
               wage_key("labourer", "north_farms"): 0.8, wage_key("labourer", "north_port"): 0.9},
        prices={market_key("grain", "grain:home"): 2.0, market_key("grain", "grain:north"): 4.0},
        volume_weights={market_key("grain", "grain:home"): 100.0, market_key("grain", "grain:north"): 50.0})
    workforce = MarketState()
    workforce.workers = {labour_area("town"): {"labourer": [60.0, 20.0], "miner": [5.0]}, labour_area("farms"): {"labourer": [30.0]},
                         labour_area("north_farms"): {"labourer": [20.0, 10.0]}, labour_area("north_port"): {"scribe": [2.0]}}
    cohorts = [cohort("household:town", "town", 100.0, 200.0), cohort("household:farms", "farms", 50.0, 50.0),
               cohort("household:north_farms", "north_farms", 40.0, 30.0), cohort("household:north_port", "north_port", 10.0, 20.0)]
    producers = [producer("producer:mine", "hills", "mine", 4.0), producer("producer:farm", "farms", "farm", 6.0, land_rent_per_run=1.0),
                 producer("producer:north_farm", "north_farms", "farm", 5.0, land_rent_per_run=2.0)]
    record = SimpleNamespace(cohorts=CohortStore({each.agent_id: each for each in cohorts}), producers=ProducerStore({each.agent_id: each for each in producers}), memory=memory, goods=SimpleNamespace(volumes={}),
                           labour=labour_record({wage_key("labourer", "town"): 1000.0, wage_key("labourer", "farms"): 3000.0, wage_key("labourer", "north_farms"): 100.0},
                                                {wage_key("labourer", "town"): 10.0, wage_key("miner", "hills"): 0.0}, workforce=workforce), carriage=SimpleNamespace(carried_goods={}), land=SimpleNamespace(land_rent={}, rent_paid={"farms": 6.0, "north_farms": 10.0},
                                                                                      titles={each.tile: {each.agent_id: 1.0} for each in cohorts}))
    area_map = SimpleNamespace(goods=lambda: ("grain",),
                               areas=lambda good: tuple(SimpleNamespace(area_id=area_id, tiles=tiles) for area_id, tiles in GRAIN_AREAS.items()),
                               tile_sets=lambda good: {area_id: set(tiles) for area_id, tiles in GRAIN_AREAS.items()})
    return SimpleNamespace(setup=setup, record=record, area_map=area_map)
