"""Complaint 649: a country's trade book counts what crossed its border over the external edge (trade with partners off the map),
by year, as well as the goods the merchants carried; the home state's `foreign_trade_by_year` has this counterpart for every
country. The rules are called on built inputs and on the hand-built two-country economy."""

QUICK_TOPIC = True

from .harness import check

from sim.economy import carried_book, country_figures
from sim.engine import country_trade_years
from sim.engine.economy_port_country import CountryAnswers
from sim.tests import economy_fixture as fixture

book = {}
country_trade_years.note(book, "north", 100, 30.0, 10.0)
country_trade_years.note(book, "north", 100, 5.0, 0.0)
country_trade_years.note(book, "north", 101, 7.0, 2.0)
check("a year's off-map flows add up by country and year",
	  country_trade_years.value(book, "north", 100, "in") == 35.0 and country_trade_years.value(book, "north", 100, "out") == 10.0
	  and country_trade_years.value(book, "north", 101, "in") == 7.0, book)
check("another country's book is its own", country_trade_years.value(book, "south", 100, "in") == 0.0)
check("a year nothing was noted for crossed nothing", country_trade_years.value(book, "north", 99, "out") == 0.0)
country_trade_years.note(book, "north", 100 + country_trade_years.YEARS_KEPT, 1.0, 1.0)
check("only the last few years are kept", "100" not in book["north"] and "101" in book["north"], sorted(book["north"]))

setup = fixture.two_country_setup()
economy, _outcomes = fixture.run(setup, years=4)
carried = carried_book.trade_value(country_figures.trade_book(economy, fixture.NORTH), "in") * setup.coin_per_unit
away = {"in": 11.0, "out": 3.0}
answers = CountryAnswers(economy, fixture.NORTH, off_map_trade=away.get)
alone = CountryAnswers(economy, fixture.NORTH, off_map_trade=lambda direction: 0.0)
check("a country's trade is what the merchants carried across its border plus what crossed the external edge",
	  abs(answers.trade_value("in") - (alone.trade_value("in") + 11.0)) < 1e-9 and abs(answers.trade_value("out") - (alone.trade_value("out") + 3.0)) < 1e-9
	  and abs(alone.trade_value("in") - carried) < 1e-9, (answers.trade_value("in"), alone.trade_value("in"), carried))
check("the book by good is the merchants' alone (the off-map flows have no good)", answers.trade_book() == alone.trade_book())

# the port attributes the year's external-edge trade to the country whose tile the port stands on
from types import SimpleNamespace

from sim.engine.economy_port_year import AgentEconomy

kept = {}
port = SimpleNamespace(stored=kept, _economy=SimpleNamespace(setup=SimpleNamespace(port_tile="north_port", country_of=lambda tile: "north")),
					   _sim=SimpleNamespace(state=SimpleNamespace(scenario=SimpleNamespace(year=120))))
AgentEconomy._note_off_map_trade(port, 40.0, 25.0)
check("the port's off-map trade of a year is booked to the country of its tile, and kept with the economy's record",
	  kept["country_trade_by_year"] == {"north": {"120": {"in": 40.0, "out": 25.0}}}, kept)
