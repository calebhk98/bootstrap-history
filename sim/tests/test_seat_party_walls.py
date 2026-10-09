"""No module names the founder as a party, a lender, a borrower or an agent where it should name the acting seat
(scans every module, so not a quick topic)."""
import ast
import pathlib

from .harness import *  # noqa: F401,F403

root = pathlib.Path(__file__).resolve().parents[1]
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
by_name, by_literal = [], []
for path in sorted(root.rglob("*.py")):
    relative = path.relative_to(root).as_posix()
    if relative.startswith("tests/"):
        continue
    source = path.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        named = (node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute)
                 else node.name if isinstance(node, (ast.alias, ast.ClassDef)) else None)
        if named in FORBIDDEN_NAMES or (isinstance(node, ast.Attribute) and node.attr == "founder"
                                        and isinstance(node.value, ast.Attribute) and node.value.attr == "goods_market"):
            by_name.append("%s:%d" % (relative, getattr(node, "lineno", 0)))
    if relative in LITERAL_ALLOWED:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == "founder":
            by_literal.append("%s:%d" % (relative, node.lineno))
check("no module uses a founder party constant", not by_name, by_name[:10])
check("no module writes the literal party id founder outside the seat's own definition", not by_literal, by_literal[:10])
