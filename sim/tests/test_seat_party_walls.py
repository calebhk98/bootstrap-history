"""No module names the founder as a party, a lender, a borrower or an agent where it should name the acting seat.
A source scan: the files that could offend are found by text first, so only those are parsed."""
QUICK_TOPIC = True

import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {"FOUNDER", "FOUNDER_LOAN", "FOUNDER_AGENT", "FOUNDER_ACTOR_ID", "FounderParty"}
# Modules where the literal "founder" is not a party id: the seat's own first id, the household facade's map of
# sub-states, the sub-state name in saves, and the plan key a firm uses to name who started it.
LITERAL_ALLOWED = {
    "engine/state_seat.py": "the first seat's id",
    "engine/state.py": "the first seat's id as the default acting seat",
    "agents/household.py": "the facade's map from field to the sub-state named founder",
    "engine/core_properties.py": "reads the founder sub-state",
    "engine/saveload.py": "the name of a seat section",
    "engine/settings.py": "reads the founder sub-state of a saved seat",
    "agents/firm_exit.py": "a firm's plan key naming who founded it",
    "agents/spinoff.py": "a firm's plan key naming who founded it",
    "agents/entry_round.py": "a firm's plan key naming who founded it",
}
MENTIONS = sorted(FORBIDDEN_NAMES) + ["goods_market", "'founder'", '"founder"']


def mentions():
    """(relative path, tree) of every non-test module that could break either rule."""
    for path in sorted(ROOT.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if not relative.startswith("tests/"):
            text = path.read_text()
            if any(mention in text for mention in MENTIONS):
                yield relative, ast.parse(text)


def forbidden_uses(tree):
    found = []
    for node in ast.walk(tree):
        named = (node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute)
                 else node.name if isinstance(node, (ast.alias, ast.ClassDef)) else None)
        if named in FORBIDDEN_NAMES or (isinstance(node, ast.Attribute) and node.attr == "founder"
                                        and isinstance(node.value, ast.Attribute) and node.value.attr == "goods_market"):
            found.append(getattr(node, "lineno", 0))
    return found


def founder_literals(tree):
    return [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Constant) and node.value == "founder"]


class PartyWallTests(unittest.TestCase):
    def test_no_module_uses_a_founder_party_constant(self):
        offenders = ["%s:%d" % (relative, number) for relative, tree in mentions() for number in forbidden_uses(tree)]
        self.assertEqual(offenders[:10], [])

    def test_no_module_writes_the_literal_party_id_founder_outside_the_seats_own_definition(self):
        offenders = ["%s:%d" % (relative, number) for relative, tree in mentions()
                     if relative not in LITERAL_ALLOWED for number in founder_literals(tree)]
        self.assertEqual(offenders[:10], [])

    def test_the_scan_finds_a_party_constant_and_a_literal_when_there_is_one(self):
        tree = ast.parse("lender = FOUNDER_LOAN\nparty = 'founder'\nseller = world.goods_market.founder\n")
        self.assertEqual(forbidden_uses(tree), [1, 3])
        self.assertEqual(founder_literals(tree), [2])


if __name__ == "__main__":
    unittest.main()
