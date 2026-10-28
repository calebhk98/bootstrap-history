"""Shared assertions used by both layers of the regional-weather tests."""

import random

from sim import simulator


def assert_single_draw_fallback(test_case, test_sim, agriculture, year=137):
    test_sim.assembly.modules["agriculture"]._cells = []
    expected = agriculture.draw_weather_multiplier(
        random.Random(test_sim.view("weather_seed")(year, None)),
        agriculture.DEFAULT_SOIL.weather_stdev_fraction,
    )
    test_case.assertEqual(
        test_sim.view("harvest_weather")(year, None, True), expected)


def assert_matching_century(test_case, make_sim, years=100):
    first, second = make_sim(), make_sim()
    for _year in range(years):
        first.step()
        second.step()
    test_case.assertEqual(first.view("population")().children, second.view("population")().children)
    test_case.assertEqual(
        first.view("population")().working_age, second.view("population")().working_age)
    test_case.assertEqual(first.view("population")().elderly, second.view("population")().elderly)
    test_case.assertEqual(first.view("farm_holdings")()["stock_kg"], second.view("farm_holdings")()["stock_kg"])


def assert_save_reload_trajectory(test_case, make_sim, path, years=60):
    reference = make_sim()
    for _year in range(years):
        reference.step()

    replayed = make_sim()
    for _year in range(years // 2):
        replayed.step()
    simulator.save_state(replayed, path)

    resumed = make_sim()
    simulator.load_state(resumed, path)
    for _year in range(years // 2):
        resumed.step()

    test_case.assertEqual(
        reference.view("population")().children, resumed.view("population")().children)
    test_case.assertEqual(
        reference.view("population")().working_age, resumed.view("population")().working_age)
    test_case.assertEqual(
        reference.view("population")().elderly, resumed.view("population")().elderly)
    test_case.assertEqual(reference.view("farm_holdings")()["stock_kg"], resumed.view("farm_holdings")()["stock_kg"])
