"""Print what each cross-class method reference targets (writes, reads only, pure). Run from the repository root."""
import ast, collections, inspect, sys, textwrap
sys.path.insert(0, ".")
from sim.engine.core import Sim
CONTAINER_WRITES = {"append", "extend", "update", "pop", "add", "setdefault", "clear", "remove", "insert", "discard", "popitem", "sort"}
WRITE_VERBS = ("pay", "spend", "transfer", "receive", "hire", "fire", "add_", "remove_", "set_", "record", "grant", "take", "give",
               "post", "book", "charge", "credit", "debit", "settle", "buy", "sell", "start", "finish", "complete", "kill", "move", "apply", "assign", "release")
CACHE_WORDS = ("cache", "memo", "__dict__", "_seq", "version", "said", "log", "notice", "warn")
def root_name(node):
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
        node = node.func if isinstance(node, ast.Call) else node.value
    return node.id if isinstance(node, ast.Name) else None
def written_text(node):
    text = ast.unparse(node)
    return "cache" if text.startswith("self._") or text.startswith("scope[") else text
classes = [klass for klass in Sim.__mro__ if klass is not object and klass.__module__.startswith("sim.")]
trees = {klass: ast.parse(textwrap.dedent(inspect.getsource(klass))) for klass in classes}
definer, bodies = {}, {}
for klass in classes:
    for item in trees[klass].body[0].body:
        if isinstance(item, ast.FunctionDef) and item.name not in definer:
            definer[item.name], bodies[item.name] = klass, item
reads, writes, calls = {}, {}, {}
for name, function in bodies.items():
    aliases = {node.targets[0].id for node in ast.walk(function) if isinstance(node, ast.Assign) and len(node.targets) == 1
               and isinstance(node.targets[0], ast.Name) and root_name(node.value) == "self" and not isinstance(node.value, ast.Call)}
    owned = aliases | {"self"}
    reads[name], writes[name], calls[name] = False, False, set()
    for node in ast.walk(function):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            if node.attr in bodies: calls[name].add(node.attr)
            else: reads[name] = True
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AugAssign) else []
        for target in targets:
            if isinstance(target, (ast.Attribute, ast.Subscript)) and root_name(target) in owned \
                    and not any(word in written_text(target).lower() for word in CACHE_WORDS):
                writes[name] = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and root_name(node.func.value) in owned \
                and not (isinstance(node.func.value, ast.Name) and node.func.value.id == "self") \
                and (node.func.attr in CONTAINER_WRITES or node.func.attr.startswith(WRITE_VERBS)) \
                and not any(word in written_text(node.func.value).lower() for word in CACHE_WORDS):
            writes[name] = True
changed = True
while changed:
    changed = False
    for name in bodies:
        for flags in (reads, writes):
            if not flags[name] and any(flags[callee] for callee in calls[name]):
                flags[name] = changed = True
kinds = collections.Counter(); targets = collections.defaultdict(collections.Counter)
for klass in classes:
    for node in ast.walk(trees[klass]):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self" \
                and node.attr in definer and definer[node.attr] is not klass:
            kind = "writes" if writes[node.attr] else "reads only" if reads[node.attr] else "pure"
            kinds[kind] += 1; targets[kind][node.attr] += 1
print("cross-class references by what the target does:", dict(kinds))
print("distinct targets:", {kind: len(names) for kind, names in targets.items()})
print("most referenced readers:", targets["reads only"].most_common(30))
print("most referenced writers:", targets["writes"].most_common(30))
