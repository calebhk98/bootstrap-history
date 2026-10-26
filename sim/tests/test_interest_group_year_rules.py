"""An interest group's year (`InterestGroup.advance`), what the founder reads of groups (`interest_groups`,
`group_levy_reasons`), the start gate's prohibition check, and the sectors the founder's sales and hiring hurt
(`GroupView`). Stand-in worlds carry only what each rule reads."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.agents.api import ActorRecord, Sector
from sim.agents.group import InterestGroup
from sim.agents.group_tuning import GRIEVANCE_RETENTION, GROUP_PULL_SCALE
from sim.engine.agents_port_groups import GroupView
from sim.engine.interest_groups import InterestGroupsMixin, check_group_prohibition
from sim.refusal import cause_of

REVENUE = 1.0e6


class World:
    """What a group's year reads: this year's sectors, the state's revenue, capacity and purse, the founder's cover."""

    def __init__(self, sectors=None, reach=0.9, in_deficit=False, protection=0.0, year=100):
        self.year = year
        self._sectors = sectors or {}
        self.reach, self.deficit, self.protection = reach, in_deficit, protection
        self.blamed = []
        self.said = []

    def sectors(self):
        return self._sectors

    def scope_revenue(self, scope):
        return REVENUE * scope

    def concession_paid(self, line_name):
        return 0.0

    def edge(self, name):
        return name

    def state_reach(self):
        return self.reach

    def state_in_deficit(self):
        return self.deficit

    def founder_protection(self):
        return self.protection

    def lodge_blame(self, blame, text, gap, record):
        self.blamed.append(blame)

    def say(self, line):
        self.said.append(line)

    def plain_number(self, value):
        return "%d" % value

    def money_text(self, amount, grouped=False, short=False):
        return "%d" % amount


def iron_sector(lost=2.0e5, base=3.0e5, blame_share=1.0):
    sector = Sector("displaced_producers", "iron", "producers of iron", "your sales take their market", lost, base, 400.0, 1.0)
    sector.blame_share = blame_share
    return sector


SECTOR_KEY = "displaced_producers:iron"


def group_for(sector):
    return InterestGroup("group:displaced_producers:iron", ActorRecord(
        kind="interest_group", name=sector.name, group_kind=sector.kind, country=None, subject=sector.subject,
        cause=sector.cause, members=sector.members, technique=sector.technique))


class GroupYear(unittest.TestCase):

    def test_a_loss_sets_the_grievance_the_pull_and_the_claim_from_the_state_it_faces(self):
        sector = iron_sector()
        group = group_for(sector)
        group.advance(World({SECTOR_KEY: sector}))
        record = group.record
        self.assertIsNone(record.exited_year)
        self.assertAlmostEqual(record.grievance, 2.0e5 / 3.0e5)
        self.assertAlmostEqual(record.strength, 1.0 - math.exp(-2.0e5 / REVENUE / GROUP_PULL_SCALE))
        self.assertGreater(record.claim, 0.0)

    def test_a_petition_puts_blame_on_the_founder(self):
        sector = iron_sector()
        group = group_for(sector)
        world = World({SECTOR_KEY: sector})
        group.advance(world)
        self.assertEqual(group.record.petitions, 1)
        self.assertGreater(world.blamed[0], 0.0)

    def test_a_bigger_loss_has_a_stronger_pull(self):
        small, big = iron_sector(lost=2.0e4), iron_sector(lost=2.0e5)
        strengths = []
        for sector in (small, big):
            group = group_for(sector)
            group.advance(World({SECTOR_KEY: sector}))
            strengths.append(group.record.strength)
        self.assertLess(strengths[0], strengths[1])

    def test_a_loss_too_small_to_organise_over_disbands_the_group_at_once(self):
        sector = iron_sector(lost=1.0)
        group = group_for(sector)
        world = World({SECTOR_KEY: sector})
        group.advance(world)
        self.assertEqual(group.record.exited_year, 100)
        self.assertEqual((group.record.strength, group.record.claim, group.record.demands), (0.0, 0.0, []))
        self.assertEqual(cause_of(world.said[0]), "group_eased")

    def test_a_grievance_that_is_not_renewed_fades_by_the_retention_each_year_until_the_group_disbands(self):
        sector = iron_sector()
        group = group_for(sector)
        group.advance(World({SECTOR_KEY: sector}))
        first = group.record.lost_income
        group.advance(World({}))
        self.assertAlmostEqual(group.record.lost_income, first * GRIEVANCE_RETENTION)
        years = 0
        while group.record.exited_year is None and years < 100:
            group.advance(World({}, year=101 + years))
            years += 1
        self.assertIsNotNone(group.record.exited_year)

    def test_a_weak_state_makes_good_less_than_a_strong_one(self):
        claims = []
        for reach in (0.2, 0.9):
            sector = iron_sector()
            group = group_for(sector)
            group.advance(World({SECTOR_KEY: sector}, reach=reach))
            claims.append(group.record.claim)
        self.assertLess(claims[0], claims[1])

    def test_a_state_in_deficit_does_not_forbid_and_one_in_funds_does(self):
        demands = {}
        for deficit in (False, True):
            sector = iron_sector()
            group = group_for(sector)
            group.advance(World({SECTOR_KEY: sector}, in_deficit=deficit))
            demands[deficit] = list(group.record.demands)
        self.assertTrue(demands[False])
        self.assertEqual(demands[True], [])


class FounderReads(InterestGroupsMixin):
    """The reading side over a given list of group records."""

    def __init__(self, records, unfunded=None):
        self.records = records
        self.unfunded = unfunded or {}
        self.civ = {}
        self.state = types.SimpleNamespace(actors=types.SimpleNamespace(records=records))

    def _group_records(self):
        return self.records

    def state_treasury(self):
        return types.SimpleNamespace(record=types.SimpleNamespace(unfunded=self.unfunded))


class FounderReadsOfGroups(unittest.TestCase):

    def record(self, **fields):
        base = dict(kind="interest_group", name="producers of iron", group_kind="displaced_producers", subject="iron",
                    cause="c", members=400.0, lost_income=1000.0, grievance=0.5, strength=0.4, claim=300.0,
                    founded_year=90)
        base.update(fields)
        return ActorRecord(**base)

    def test_a_founder_who_hurt_nobody_has_no_groups_and_the_report_says_so_in_a_note(self):
        reads = FounderReads([])
        self.assertEqual(reads.interest_groups(), [])
        self.assertEqual(reads.interest_groups_report()["groups"], [])

    def test_a_row_carries_the_records_figures(self):
        row = FounderReads([self.record()]).interest_groups()[0]
        self.assertEqual((row["kind"], row["people"], row["income_lost_per_year"], row["state_undertakes_to_make_good"]),
                         ("displaced_producers", 400, 1000, 300))

    def test_the_report_totals_what_the_state_leaves_unpaid_on_group_lines(self):
        reads = FounderReads([self.record()], {"concession: group:displaced_producers:iron": 40.0, "road": 9.0})
        report = reads.interest_groups_report()
        self.assertEqual(report["state_leaves_unpaid_to_raise_from_taxpayers"], 40)
        self.assertTrue(report["state_in_deficit"])

    def test_a_paid_group_is_no_reason_for_a_levy_and_an_unpaid_one_is(self):
        paid = FounderReads([self.record()], {"concession: group:displaced_producers:iron": 0.0})
        unpaid = FounderReads([self.record()], {"concession: group:displaced_producers:iron": 40.0})
        self.assertEqual(paid.group_levy_reasons(), [])
        self.assertEqual(len(unpaid.group_levy_reasons()), 1)


class Prohibition(InterestGroupsMixin):
    """check_group_prohibition and group_prohibition_of over a stated ban."""
    STATE_OPPOSITION_PROTECTION_OVERRIDE = 0.5

    def __init__(self, ban=None, protection=0.0, state_interest=0.0):
        self.ban = ban
        self.nodes = {"press": {"name": "Press"}}
        self.state = types.SimpleNamespace(
            actors=types.SimpleNamespace(records=[1]), household=types.SimpleNamespace(protection=protection))
        self.actors = types.SimpleNamespace(prohibitions=lambda: {}, home_actors=lambda kind: [])
        self._interest = state_interest

    def _technique_bans(self):
        return {} if self.ban is None else {"press": self.ban}

    def state_interest(self, node):
        return self._interest


class StartGate(unittest.TestCase):

    def test_without_a_group_nothing_is_forbidden(self):
        self.assertIsNone(Prohibition().group_prohibition_of("press"))
        self.assertIsNone(check_group_prohibition(Prohibition(), "press", {}, False, None, True))

    def test_a_technique_a_group_wants_banned_is_refused_to_a_founder_without_cover(self):
        game = Prohibition(ban=("producers of iron", 0.6))
        verdict = check_group_prohibition(game, "press", game.nodes["press"], False, None, True)
        self.assertIs(verdict[0], False)

    def test_protection_above_what_the_groups_pull_needs_lets_the_founder_build(self):
        needed = 0.5 + (1.0 - 0.5) * 0.6
        below = Prohibition(ban=("producers of iron", 0.6), protection=needed - 0.01)
        above = Prohibition(ban=("producers of iron", 0.6), protection=needed + 0.01)
        self.assertIsNotNone(check_group_prohibition(below, "press", {}, False, None, True))
        self.assertIsNone(check_group_prohibition(above, "press", {}, False, None, True))

    def test_a_node_the_state_itself_values_is_not_forbidden(self):
        game = Prohibition(ban=("producers of iron", 0.6), state_interest=1.0)
        self.assertIsNone(game.group_prohibition_of("press"))

    def test_the_prohibition_is_one_of_the_start_gates_checks_and_both_name_the_same_kind_of_blocker(self):
        from sim.projects.api import START_CHECKS
        gate = next(check for check in START_CHECKS if check.cause == "group_prohibition")
        self.assertEqual((gate.source, gate.kind), ("start_gate_group_prohibition", check_group_prohibition.blocker_kind))


class HurtSectors(unittest.TestCase):

    def view(self, state, quote, pressured=None, factor=1.0):
        economy = types.SimpleNamespace(
            goods=types.SimpleNamespace(commodities_sold_by=lambda party: ["iron"]), main_material_of=lambda commodity: commodity,
            trade_quote=lambda material: quote,
            labour=types.SimpleNamespace(pressured_trades=lambda: pressured or [], price_factor=lambda trade: factor,
                                         unscarce_annual=lambda trade: 100.0))
        sim = types.SimpleNamespace(
            economy=economy, goods_market=types.SimpleNamespace(acting_party_id="founder"), market_state=lambda commodity: state,
            HOURS_PER_PERSON_YEAR=2000.0, labour=types.SimpleNamespace(market_supply=lambda trade: 2.0e6, local_market_share=lambda: 0.8),
            civ={})
        view = GroupView()
        view._sim = sim
        view.pay_per_person_year = lambda trade: 100.0
        return view

    def test_what_the_founder_displaced_is_a_loss_at_the_price_and_a_base_of_all_sales(self):
        view = self.view({"displaced_by_founder_tonnes": 10.0, "society_sales_tonnes": 30.0}, {"buy_per_tonne": 50.0})
        (sector,) = view.displaced_producers()
        self.assertEqual((sector.kind, sector.subject, sector.lost_income, sector.income_base), ("displaced_producers", "iron", 500.0, 2000.0))
        self.assertAlmostEqual(sector.members, 5.0)

    def test_nothing_displaced_makes_no_sector(self):
        view = self.view({"displaced_by_founder_tonnes": 0.0, "society_sales_tonnes": 30.0}, {"buy_per_tonne": 50.0})
        self.assertEqual(view.displaced_producers(), [])

    def test_a_commodity_with_no_market_or_no_quote_makes_no_sector(self):
        self.assertEqual(self.view(None, {"buy_per_tonne": 50.0}).displaced_producers(), [])
        self.assertEqual(self.view({"displaced_by_founder_tonnes": 1.0, "society_sales_tonnes": 1.0}, None).displaced_producers(), [])

    def test_a_trade_priced_above_the_table_squeezes_its_employers_by_the_hands_priced_out(self):
        view = self.view(None, None, pressured=["artisan"], factor=2.0)
        (sector,) = view.squeezed_employers()
        pool = 2.0e6 / 2000.0
        self.assertEqual((sector.kind, sector.subject), ("squeezed_employers", "artisan"))
        self.assertAlmostEqual(sector.lost_income, pool * 0.5 * 100.0)
        self.assertEqual(sector.scope, 0.8)

    def test_a_trade_nobody_pressed_squeezes_no_one(self):
        self.assertEqual(self.view(None, None, pressured=["labourer"], factor=1.0).squeezed_employers(), [])


if __name__ == "__main__":
    unittest.main()
