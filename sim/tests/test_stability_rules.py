"""Complaints 484 and 486, the rules: authority (reach, hold, what officials keep), unrest, a rising against a garrison, a
ruler's life and succession, and land confiscation and reform each take built inputs and call the rule. No game is built."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents import authority, collection, land_moves, revenue, revolt, ruler, unrest
from sim.agents.api import Government
from sim.agents.government_levers import LeverContext, set_lever
from sim.agents.records import ActorRecord
from sim.economy import titles, titles_moves
from sim.world import battle, demography

PEOPLE = {"seat": 1000.0, "near": 1000.0, "far": 1000.0}


class ReachTests(unittest.TestCase):

    def shares(self, officials=0.4, days=None, literacy=0.0):
        days = days or {"seat": 0.0, "near": 2.0, "far": 20.0}
        return collection.tile_shares(officials, 200.0, literacy, PEOPLE, days)

    def test_reach_falls_with_distance_and_a_tile_without_a_road_is_not_reached(self):
        shares = self.shares()
        self.assertGreaterEqual(shares["seat"], shares["near"])
        self.assertGreater(shares["near"], shares["far"])
        self.assertEqual(self.shares(days={"seat": 0.0})["far"], 0.0)

    def test_reach_rises_with_officials_and_with_roads(self):
        self.assertGreater(self.shares(officials=0.5)["far"], self.shares()["far"])
        shorter = self.shares(days={"seat": 0.0, "near": 1.0, "far": 10.0})
        self.assertGreater(shorter["far"], self.shares()["far"])

    def test_authority_is_reach_held_by_the_garrison(self):
        self.assertEqual(authority.authority(0.8, 1.0), 0.8)
        self.assertAlmostEqual(authority.authority(0.8, 0.5), 0.4)
        self.assertEqual(authority.authority(0.8, 0.0), 0.0)


class HoldTests(unittest.TestCase):

    def test_with_no_one_in_arms_the_tile_is_held_whatever_the_garrison(self):
        self.assertEqual(authority.hold(0.0, 0.0), 1.0)

    def test_hold_falls_as_the_rising_grows_and_rises_with_the_garrison(self):
        self.assertGreater(authority.hold(100.0, 10.0), authority.hold(100.0, 100.0))
        self.assertGreater(authority.hold(100.0, 100.0), authority.hold(100.0, 1000.0))
        self.assertGreater(authority.hold(200.0, 100.0), authority.hold(100.0, 100.0))

    def test_a_rising_with_no_garrison_to_meet_it_is_not_held(self):
        self.assertEqual(authority.hold(0.0, 5.0), 0.0)

    def test_hold_is_the_battle_rules_chance_the_attacker_loses(self):
        self.assertAlmostEqual(authority.hold(70.0, 30.0), 1.0 - battle.attacker_win_probability(30.0, 70.0))


class CorruptionTests(unittest.TestCase):

    def test_officials_keep_more_far_from_the_seat_and_less_when_watched(self):
        near, far = authority.share_kept(1.0, 0.0), authority.share_kept(30.0, 0.0)
        self.assertLess(near, far)
        self.assertGreater(authority.share_kept(30.0, 0.0), authority.share_kept(30.0, 0.5))
        self.assertEqual(authority.share_kept(30.0, 1.0), 0.0)
        self.assertEqual(authority.share_kept(0.0, 0.0), 0.0)

    def test_what_officials_keep_never_exceeds_the_ceiling_and_a_tile_no_road_reaches_is_at_it(self):
        self.assertLessEqual(authority.share_kept(1e6, 0.0), authority.OFFICIAL_KEEP_CEILING + 1e-12)
        self.assertEqual(authority.share_kept(None, 0.0), authority.OFFICIAL_KEEP_CEILING)

    def test_the_people_weighted_share_counts_only_tiles_the_roads_reach(self):
        days = {"seat": 0.0, "far": 30.0}
        both = authority.people_weighted_kept({"seat": 1.0, "far": 1.0, "cut_off": 1.0}, days, {})
        self.assertAlmostEqual(both, 0.5 * authority.share_kept(30.0, 0.0))
        self.assertEqual(authority.people_weighted_kept({"cut_off": 5.0}, days, {}), 0.0)

    def test_a_form_assessed_in_a_far_province_brings_the_state_less(self):
        assessed = revenue.Assessment("tithe", "harvest", 1000.0, 0.1, 100.0, tonnes=10.0, material="wheat",
                                      payers=(("a", 40.0),))
        leaked = revenue.leaked(assessed, 0.25)
        self.assertAlmostEqual(leaked.money, 75.0)
        self.assertAlmostEqual(leaked.tonnes, 7.5)
        self.assertAlmostEqual(leaked.payers[0][1], 30.0)
        self.assertEqual(leaked.kept_by_officials, 0.25)
        self.assertIs(revenue.leaked(assessed, 0.0), assessed)

    def test_a_world_that_reads_no_corruption_leaks_nothing(self):
        self.assertEqual(authority.kept_on(SimpleNamespace(), None), 0.0)
        self.assertEqual(authority.kept_on(SimpleNamespace(corruption_share=lambda tiles: 0.3), None), 0.3)

    def test_conscription_and_the_levy_follow_authority(self):
        self.assertEqual(authority.conscripts(1000.0, 0.1, 1.0), 100.0)
        self.assertEqual(authority.conscripts(1000.0, 0.1, 0.5), 50.0)
        self.assertEqual(authority.levy_reach(SimpleNamespace()), 1.0)
        self.assertEqual(authority.levy_reach(SimpleNamespace(collectible_share=lambda tiles=None: 0.4)), 0.4)


class UnrestTests(unittest.TestCase):

    def test_grievance_is_what_is_taken_and_owed_beyond_what_is_given(self):
        self.assertAlmostEqual(unrest.grievance(30.0, 10.0, 20.0, 100.0), 0.2)
        self.assertEqual(unrest.grievance(10.0, 0.0, 50.0, 100.0), 0.0)
        self.assertEqual(unrest.grievance(10.0, 0.0, 0.0, 0.0), 0.0)

    def test_only_a_take_above_the_accustomed_one_is_felt_and_custom_follows_the_take(self):
        self.assertEqual(unrest.adapted(0.1, 0.1), 0.0)
        self.assertAlmostEqual(unrest.adapted(0.3, 0.1), 0.2)
        reference = 0.1
        for _ in range(60):
            reference = unrest.adapt(reference, 0.3)
        self.assertAlmostEqual(reference, 0.3, places=3)

    def test_unrest_rises_with_each_pressure_and_never_reaches_one(self):
        base = unrest.unrest(0.1, 0.0, 0.0)
        self.assertGreater(unrest.unrest(0.2, 0.0, 0.0), base)
        self.assertGreater(unrest.unrest(0.1, 0.3, 0.0), base)
        self.assertGreater(unrest.unrest(0.1, 0.0, 0.5), base)
        self.assertEqual(unrest.unrest(0.0, None, 0.0), 0.0)
        self.assertLess(unrest.unrest(50.0, 1.0, 50.0), 1.0 + 1e-12)

    def test_hunger_is_the_share_of_need_unmet_and_none_where_nothing_is_booked(self):
        self.assertIsNone(unrest.hunger(None))
        self.assertAlmostEqual(unrest.hunger(0.7), 0.3)
        self.assertEqual(unrest.hunger(1.4), 0.0)

    def test_collective_liability_weighs_more_as_payers_leave_and_an_individual_rule_never_does(self):
        self.assertEqual(unrest.liability_burden("individual", 0.1, 100.0, 40.0), 0.0)
        self.assertEqual(unrest.liability_burden("collective", 0.1, 100.0, 100.0), 0.0)
        heavy = unrest.liability_burden("collective", 0.1, 100.0, 50.0)
        self.assertAlmostEqual(heavy, 1.0)
        self.assertGreater(unrest.liability_burden("collective", 0.1, 100.0, 25.0), heavy)
        self.assertEqual(unrest.liability_burden("collective", 0.1, 100.0, 0.0), 0.0)

    def test_the_factions_grievance_is_the_people_weighted_mean(self):
        self.assertAlmostEqual(unrest.faction_grievance([(100.0, 0.5), (300.0, 0.1)], 1000.0), 0.08)
        self.assertEqual(unrest.faction_grievance([], 1000.0), 0.0)

    def test_a_rising_is_the_armed_organised_share_of_the_discontented(self):
        self.assertAlmostEqual(unrest.rising_soldiers(1000.0, 0.5, 1.0), 1000.0 * 0.5 * unrest.ARMED_SHARE_OF_DISCONTENTED)
        self.assertLess(unrest.rising_soldiers(1000.0, 0.5, 0.1), unrest.rising_soldiers(1000.0, 0.5, 1.0))
        self.assertEqual(unrest.organisation(0.0, 1000.0), unrest.ORGANISED_FLOOR)
        self.assertGreater(unrest.organisation(900.0, 1000.0), unrest.ORGANISED_FLOOR)

    def test_the_discontented_rise_only_where_they_would_more_likely_than_not_win(self):
        reference = 100.0
        weak = unrest.rising_strength(10.0, reference)
        self.assertFalse(unrest.rises(weak, 1000.0))
        self.assertTrue(unrest.rises(unrest.rising_strength(5000.0, reference), unrest.rising_strength(100.0, reference)))
        self.assertTrue(unrest.rises(1.0, 0.0))
        self.assertFalse(unrest.rises(0.0, 0.0))

    def test_land_taken_is_remembered_and_fades(self):
        faded = unrest.fade_memory({"a": 0.5, "b": 1e-7})
        self.assertAlmostEqual(faded["a"], 0.5 * unrest.CONFISCATION_MEMORY_PER_YEAR)
        self.assertNotIn("b", faded)


class RisingTests(unittest.TestCase):

    def test_a_won_rising_takes_the_tile_and_at_the_seat_the_ruler(self):
        won = revolt.resolve(500.0, 100.0, 50.0, 10.0, on_seat=False, draw=0.0)
        self.assertEqual(won.kind, revolt.TILE_LOST)
        self.assertTrue(won.rising_won)
        seat = revolt.resolve(500.0, 100.0, 50.0, 10.0, on_seat=True, draw=0.0)
        self.assertEqual(seat.kind, revolt.RULER_REPLACED)

    def test_a_rising_beaten_by_a_much_stronger_garrison_is_put_down_and_loses_more(self):
        lost = revolt.resolve(500.0, 10.0, 500.0, 1000.0, on_seat=True, draw=0.99)
        self.assertEqual(lost.kind, revolt.PUT_DOWN)
        self.assertGreater(lost.rising_lost / 500.0, lost.garrison_lost / 500.0)

    def test_the_draw_decides_between_equals(self):
        kinds = {revolt.resolve(100.0, 50.0, 100.0, 50.0, False, draw).kind for draw in (0.1, 0.9)}
        self.assertEqual(kinds, {revolt.TILE_LOST, revolt.PUT_DOWN})


class RulerTests(unittest.TestCase):

    def test_mortality_follows_the_demography_band_of_his_age(self):
        self.assertEqual(ruler.mortality_rate(5.0), demography.BASELINE_ANNUAL_MORTALITY_RATE_CHILD)
        self.assertEqual(ruler.mortality_rate(30.0), demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE)
        self.assertEqual(ruler.mortality_rate(70.0), demography.BASELINE_ANNUAL_MORTALITY_RATE_ELDERLY)
        self.assertGreater(ruler.death_probability(70.0), ruler.death_probability(30.0))

    def test_poor_health_raises_the_chance_and_no_hazard_removes_it(self):
        self.assertGreater(ruler.death_probability(30.0, 3.0), ruler.death_probability(30.0, 1.0))
        self.assertEqual(ruler.death_probability(30.0, 0.0), 0.0)

    def test_a_ruler_dies_when_the_draw_falls_below_his_chance(self):
        chance = ruler.death_probability(60.0)
        self.assertTrue(ruler.dies(60.0, 1.0, chance * 0.5))
        self.assertFalse(ruler.dies(60.0, 1.0, chance * 2.0))

    def test_an_heir_is_born_a_childbearing_age_before_and_never_before_birth(self):
        self.assertAlmostEqual(ruler.heir_age(60.0), 60.0 - ruler.childbearing_age())
        self.assertEqual(ruler.heir_age(20.0), 0.0)

    def test_an_even_split_of_backing_is_disputed_and_a_dominant_faction_is_not(self):
        self.assertEqual(ruler.dispute_probability({"a": 1.0, "b": 1.0}), 1.0)
        self.assertAlmostEqual(ruler.dispute_probability({"a": 9.0, "b": 1.0}), 0.2)
        self.assertEqual(ruler.dispute_probability({"a": 1.0}), 0.0)
        self.assertEqual(ruler.dispute_probability({}), 0.0)

    def test_the_strongest_and_the_runner_up_are_found_with_ties_by_id(self):
        self.assertEqual(ruler.contenders({"b": 2.0, "a": 2.0, "c": 1.0}), ("a", "b"))
        self.assertEqual(ruler.contenders({"a": 0.0}), (None, None))

    def test_the_state_ages_its_ruler_and_an_heir_accedes_backed_by_the_strongest_faction(self):
        record = ActorRecord(kind="government")
        state = Government("government", record)

        class World:
            year = 100
            backing = {"g1": 3.0, "g2": 2.9}

            def faction_backing(self):
                return dict(self.backing)

        def draws(*values):
            queue = iter(values)
            return lambda *key: SimpleNamespace(random=lambda: next(queue))

        record.ruler_age = 80.0
        world = World()
        world.rng_for = draws(0.0, 0.99)       # the ruler dies; the even-ish split is not disputed
        state.accede(world)
        self.assertTrue(record.accession_due)
        self.assertAlmostEqual(record.ruler_age, ruler.heir_age(81.0))
        self.assertEqual((record.ruler_backer, record.succession_challenger), ("g1", ""))
        record.accession_due, record.ruler_age = False, 60.0
        world.rng_for = draws(0.0, 0.0)        # he dies again and the runner-up disputes it
        state.accede(world)
        self.assertEqual((record.ruler_backer, record.succession_challenger), ("g1", "g2"))
        record.accession_due, record.ruler_age, record.succession_challenger = False, ruler.opening_age(), ""
        world.rng_for = draws(0.999)
        state.accede(world)
        self.assertFalse(record.accession_due)
        self.assertEqual(record.ruler_age, ruler.opening_age() + 1.0)


class LandTests(unittest.TestCase):

    def test_confiscation_takes_a_share_of_each_private_holding_for_the_state_and_spares_its_own(self):
        moves = land_moves.confiscation_moves({"a": 0.6, "b": 0.3, "state": 0.1}, "state", 0.5)
        self.assertEqual([(move.giver, move.receiver) for move in moves], [("a", "state"), ("b", "state")])
        self.assertAlmostEqual(sum(move.share for move in moves), 0.45)
        self.assertEqual(land_moves.confiscation_moves({"a": 1.0}, "state", 0.0), [])
        self.assertEqual(land_moves.confiscation_moves({"a": 1.0}, "state", 0.5, exempt=("a",)), [])

    def test_reform_gives_the_excess_over_the_cap_to_the_tenants_in_proportion_to_what_they_work(self):
        rows = [{"tenant": "t1", "lessor": "lord", "share": 0.3}, {"tenant": "t2", "lessor": "lord", "share": 0.1}]
        moves = land_moves.reform_moves({"lord": 0.8, "t1": 0.1}, rows, cap=0.5)
        self.assertEqual({move.receiver: round(move.share, 9) for move in moves}, {"t1": 0.225, "t2": 0.075})
        self.assertAlmostEqual(sum(move.share for move in moves), 0.3)

    def test_what_a_holder_does_not_let_out_stays_with_him(self):
        self.assertEqual(land_moves.reform_moves({"lord": 0.8}, [], cap=0.5), [])
        rows = [{"tenant": "t1", "lessor": "lord", "share": 0.1}]
        self.assertAlmostEqual(sum(move.share for move in land_moves.reform_moves({"lord": 0.8}, rows, 0.5)), 0.1)

    def test_the_applied_moves_change_the_titles_by_the_economys_own_rule(self):
        record = SimpleNamespace(titles={"t": {"lord": 0.8, "t1": 0.1}},
                                 tenancies={"t": [{"tenant": "t1", "lessor": "lord", "share": 0.3, "arrears": 0.0}]},
                                 cohorts={})
        held, rows = titles_moves.holdings(record, ["t"])
        plan = land_moves.planned(held, rows, "state", confiscate=0.5, cap=None)
        moved = titles_moves.apply(record, [("t", move.giver, move.receiver, move.share) for move in plan["t"]])
        self.assertAlmostEqual(moved["t"], 0.45)
        self.assertAlmostEqual(titles.shares(record, "t")["state"], 0.45)
        self.assertAlmostEqual(titles.shares(record, "t")["lord"], 0.4)
        self.assertAlmostEqual(sum(titles.shares(record, "t").values()), 0.9)

    def test_reform_after_confiscation_works_on_what_is_left(self):
        rows = [{"tenant": "t1", "lessor": "lord", "share": 0.4}]
        plan = land_moves.planned({"t": {"lord": 0.8}}, {"t": rows}, "state", confiscate=0.0, cap=0.5)
        record = SimpleNamespace(titles={"t": {"lord": 0.8}}, tenancies={"t": [dict(rows[0], arrears=0.0)]}, cohorts={})
        titles_moves.apply(record, [("t", move.giver, move.receiver, move.share) for move in plan["t"]])
        held = titles.shares(record, "t")
        self.assertAlmostEqual(held["lord"], 0.5)
        self.assertAlmostEqual(held["t1"], 0.3)
        self.assertAlmostEqual(land_moves.taken_from_private(plan["t"], "state"), 0.3)

    def test_the_levers_are_set_read_and_refused_like_any_other(self):
        record = ActorRecord(kind="government")
        context = LeverContext()
        change = set_lever(record, {"lever": "confiscation", "value": 0.2}, context)
        self.assertEqual(change["after"], 0.2)
        self.assertEqual(set_lever(record, {"lever": "land_reform", "value": 0.4}, context)["after"], 0.4)
        refused = set_lever(record, {"lever": "land_reform", "value": 1.5}, context)
        self.assertEqual(refused.cause, "value_out_of_range")
        self.assertEqual(record.levers["land_reform"], 0.4)


if __name__ == "__main__":
    unittest.main()
