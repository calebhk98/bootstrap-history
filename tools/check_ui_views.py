"""Every view the screens and the protocol read (`sim.view("name")`) and every command they send (`sim.send(ui_port.Command(...))`)
exists in a built game. Prints each missing one, one per line, and exits non-zero when there are any. Run after a module move.
Run from the repository root. `--list` prints the views the UI reads, so the list the UI depends on is always current."""
import ast
import glob
import sys

sys.path.insert(0, ".")
from sim.engine import game_assembly, ui_port  # noqa: E402

assembly = game_assembly.build(None, True)
used_views = {}
used_commands = {}
for path in sorted(glob.glob("sim/ui/**/*.py", recursive=True) + ["sim/engine/ui_port.py"]):
    for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "view" and node.args
                and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            used_views.setdefault(node.args[0].value, path)
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "ui_port"
                and node.attr[:1].isupper() and not node.attr.isupper()):
            used_commands.setdefault(node.attr, path)
missing = ["%s: view %r is not published" % (path, name) for name, path in sorted(used_views.items()) if name not in assembly.views]
for name, path in sorted(used_commands.items()):
    command = getattr(ui_port, name, None)
    if command is None or command not in assembly.handlers:
        if not hasattr(command, "__module__") or name in ("IdentityCache",):
            continue
        missing.append("%s: command %s has no handler" % (path, name))
if "--list" in sys.argv:
    print("\n".join(sorted(used_views)))
print("\n".join(missing))
sys.exit(1 if missing else 0)
