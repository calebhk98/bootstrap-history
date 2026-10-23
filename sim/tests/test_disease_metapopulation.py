"""The spatial stage of the disease model (Complaint 490): one patch per tile, infection passing along the traffic
between tiles, the immune state an endemic pathogen leaves, and the readers of regional disease. Rules are called on
patches built in the test; the expected-value stepping (`metapopulation.expected`) makes a comparison exact."""

QUICK_TOPIC = True

import unittest

from sim.agents import budget_works
from sim.disease import api as disease
from sim.disease import endemic_state, metapopulation as spread
from sim.engine import colony_rules

BANDS = ("children", "working_age", "elderly")


def pathogen(density_exponent=0.0, reproduction=4.0, case_fatality=0.2):
    """Two stages: 5 days exposed, 10 days infectious; transmissibility set so the reproduction number is `reproduction`."""
    return disease.Pathogen.from_plain({
        "id": "test_pathogen", "name": "Test pathogen",
        "stages": [{"id": "exposed", "infectiousness": 0.0, "mean_duration_in_days": 5.0, "shape": 2},
                   {"id": "infectious", "infectiousness": 1.0, "mean_duration_in_days": 10.0, "shape": 2}],
        "transmissibility_per_day": reproduction / 10.0, "case_fatality": case_fatality,
        "immunity": {"permanent": True, "duration_in_days": None}, "density_exponent": density_exponent})


def people(total):
    return {"children": total * 0.3, "working_age": total * 0.6, "elderly": total * 0.1}


def tiles_with_seed(test_pathogen, tile_people, crowding, seeded_tile="a", seeded=50):
    tiles = spread.patches_for(test_pathogen, None, tile_people, crowding, "rule-test", 1)
    tiles[seeded_tile]["working_age"].seed_infection(test_pathogen, seeded)
    return tiles


def infected_in(tiles, tile):
    return sum(patch.infected_now() for patch in tiles[tile].values())


def run_days(test_pathogen, tiles, contacts, crowding, days):
    spread.advance_tiles(test_pathogen, tiles, contacts, crowding, days, draw=spread.expected)


def two_tiles(total_a=100000, total_b=100000):
    return {"a": people(total_a), "b": people(total_b)}


class ContactBetweenTilesTest(unittest.TestCase):
    def test_with_no_contact_nothing_passes_between_tiles(self):
        test_pathogen = pathogen()
        tile_people, crowding = two_tiles(), {"a": 1.0, "b": 1.0}
        tiles = tiles_with_seed(test_pathogen, tile_people, crowding)
        run_days(test_pathogen, tiles, {}, crowding, 120)
        self.assertEqual(infected_in(tiles, "b"), 0)
        self.assertEqual(tiles["b"]["working_age"].counts["susceptible"], 60000)
        self.assertGreater(tiles["a"]["working_age"].counts["recovered"], 0)

    def test_more_traffic_between_tiles_carries_infection_there_sooner(self):
        test_pathogen = pathogen()
        tile_people, crowding = two_tiles(), {"a": 1.0, "b": 1.0}
        reached = []
        for trips in (0.0, 2000.0, 20000.0):
            tiles = tiles_with_seed(test_pathogen, tile_people, crowding)
            contacts = spread.contacts_from_trips({("a", "b"): trips}, tile_people)
            run_days(test_pathogen, tiles, contacts, crowding, 40)
            reached.append(infected_in(tiles, "b") + tiles["b"]["working_age"].counts["recovered"])
        self.assertEqual(reached[0], 0)
        self.assertGreater(reached[1], reached[0])
        self.assertGreater(reached[2], reached[1])

    def test_a_dense_town_takes_infection_faster_than_a_sparse_countryside(self):
        test_pathogen = pathogen(density_exponent=1.0)
        tile_people = two_tiles()
        contacts = spread.contacts_from_trips({("a", "b"): 20000.0}, tile_people)
        reached = {}
        for name, crowding_of_b in (("countryside", 1.0), ("town", 4.0)):
            crowding = {"a": 1.0, "b": crowding_of_b}
            tiles = tiles_with_seed(test_pathogen, tile_people, crowding)
            run_days(test_pathogen, tiles, contacts, crowding, 40)
            reached[name] = infected_in(tiles, "b") + tiles["b"]["working_age"].counts["recovered"]
        self.assertGreater(reached["town"], reached["countryside"])

    def test_a_pathogen_whose_contact_does_not_follow_density_ignores_crowding(self):
        test_pathogen = pathogen(density_exponent=0.0)
        tile_people = two_tiles()
        contacts = spread.contacts_from_trips({("a", "b"): 20000.0}, tile_people)
        reached = []
        for crowding_of_b in (1.0, 4.0):
            crowding = {"a": 1.0, "b": crowding_of_b}
            tiles = tiles_with_seed(test_pathogen, tile_people, crowding)
            run_days(test_pathogen, tiles, contacts, crowding, 40)
            reached.append(infected_in(tiles, "b"))
        self.assertAlmostEqual(reached[0], reached[1])

    def test_people_are_conserved_across_tiles_less_the_dead(self):
        test_pathogen = pathogen()
        tile_people, crowding = two_tiles(), {"a": 1.0, "b": 1.0}
        tiles = tiles_with_seed(test_pathogen, tile_people, crowding)
        contacts = spread.contacts_from_trips({("a", "b"): 20000.0}, tile_people)
        run_days(test_pathogen, tiles, contacts, crowding, 200)
        living = sum(patch.living() for patches in tiles.values() for patch in patches.values())
        killed = sum(patch.deaths_from_disease for patches in tiles.values() for patch in patches.values())
        self.assertAlmostEqual(living + killed, 200000.0, places=3)
        self.assertGreater(killed, 0.0)


class TrafficTest(unittest.TestCase):
    def test_trade_trips_follow_the_tonnes_carried_in_either_direction_between_held_tiles(self):
        trips = spread.trade_trips({"a": {"b": 10.0}, "b": {"a": 6.0, "outside": 99.0}}, ["a", "b"], travellers_per_tonne=2.0)
        self.assertEqual(trips, {("a", "b"): 32.0})

    def test_migrants_go_to_the_bordering_tiles_in_proportion_to_who_took_people_in(self):
        trips = spread.migrant_trips({"a": 90.0}, {"b": 2.0, "c": 1.0, "d": 50.0}, {"a": ["b", "c"]})
        self.assertAlmostEqual(trips[("a", "b")], 60.0)
        self.assertAlmostEqual(trips[("a", "c")], 30.0)
        self.assertNotIn(("a", "d"), trips)

    def test_everyday_trips_go_to_bordering_tiles_and_a_larger_neighbour_draws_more(self):
        tile_people = {"a": people(1000), "b": people(3000), "c": people(1000)}
        trips = spread.local_trips(tile_people, {"a": ["b", "c"], "b": [], "c": []}, trips_per_person=1.0)
        self.assertAlmostEqual(trips[("a", "b")], 750.0)
        self.assertAlmostEqual(trips[("a", "c")], 250.0)

    def test_an_empty_tile_does_not_stop_its_neighbours_meeting(self):
        tile_people = {"a": people(1000), "empty": people(0), "b": people(1000)}
        reached = spread.borders_through_empty(tile_people, {"a": ["empty"], "empty": ["a", "b"], "b": ["empty"]})
        self.assertEqual(reached["a"], ["b"])
        self.assertEqual(reached["b"], ["a"])
        self.assertNotIn("empty", reached["a"])

    def test_an_arrival_enters_each_group_of_joined_tiles_the_routes_reach_about_as_soon(self):
        groups = [["a", "b"], ["c"], ["d"]]
        days = {"a": 10.0, "b": 12.0, "c": 40.0, "d": 400.0}
        self.assertEqual(spread.entry_tiles(days, groups, margin_days=150.0), ["a", "c"])
        self.assertEqual(spread.entry_tiles({}, groups, margin_days=150.0), [])

    def test_groups_of_joined_tiles_follow_the_contacts(self):
        contacts = {"a": [("b", 0.1)], "b": [("a", 0.1)]}
        self.assertEqual(spread.components(contacts, {"a", "b", "c"}), [["a", "b"], ["c"]])

    def test_contact_shares_scale_with_trips_and_never_pass_all_of_a_tiles_time(self):
        tile_people = {"a": people(1000), "b": people(1000)}
        small = dict(spread.contacts_from_trips({("a", "b"): 10.0}, tile_people, visit_days=1.0)["a"])
        large = dict(spread.contacts_from_trips({("a", "b"): 20.0}, tile_people, visit_days=1.0)["a"])
        self.assertAlmostEqual(large["b"], 2 * small["b"])
        saturated = spread.contacts_from_trips({("a", "b"): 1e9}, tile_people)
        self.assertAlmostEqual(sum(share for _, share in saturated["a"]), 1.0)

    def test_crowding_averages_to_the_nations_index_and_a_dense_tile_sits_above_a_sparse_one(self):
        tile_people = {"town": people(9000), "farms": people(1000)}
        crowding = spread.crowding_by_tile(tile_people, {"town": 100.0, "farms": 100.0}, 2.0)
        self.assertGreater(crowding["town"], crowding["farms"])
        mean = sum(sum(tile_people[tile].values()) * crowding[tile] for tile in crowding) / 10000.0
        self.assertAlmostEqual(mean, 2.0)

    def test_a_tile_with_no_known_area_takes_the_national_index(self):
        self.assertEqual(spread.crowding_by_tile({"a": people(10)}, {}, 1.5), {"a": 1.5})


class EndemicStateTest(unittest.TestCase):
    def test_the_susceptible_share_is_the_reciprocal_of_the_reproduction_number(self):
        for reproduction in (2.0, 4.75, 15.0):
            test_pathogen = pathogen(reproduction=reproduction)
            band_people = people(100000)
            force = endemic_state.endemic_force_per_year(test_pathogen, band_people)
            susceptible = sum(band_people[band] * endemic_state.susceptible_share_of_band(force, endemic_state.BAND_AGES[band])
                              for band in BANDS) / 100000.0
            self.assertAlmostEqual(susceptible, 1.0 / reproduction, places=6)

    def test_children_are_mostly_susceptible_and_adults_mostly_immune(self):
        counts = endemic_state.endemic_counts(pathogen(reproduction=15.0), people(100000))
        immune_share = {band: counts[band]["recovered"] / sum(counts[band].values()) for band in BANDS}
        self.assertLess(immune_share["children"], immune_share["working_age"])
        self.assertLess(immune_share["working_age"], immune_share["elderly"])
        self.assertGreater(immune_share["working_age"], 0.9)

    def test_a_more_contagious_pathogen_leaves_more_people_immune(self):
        immune = [sum(band["recovered"] for band in endemic_state.endemic_counts(pathogen(reproduction=r), people(100000)).values())
                  for r in (2.0, 5.0, 15.0)]
        self.assertLess(immune[0], immune[1])
        self.assertLess(immune[1], immune[2])

    def test_a_pathogen_that_cannot_sustain_itself_leaves_nobody_immune_or_infected(self):
        counts = endemic_state.endemic_counts(pathogen(reproduction=0.8), people(1000))
        self.assertEqual(sum(band["recovered"] for band in counts.values()), 0)
        self.assertEqual(sum(count for band in counts.values() for name, count in band.items() if name not in ("susceptible", "recovered")), 0)

    def test_crowding_raises_the_effective_number_and_so_the_immune_share_of_a_density_dependent_pathogen(self):
        test_pathogen = pathogen(density_exponent=1.0, reproduction=3.0)
        sparse = endemic_state.endemic_counts(test_pathogen, people(100000), crowding=1.0)
        dense = endemic_state.endemic_counts(test_pathogen, people(100000), crowding=4.0)
        self.assertGreater(sum(band["recovered"] for band in dense.values()), sum(band["recovered"] for band in sparse.values()))

    def test_an_endemic_start_keeps_every_person_and_opens_with_infection_in_the_people(self):
        test_pathogen = pathogen(reproduction=6.0)
        tiles = spread.patches_for(test_pathogen, None, {"a": people(50000)}, {"a": 1.0}, "rule-test", 1, endemic=True)
        self.assertEqual(sum(patch.living() for patch in tiles["a"].values()), 50000)
        self.assertGreater(sum(patch.infected_now() for patch in tiles["a"].values()), 0)
        self.assertGreater(tiles["a"]["working_age"].immune_share(), tiles["a"]["children"].immune_share())


class RecordsTest(unittest.TestCase):
    def test_a_year_saves_counts_only_and_a_loaded_year_draws_what_a_straight_year_does(self):
        test_pathogen = pathogen()
        known = {"test_pathogen": test_pathogen}
        tile_people, crowding = two_tiles(20000, 20000), {"a": 1.0, "b": 1.0}
        contacts = spread.contacts_from_trips({("a", "b"): 5000.0}, tile_people)

        def one_year(records, arrivals):
            introduced, deaths = {}, {}
            spread.run_year(known, records, introduced, deaths, tile_people, contacts, crowding, {}, arrivals, "seed", 7)
            return deaths

        straight = {}
        one_year(straight, {"test_pathogen": ["a"]})
        import json
        loaded = json.loads(json.dumps(straight))
        second_straight, second_loaded = json.loads(json.dumps(straight)), loaded
        self.assertEqual(one_year(second_straight, {}), one_year(second_loaded, {}))
        self.assertEqual(second_straight, second_loaded)
        self.assertEqual(set(straight["test_pathogen"]["a"]["working_age"]), set(network_names(test_pathogen)))

    def test_a_forecast_changes_nothing_and_is_empty_when_nobody_is_infected(self):
        test_pathogen = pathogen()
        known = {"test_pathogen": test_pathogen}
        tile_people, crowding = two_tiles(20000, 20000), {"a": 1.0, "b": 1.0}
        records = {}
        spread.run_year(known, records, {}, {}, tile_people, {}, crowding, {}, {"test_pathogen": ["a"]}, "seed", 1)
        after = {tile: {band: dict(counts) for band, counts in bands.items()} for tile, bands in records["test_pathogen"].items()}
        quiet = {"test_pathogen": {tile: {band: dict(counts, **{name: 0 for name in network_names(test_pathogen)
                                                                if name not in ("susceptible", "recovered")})
                                          for band, counts in bands.items()} for tile, bands in after.items()}}
        self.assertEqual(spread.forecast_year(known, quiet, tile_people, {}, crowding, {}, "seed", 2), {})
        spread.forecast_year(known, records, tile_people, {}, crowding, {}, "seed", 2)
        self.assertEqual(records["test_pathogen"], after)

    def test_a_forecast_expects_more_deaths_where_more_are_infected(self):
        test_pathogen = pathogen(case_fatality=0.3)
        known = {"test_pathogen": test_pathogen}
        tile_people, crowding = two_tiles(20000, 20000), {"a": 1.0, "b": 1.0}
        expected_deaths = []
        for seeded in (10, 1000):
            tiles = tiles_with_seed(test_pathogen, tile_people, crowding, seeded=seeded)
            records = {"test_pathogen": spread._saved(tiles)}
            forecast = spread.forecast_year(known, records, tile_people, {}, crowding, {}, "seed", 1)["test_pathogen"]
            expected_deaths.append(sum(sum(bands.values()) for bands in forecast["expected_deaths_by_tile"].values()))
        self.assertGreater(expected_deaths[1], expected_deaths[0])
        self.assertEqual(set(forecast["expected_deaths_by_tile"]), {"a"})


def network_names(test_pathogen):
    from sim.disease import network
    return network.compartment_ids(test_pathogen)


class ReadersOfRegionalDiseaseTest(unittest.TestCase):
    def test_a_party_must_be_larger_where_the_year_takes_more_of_it(self):
        factors = [disease.nation.provisioning_factor(loss) for loss in (0.0, 0.1, 0.5, 0.99)]
        self.assertEqual(factors[0], 1.0)
        self.assertEqual(factors, sorted(factors))
        self.assertAlmostEqual(factors[1], 1.0 / 0.9)
        self.assertTrue(all(factor < 1e6 for factor in factors))

    def test_outfitting_settlers_costs_more_on_a_tile_whose_diseases_take_more(self):
        spec = {"settlers": 100, "outfit_hours_per_settler": 50.0}
        healthy = colony_rules.outfit_cost(spec, 2.0)
        sick = colony_rules.outfit_cost(spec, 2.0, disease_loss=0.2)
        self.assertEqual(healthy, 100 * 50.0 * 2.0)
        self.assertAlmostEqual(sick, healthy / 0.8)

    def test_a_campaign_needs_more_grain_where_the_frontier_regions_disease_takes_more_of_the_men(self):
        class World:
            loss = 0.0

            def threat_pressure(self):
                return 0.5

            def territory(self):
                return type("Territory", (), {"frontier_km": 1000.0})()

            def frontier_disease_loss(self):
                return self.loss

            def commodity_of(self, material):
                return material

            def material_cost(self, material, tonnes):
                return 2.0 * tonnes

        def tonnes(loss):
            world = World()
            world.loss = loss
            lines = budget_works.campaign_line(world, 10000.0)
            return sum(lines[0].materials.values())

        self.assertGreater(tonnes(0.3), tonnes(0.0))
        self.assertAlmostEqual(tonnes(0.3) / tonnes(0.0), 1.0 / 0.7, places=6)


if __name__ == "__main__":
    unittest.main()
