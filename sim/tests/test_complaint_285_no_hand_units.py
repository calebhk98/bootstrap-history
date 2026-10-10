"""Complaint 285: nothing formats a mass, area, sum of money or temperature for a player by hand.

Three static scans (no game is built):
1. no string literal in sim/ writes a placeholder straight in front of a unit word (`%s denarii`, `{} tonnes`,
   `%d ha`, `%.1f kg`): such a sentence must call units_prose (mass_text, area_text, money_text, temperature_text);
2. every reply key in the UI package that reads like a quantity has a unit field rule, so a reply converts it;
3. every reply key a text-screen line prints beside a native unit label has a field rule too.
A new sentence or reply field that breaks one fails here.
"""

QUICK_TOPIC = True

import ast
import os
import re
import unittest

from sim.engine import units as U

ROOT = U.ROOT
PLACEHOLDER = r"(?:%[-+ #0-9.,*]*[dfgsr]|\{[^{}]*\})"
UNIT_WORD = r"(?:tonnes?|t|hectares?|ha|m2|square metres?|kg|kilograms?|denarii|den|°C|celsius)"
HAND_UNIT = re.compile(PLACEHOLDER + r"\)?\s*" + UNIT_WORD + r"(?![A-Za-z])")
NATIVE_LABEL = re.compile(r"\bden\b|\btonnes?\b|\bt/yr\b|\bha\b|\bhectares?\b|\bkg\b")

# Files whose literals may name a unit beside a placeholder, and why.
EXEMPT_SENTENCE_FILES = {
    # Text-screen renderers print values from a reply that units_text.for_text already converted; the label
    # they print is swapped by render_pretty. Held by complaint_285_text_screens and the key scans below.
    "sim/ui/proto/render_screens_economy.py": "text screen over a converted reply",
    "sim/ui/proto/render_screen_state_blocks.py": "text screen over a converted reply",
    "sim/ui/proto/render_screen_why.py": "text screen over a converted reply",
    "sim/ui/proto/state_shut_staffing.py": "text screen over a converted reply",
    "sim/ui/proto/util.py": "text screen over a converted reply (coin hoard line)",
    # Developer analysis subcommands over the tree in book terms, not the game's screens.
    "sim/ui/cli.py": "analysis subcommand output",
    "sim/ui/cli_analysis.py": "analysis subcommand output",
    # Help names the unit a command takes without a quantity of its own.
    "sim/ui/proto/help.py": "help text giving a command example and naming its unit",
    # Model internals: a repr, a data unit label, and messages for data authors.
    "sim/world/deposits.py": "model repr and a data unit label",
    "sim/engine/validate_production.py": "message for data authors",
    # Carrier labels kept on a record of physical inputs; not shown to a player.
    "sim/geography/sea_freight.py": "audit label",
    "sim/geography/rail_freight.py": "audit label",
}
# A number written with thousands separators by hand; counts, people and hours go through plain_number instead.
HAND_NUMBER = re.compile(r"\{:,\.\d+f\}")
# Names that hold a sum of money in the civilisation's coin when they appear as a sentence argument.
MONEY_SOURCES = {"capital", "purchase_budget", "spending_power", "credit_limit", "project_cost", "upkeep", "revenue",
                 "reopen_fee", "bounty_price", "farm_price_per_hectare", "housing_price_per_place", "wage_bill",
                 "mine_operating_cost", "living_cost", "committed_spend", "funding_capacity", "slave_quote",
                 "venture_real_earnings", "venture_real_upkeep", "recurring_net", "project_cost_now"}
# Files that may write a number or name the currency by hand, and why.
EXEMPT_FORMAT_FILES = {
    "sim/engine/units_prose.py": "the formatters themselves",
    "sim/engine/units.py": "the registry",
    "sim/engine/data.py": "defines the currency words",
    "sim/engine/knowledge_warning.py": "formats numbers of a reply the text screen already converted",
    "sim/engine/shortage_conditions.py": "formats a number of a reply the text screen already converted",
    "sim/engine/cash_remedies.py": "a tonnage that is the argument of the command it suggests",
    "sim/ui/proto/util.py": "_fmt_num, the text screens' number format over converted replies",
    "sim/ui/proto/state_shut_staffing.py": "text screen over a converted reply",
    "sim/ui/proto/dispatch.py": "swaps the currency word of a reply (_localise_money)",
}
# Files that ask for the currency word to hand it to the text screens as the label they swap in.
CURRENCY_WORD_EXEMPT = {"sim/ui/cli_interactive.py": "sets the screens' short currency label"}
# Sentences whose arguments name a money source but are not themselves a sum of money.
MONEY_ARGUMENT_EXEMPT = {
    "sim/engine/step_phase_project_start.py": "a tonnage sized from capital",
}
# Reply keys whose names read like a quantity but whose values are not a number of money, mass or area.
NOT_NUMERIC_KEYS = {
    "and_could_pay_for", "capacity_gained_or_lost", "cash_book", "coin_hoard", "could_pay_for", "debt", "done_earned",
    "expected_lost_per_sacking", "failure_costs_hours", "interest_groups", "it_yields_per_hectare_per_year",
    "max_cost", "max_total_cost", "pay_to_lower_the_risk", "reserve_cash", "revenue_and_upkeep_apply_only_once_opened",
    "revenue_forecast_scope", "state_interest_trait_score", "sustainable_debt_means", "wage_foundation",
    "what_a_failure_costs", "what_it_costs_you", "where_the_money_comes_from", "worth_knowing_early",
    "you_could_pay_for", "your_hours_lost",
}
# Rounded reply fields that are counts, hours, people, factors, shares, distances or years: not a mass, area, sum of money or
# temperature. A new rounded field not in a field rule, not tagged by its producer (units.tagged) and not here fails.
ROUND_NOT_A_UNIT_QUANTITY = {
    "arrives_units", "chance_caught", "covered", "delivered_units",  # stock in its own unit, a chance, a share covered
    "artisan_capacity", "artisans", "births", "calendar_floor_years", "calendar_years_left",
    "chance_of_being_denounced_this_year", "change_share", "children", "civ_domain_factor", "committed_hours",
    "corpus_kept", "craftsmen", "craftsmen_on_your_staff", "days_on_the_road", "deaths", "deaths_children",
    "deaths_elderly", "deaths_working_age", "debt_interest_rate", "demand_hours_this_year", "demand_kw",
    "demographic_scarcity", "deputies", "deputies_who_direct_work_for_you", "deputy_hours_a_year",
    "diffusion_index", "directed_hours_per_year", "directed_hours_this_year", "directors_extra",
    "disease_burden", "earliest_completion_year", "earliest_completion_years", "effective_schooling_flow",
    "elderly", "elite", "elite_ceiling", "elite_next_year", "emigration", "eminence", "employees_total",
    "expected_calendar_years_with_retries", "expected_failures", "familiarity", "farm_share_of_hours",
    "farm_share_of_working_hours", "food_cost_factor", "founder_alive", "founder_hours_available",
    "founder_hours_left", "founder_hours_sold_for_wages_this_year", "founder_hours_spent_teaching_this_year",
    "free_now", "fte", "gap", "general", "general_ceiling", "general_ceiling_now", "general_next_year",
    "grid_scale", "held_now", "hours_available_to_you_in_all", "hours_committed_so_far",
    "hours_still_to_work", "hours_the_market_can_supply", "hours_you_could_still_commission",
    "hours_you_have_commissioned", "hours_your_own_people_add", "household_places_in_all",
    "household_places_used", "idle_hours", "immigration", "in_bondage_for_debt", "interest_rate_on_arrears",
    "interest_rate_percent", "km", "labour_hours", "literacy_elite", "literacy_factor", "literacy_general",
    "local_trade_scarcity", "local_workshop_scale", "market_supply_hours_per_year",
    "material_distance_factor", "most_you_can_ever_have", "n", "normalized_change", "now", "nutrition_ratio",
    "opposition_factor", "people", "people_you_can_oversee", "population", "price_factor_over_book",
    "price_index", "printing_adopted", "protection", "purchasing_power_of_the_coin", "raw",
    "reference_population_at_start", "reputation", "resource_throttle", "room_for_more_people", "scandal",
    "scandal_now", "scandal_room", "scholars", "scholars_including_you", "schooling_flow", "share_below_peak",
    "society_price_level", "spare_hours_this_year", "spare_people_equivalent", "start", "the_town_there",
    "throttle", "total_founder_hours", "transmission_capacity_kw", "units", "value", "wage_index",
    "work_runs_at_share_of_plan", "worker_housing_places", "worker_years_equivalent", "working_age", "years",
    "years_following_the_chain_alone", "years_of_supply_it_takes", "years_solvent", "years_staffed",
    "you_employ", "you_employ_in_total", "you_now_employ", "your_hours", "your_hours_left_this_year",
    "your_hours_lost",
}
# Keys printed beside a native label that are counts, factors, hours, names or prose.
NOT_QUANTITY_KEYS = {
    "because", "chain_founder_hours", "chain_size", "chain_size_counting_what_you_have_built", "civ_domain_factor",
    "critical_path_years", "dearer_than_usual_by", "employees_total", "fix", "in_bondage_for_debt", "material",
    "material_distance_factor", "metal", "missing", "name", "opposition_factor", "price_index", "trade", "you_employ",
    "you_employ_in_total",
}


def python_files(*roots):
    for root in roots:
        for directory, _, names in os.walk(os.path.join(ROOT, root)):
            for name in sorted(names):
                if name.endswith(".py"):
                    yield os.path.join(directory, name)


def relative(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def docstring_ids(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant):
                found.add(id(node.body[0].value))
    return found


def hand_formatted_sentences():
    found = []
    for path in python_files("sim"):
        name = relative(path)
        if name.startswith("sim/tests/") or name in EXEMPT_SENTENCE_FILES:
            continue
        tree = ast.parse(open(path, encoding="utf-8").read())
        skipped = docstring_ids(tree)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skipped
                    and HAND_UNIT.search(node.value)):
                found.append("%s:%d %s" % (name, node.lineno, node.value[:70].replace("\n", " ")))
    return found


def code_nodes(kinds):
    """(file, node) for every node of the given kinds in sim/ outside the tests and the exempt files."""
    for path in python_files("sim"):
        name = relative(path)
        if name.startswith("sim/tests/") or name in EXEMPT_FORMAT_FILES or name in EXEMPT_SENTENCE_FILES:
            continue
        for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
            if isinstance(node, kinds):
                yield name, node


def hand_numbers():
    found = []
    for path in python_files("sim"):
        name = relative(path)
        if name.startswith("sim/tests/") or name in EXEMPT_FORMAT_FILES or name in EXEMPT_SENTENCE_FILES:
            continue
        tree = ast.parse(open(path, encoding="utf-8").read())
        skipped = docstring_ids(tree)
        found += ["%s:%d" % (name, node.lineno) for node in ast.walk(tree)
                  if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skipped
                  and HAND_NUMBER.search(node.value)]
    return found


def currency_word_calls():
    return ["%s:%d" % (name, node.lineno) for name, node in code_nodes((ast.Call,))
            if getattr(node.func, "id", getattr(node.func, "attr", "")) in ("money_word", "money_short")
            and name not in CURRENCY_WORD_EXEMPT]


def unconverted_money_arguments():
    """Sentences (a string % arguments) whose arguments name a money source without passing through money_text."""
    def bare(node):
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) in ("money_text", "round"):
            return
        if isinstance(node, ast.Attribute) and node.attr in MONEY_SOURCES:
            yield node.attr
        if isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", "")) in MONEY_SOURCES:
            yield getattr(node.func, "attr", getattr(node.func, "id", ""))
        for child in ast.iter_child_nodes(node):
            yield from bare(child)
    return ["%s:%d %s" % (name, node.lineno, sorted(set(bare(node.right))))
            for name, node in code_nodes((ast.BinOp,))
            if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
            and list(bare(node.right)) and name not in MONEY_ARGUMENT_EXEMPT]


def dict_keys(folder):
    for path in python_files(folder):
        for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
            if isinstance(node, ast.Dict):
                for key in node.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        yield relative(path), key.value


def keys_beside_native_labels(folder):
    """(file:line, key) for each reply key read in a statement whose string prints a native unit label."""
    for path in python_files(folder):
        tree = ast.parse(open(path, encoding="utf-8").read())
        for statement in ast.walk(tree):
            if not isinstance(statement, ast.stmt) or isinstance(
                    statement, (ast.FunctionDef, ast.ClassDef, ast.If, ast.For, ast.While, ast.With, ast.Try)):
                continue
            strings = [node.value for node in ast.walk(statement)
                       if isinstance(node, ast.Constant) and isinstance(node.value, str)]
            if not any(NATIVE_LABEL.search(text) and ("%" in text or "{" in text) for text in strings):
                continue
            for node in ast.walk(statement):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
                        and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    yield "%s:%d" % (relative(path), statement.lineno), node.args[0].value
                if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                    yield "%s:%d" % (relative(path), statement.lineno), node.slice.value


class NoHandFormattedUnits(unittest.TestCase):
    def setUp(self):
        U.set_registry(None)
        self.registry = U.registry()

    def test_no_engine_sentence_formats_a_quantity_beside_a_unit_word(self):
        found = hand_formatted_sentences()
        self.assertEqual(found, [], "use sim.engine.units_prose (mass_text, area_text, money_text, temperature_text)")

    def test_no_sentence_writes_a_number_with_separators_by_hand(self):
        found = hand_numbers()
        self.assertEqual(found, [], "money goes through money_text, a count or hours through plain_number")

    def test_nothing_outside_the_formatters_asks_for_the_currency_word(self):
        found = currency_word_calls()
        self.assertEqual(found, [], "a sum is written with units_prose.money_text, which reads the civilisation's words")

    def test_no_sentence_prints_a_sum_of_money_without_money_text(self):
        found = unconverted_money_arguments()
        self.assertEqual(found, [], "wrap the amount in units_prose.money_text")

    def test_the_scan_catches_a_hand_written_sentence(self):
        for sentence in ("it costs %s denarii", "bought {} tonnes", "%.0f ha of land", "up to %d kg", "net %s den/yr",
                         "held {:,.0f} t"):
            self.assertIsNotNone(HAND_UNIT.search(sentence), sentence)
        for sentence in ("%s tonnesless", "the t of it", "denarii are coins", "%s of %s"):
            self.assertIsNone(HAND_UNIT.search(sentence), sentence)

    def test_the_exempt_files_are_real_and_each_still_needs_the_exemption(self):
        for name in EXEMPT_SENTENCE_FILES:
            path = os.path.join(ROOT, name)
            self.assertTrue(os.path.isfile(path), name)
            tree = ast.parse(open(path, encoding="utf-8").read())
            skipped = docstring_ids(tree)
            hits = [node for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and id(node) not in skipped and HAND_UNIT.search(node.value)]
            self.assertTrue(hits, "%s no longer needs its exemption" % name)

    def test_the_format_exemptions_name_real_files(self):
        for name in list(EXEMPT_FORMAT_FILES) + list(CURRENCY_WORD_EXEMPT) + list(MONEY_ARGUMENT_EXEMPT):
            self.assertTrue(os.path.isfile(os.path.join(ROOT, name)), name)

    def test_every_quantity_like_reply_key_has_a_field_rule(self):
        missing = {key: path for path, key in dict_keys("sim/ui/proto")
                   if U.looks_like_quantity(self.registry, key) and not U.known_field(self.registry, key)
                   and key not in NOT_NUMERIC_KEYS}
        self.assertEqual(missing, {}, "add a field rule to data/world/units.json, or list the key as not numeric")

    def test_every_rounded_reply_field_is_ruled_tagged_or_not_a_unit_quantity(self):
        tagged_names = set()
        rounded = {}
        for path in python_files("sim/ui/proto"):
            for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
                if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "tagged":
                    tagged_names.update(keyword.arg for keyword in node.keywords if keyword.arg)
                if isinstance(node, ast.Dict):
                    for key, value in zip(node.keys, node.values):
                        if (isinstance(key, ast.Constant) and isinstance(key.value, str) and isinstance(value, ast.Call)
                                and getattr(value.func, "id", "") == "round"):
                            rounded.setdefault(key.value, relative(path))
        missing = {key: path for key, path in rounded.items()
                   if not U.known_field(self.registry, key) and key not in tagged_names
                   and key not in ROUND_NOT_A_UNIT_QUANTITY}
        self.assertEqual(missing, {}, "add a field rule, tag it with units.tagged where it is built, or list it as not a unit quantity")

    def test_every_key_printed_beside_a_native_label_has_a_field_rule(self):
        missing = {key: where for where, key in keys_beside_native_labels("sim/ui/proto")
                   if not U.known_field(self.registry, key) and key not in NOT_QUANTITY_KEYS}
        self.assertEqual(missing, {}, "add a field rule to data/world/units.json, or list the key as not a quantity")

    def test_no_screen_shows_a_temperature_and_a_future_one_is_covered_by_a_rule(self):
        """Temperature is on no screen or reply (the production data keeps it in the engine); a key that names
        one would have to match the temperature field rule."""
        names = [key for _, key in dict_keys("sim/ui") if re.search(r"temperature|celsius|kelvin|fahrenheit", key)]
        for key in names:
            rule = U.field_rule(self.registry, key)
            self.assertTrue(rule and rule["dimension"] == "temperature", key)
        self.assertEqual(U.field_rule(self.registry, "furnace_temperature_c")["dimension"], "temperature")
        shown = [path for path in python_files("sim/ui")
                 if re.search(r"(?i)\btemperature\b|\bcelsius\b", open(path, encoding="utf-8").read())
                 and "units" not in os.path.basename(path)]
        self.assertEqual([relative(path) for path in shown], [],
                         "a screen now mentions temperature: format it with units_prose.temperature_text")

    def test_the_detector_reads_the_registry_not_a_private_list(self):
        self.assertTrue(U.looks_like_quantity(self.registry, "annual_wage_bill"))
        self.assertFalse(U.looks_like_quantity(self.registry, "price_index"))
        self.assertFalse(U.looks_like_quantity(self.registry, "population"))


if __name__ == "__main__":
    unittest.main()
