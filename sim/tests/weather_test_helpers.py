"""Shared assertions used by both layers of the regional-weather tests."""

import random

from sim import simulator


def assert_single_draw_fallback(test_case, test_sim, agriculture, year=137):
    test_sim._farm_weather_cells = []
    expected = agriculture.draw_weather_multiplier(
        random.Random(test_sim._farm_year_weather_seed(year)),
        agriculture.DEFAULT_SOIL.weather_stdev_fraction,
    )
    test_case.assertEqual(
        test_sim._pooled_farm_weather_multiplier(year), expected)


def assert_matching_century(test_case, make_sim, years=100):
    first, second = make_sim(), make_sim()
    for _year in range(years):
        first.step()
        second.step()
    test_case.assertEqual(first.population.children, second.population.children)
    test_case.assertEqual(
        first.population.working_age, second.population.working_age)
    test_case.assertEqual(first.population.elderly, second.population.elderly)
    test_case.assertEqual(first.farm_stock_kg, second.farm_stock_kg)


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
        reference.population.children, resumed.population.children)
    test_case.assertEqual(
        reference.population.working_age, resumed.population.working_age)
    test_case.assertEqual(
        reference.population.elderly, resumed.population.elderly)
    test_case.assertEqual(reference.farm_stock_kg, resumed.farm_stock_kg)
