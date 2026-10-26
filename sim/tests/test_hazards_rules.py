"""The hazards module's rules, called on plain values (`sim/hazards/rules.py`): what built defences take off a harm, the output
floor, the corpus a sack faces, the output factor's fall and recovery, how the hazards ahead are worded, the world event log and
the famine reading."""
QUICK_TOPIC = True

import unittest

from sim.hazards import constants, rules

RESIDUE = constants.KNOWLEDGE_RESIDUE_AFTER_CLOSURE


class DefencesTests(unittest.TestCase):
    def test_a_counter_never_built_gives_nothing_a_shut_one_a_residue_and_a_running_one_all(self):
        self.assertEqual(rules.counter_strength(False, True, RESIDUE), 0.0)
        self.assertEqual(rules.counter_strength(True, False, RESIDUE), RESIDUE)
        self.assertEqual(rules.counter_strength(True, True, RESIDUE), 1.0)

    def test_a_counter_names_what_else_must_run_for_its_own_kind_and_label_only(self):
        node = {"mechanics": {"hazard_counters": [
            {"kind": "sack_chance", "label": "guns", "requires_running": ["works"]},
            {"kind": "sack_chance", "label": "walls"}]}}
        self.assertEqual(rules.counter_requirements(node, "sack_chance", "guns"), ["works"])
        self.assertEqual(rules.counter_requirements(node, "sack_chance", "walls"), ())
        self.assertEqual(rules.counter_requirements(node, "staff_loss", "guns"), ())
        self.assertEqual(rules.counter_requirements({}, "sack_chance", "guns"), ())

    def test_an_own_mine_counts_only_above_its_floor(self):
        self.assertEqual(rules.own_mine_strength(0.0005, 0.0005), 0.0)
        self.assertEqual(rules.own_mine_strength(1.0, 0.0005), 1.0)

    def test_each_defence_removes_a_share_of_what_is_left(self):
        entries = [{"factor": 0.6}, {"factor": 0.5}]
        self.assertAlmostEqual(rules.relief_product(entries), 0.3)
        self.assertEqual(rules.relief_product([]), 1.0)

    def test_the_share_each_defence_removes_is_what_the_harm_would_be_without_it_less_what_it_is(self):
        removed = rules.removed_shares([{"factor": 0.6}, {"factor": 0.5}])
        self.assertAlmostEqual(removed[0], 0.5 - 0.3)
        self.assertAlmostEqual(removed[1], 0.6 - 0.3)

    def test_relief_moves_the_output_floor_back_toward_one(self):
        self.assertAlmostEqual(rules.output_floor(0.6, 1.0), 0.6)
        self.assertAlmostEqual(rules.output_floor(0.6, 0.5), 0.8)
        self.assertEqual(rules.output_floor(0.6, 0.0), 1.0)

    def test_the_nations_public_health_lowers_the_rate_before_the_households_own_defences(self):
        exposure = rules.staff_exposure(0.4, 0.25, 0.5)
        self.assertAlmostEqual(exposure["before_defences"], 0.3)
        self.assertAlmostEqual(exposure["loss"], 0.15)

    def test_the_counters_of_nodes_and_of_own_mines_are_merged_each_kind_in_row_order(self):
        rows = {"real_erosion": [(5, "vault", 0.2, "a vault")], "sack_chance": [(1, "walls", 0.5, "walls")]}
        own = {"real_erosion": [(0, "_own_gold", 0.55, "gold")]}
        merged = rules.counters_by_kind(rows, own)
        self.assertEqual(merged["real_erosion"], [("_own_gold", 0.55, "gold"), ("vault", 0.2, "a vault")])
        self.assertEqual(merged["sack_chance"], [("walls", 0.5, "walls")])

    def test_a_war_costs_less_the_stronger_the_military_and_a_founder_with_none_changes_nothing(self):
        self.assertEqual(rules.war_relief(0.0, 0.3), (1.0, None))
        self.assertAlmostEqual(rules.war_relief(1.0, 0.3)[0], 0.7)

    def test_a_lapsed_defence_is_told_with_why_and_what_the_country_has_adopted(self):
        entry = {"label": "walls", "short_of": "a garrison", "lapsed_node": "wall", "partly_adopted_nationally": True}
        words = rules.entry_words(entry, "Wall", "by your choice")
        self.assertIn("lapsed: a garrison", words)
        self.assertIn("lapsed: Wall is closed by your choice", words)
        self.assertIn("partly adopted nationally", words)
        self.assertEqual(rules.entry_words({"label": "walls"}, None, None), "walls")

    def test_a_shut_concern_is_told_by_its_reason_and_one_never_opened_says_so(self):
        reasons = {"staff": "for want of staff"}
        self.assertEqual(rules.closure_words({"reason": "staff"}, reasons), "for want of staff")
        self.assertEqual(rules.closure_words({"reason": "something_else"}, reasons), "")
        self.assertEqual(rules.closure_words(None, reasons), "and has not been opened")

    def test_the_kinds_a_hazard_carries_follow_the_declared_order(self):
        self.assertEqual(rules.hazard_kinds_in({"real_erosion": 1, "staff_loss": 1, "name": "x"}), ["staff_loss", "real_erosion"])


class CorpusTests(unittest.TestCase):
    def test_a_sack_that_takes_anything_takes_at_least_one(self):
        self.assertEqual(rules.losable_after_roll(["a", "b", "c", "d"], 0.5), 2)
        self.assertEqual(rules.losable_after_roll(["a", "b", "c", "d"], 0.01), 1)

    def test_the_announcement_names_what_went_and_says_when_the_corpus_itself_did(self):
        plain = rules.corpus_loss_message(["b", "a"], True, [], 0)
        self.assertEqual(plain, "KNOWLEDGE LOST: 2 technologies forgotten - a, b")
        worse = rules.corpus_loss_message(["a"], False, ["written"], 1)
        self.assertIn("1 technology forgotten", worse)
        self.assertIn("never printed and dispersed", worse)
        self.assertIn("THE CORPUS ITSELF WENT (written)", worse)
        self.assertIn("1 of these stood on the road to your goal", worse)

    def test_more_than_eight_losses_are_counted_not_all_named(self):
        message = rules.corpus_loss_message([str(number) for number in range(12)], True, [], 0)
        self.assertIn("and 4 more", message)


class OutputFactorTests(unittest.TestCase):
    def test_recovery_adds_the_base_rate_doubled_at_full_leverage_and_stops_at_one(self):
        self.assertAlmostEqual(rules.recovered_output_factor(0.5, 0.01, 0.0), 0.51)
        self.assertAlmostEqual(rules.recovered_output_factor(0.5, 0.01, 1.0), 0.52)
        self.assertEqual(rules.recovered_output_factor(0.999, 0.01, 1.0), 1.0)

    def test_a_hazard_lowers_the_factor_to_the_highest_floor_and_never_raises_it(self):
        self.assertEqual(rules.lowered_output_factor(1.0, [0.5, 0.7]), 0.7)
        self.assertEqual(rules.lowered_output_factor(0.6, [0.9]), 0.6)


class TimelineTests(unittest.TestCase):
    def state(self, years_until, quick, strong, multiplier=1.0, in_progress=False):
        return rules.timeline_state(in_progress, multiplier, years_until, quick, strong, "plague")[0]

    def test_the_urgency_escalates_as_the_date_closes_in_on_the_lead_time_of_the_hedge(self):
        self.assertEqual(self.state(100, 3, 10), "on the horizon")
        self.assertEqual(self.state(12, 3, 10), "begin hedge now")
        self.assertEqual(self.state(8, 3, 10), "stopgap only")
        self.assertEqual(self.state(2, 3, 10), "too late to hedge")

    def test_no_hedge_in_sight_and_a_hazard_well_hedged_or_under_way_each_read_their_own_way(self):
        self.assertEqual(self.state(50, None, None), "no hedge found")
        self.assertEqual(self.state(50, None, None, multiplier=0.5), "hedged")
        self.assertEqual(self.state(0, 3, 10, in_progress=True), "happening now")

    def test_the_headline_says_the_years_in_words(self):
        self.assertEqual(rules.years_words(1), "1 year")
        self.assertEqual(rules.years_words(12.4), "12 years")

    def test_lead_times_are_read_from_a_range_or_a_single_figure_or_are_absent(self):
        key = "even_started_today_the_real_hedges_here_take_years"
        self.assertEqual(rules.hedge_lead_times({key: {"quickest": 3, "slowest": 10}}), (3, 10))
        self.assertEqual(rules.hedge_lead_times({key: 7}), (7, 7))
        self.assertEqual(rules.hedge_lead_times({}), (None, None))

    def test_only_the_first_row_and_the_warnings_keep_their_sentence(self):
        rows = [{"urgency": "hedged", "headline": "a", "in_progress": False}, {"urgency": "hedged", "headline": "b", "in_progress": False},
                {"urgency": "too late to hedge", "headline": "c", "in_progress": False}]
        kept = rules.compact_timeline(rows, constants.HAZARD_TIMELINE_WARN_TAGS)
        self.assertEqual(["headline" in row for row in kept], [True, False, True])


class EventLogTests(unittest.TestCase):
    def test_an_entry_stringifies_actors_and_tiles_and_copies_its_facts(self):
        facts = {"died": 3.0}
        entry = rules.world_event_entry(210.0, "flood", [1, "rome"], ("t1",), "rain", facts)
        self.assertEqual(entry, {"year": 210, "kind": "flood", "actors": ["1", "rome"], "tiles": ["t1"], "cause": "rain", "facts": {"died": 3.0}})
        self.assertIsNot(entry["facts"], facts)

    def test_records_older_than_the_years_kept_are_dropped_in_place(self):
        kept = [{"year": 100}, {"year": 150}, {"year": 205}]
        same = kept
        rules.trim_world_events(kept, 100)
        self.assertEqual(kept, [{"year": 150}, {"year": 205}])
        self.assertIs(kept, same)

    def test_rows_filter_by_kind_year_and_actor(self):
        events = [{"year": 1, "kind": "a", "actors": ["x"]}, {"year": 5, "kind": "b", "actors": ["x", "y"]}]
        self.assertEqual([row["year"] for row in rules.world_event_rows(events, kind="b")], [5])
        self.assertEqual([row["year"] for row in rules.world_event_rows(events, since_year=5)], [5])
        self.assertEqual([row["year"] for row in rules.world_event_rows(events, actor="x")], [1, 5])

    def test_the_famine_reading_weights_each_stratum_by_its_people(self):
        people, shortfall = rules.famine_shortfall([(600.0, 0.6), (400.0, 0.2)])
        self.assertEqual(people, 1000.0)
        self.assertAlmostEqual(shortfall, 0.44)
        self.assertEqual(rules.famine_shortfall([]), (0.0, 0.0))

    def test_the_draw_seed_names_the_game_the_country_the_kind_and_the_year(self):
        self.assertEqual(rules.draw_seed(7, "han", "flood", 100), "7|han|flood|100")

    def test_the_words_for_causes_that_fail_fall_back_to_the_quantity(self):
        report = {"failed": [{"why": "no grain", "quantity": "food"}, {"why": "", "quantity": "population"}]}
        self.assertEqual(rules.failed_causes_words(report), "no grain; population")


if __name__ == "__main__":
    unittest.main()
