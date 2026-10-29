"""The coupling between assembled modules, read from the shipped assembly's declarations.

For each module: the views and points it reads that another module publishes, the commands it sends that another module
applies, and how many other modules those reach. Then the directed dependency pairs, the largest group of modules that
can all reach one another, the reads the engine bridge still answers, and the reads of `legacy_*` views (the engine's live
objects handed out whole). These are declaration counts, not call counts: `python3 tools/measure/module_graph.py`,
`--modules` for the per-module table. Run from the repository root."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sim.assembly.api import FRAMEWORK_ID  # noqa: E402
from sim.engine import game_assembly  # noqa: E402
from sim.engine.bridge import BRIDGE_ID  # noqa: E402


def owners(specs):
    """{view or point name: module id}, {command class: module id}."""
    name_owner = {}
    for module_id, spec in specs.items():
        for view in spec.publishes:
            name_owner[view.name] = module_id
        for point in spec.extension_points:
            name_owner[point.name] = module_id
    command_owner = {command: module_id for module_id, spec in specs.items() for command, _handler in spec.applies}
    return name_owner, command_owner


def module_rows(specs):
    """[(module id, external reads, external sends, {modules depended on})], the bridge and the assembly left out as readers."""
    name_owner, command_owner = owners(specs)
    rows = []
    for module_id, spec in specs.items():
        if module_id in (BRIDGE_ID, FRAMEWORK_ID):
            continue
        reads = [name for name in tuple(spec.reads) + tuple(spec.optional_reads) if name_owner.get(name) not in (None, module_id)]
        sends = [command for command in spec.sends if command_owner.get(command) not in (None, module_id)]
        depended_on = {name_owner[name] for name in reads} | {command_owner[command] for command in sends}
        rows.append((module_id, reads, sends, depended_on))
    return rows


def largest_group(edges):
    """The size of the largest strongly connected group of the directed graph {node: set of nodes} (Tarjan)."""
    index, low, stack, on_stack, groups, counter = {}, {}, [], set(), [], [0]

    def visit(node):
        index[node] = low[node] = counter[0]
        counter[0] += 1
        stack.append(node)
        on_stack.add(node)
        for target in sorted(edges.get(node, ())):
            if target not in index:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in on_stack:
                low[node] = min(low[node], index[target])
        if low[node] == index[node]:
            group = []
            while True:
                member = stack.pop()
                on_stack.discard(member)
                group.append(member)
                if member == node:
                    break
            groups.append(group)

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10 * len(edges) + 100))
    for node in sorted(edges):
        if node not in index:
            visit(node)
    return max((len(group) for group in groups), default=0)


def summary(specs):
    rows = module_rows(specs)
    name_owner, _command_owner = owners(specs)
    edges = {module_id: depended_on - {BRIDGE_ID, FRAMEWORK_ID} for module_id, _reads, _sends, depended_on in rows}
    bridge_reads = sum(1 for module_id, reads, _sends, _deps in rows for name in reads if name_owner.get(name) == BRIDGE_ID)
    assembly_reads = sum(1 for module_id, reads, _sends, _deps in rows for name in reads if name_owner.get(name) == FRAMEWORK_ID)
    legacy_reads = sum(1 for module_id, reads, _sends, _deps in rows for name in reads if name.startswith("legacy_"))
    return {
        "modules": len(rows),
        "views published": sum(len(spec.publishes) for module_id, spec in specs.items() if module_id not in (BRIDGE_ID, FRAMEWORK_ID)),
        "dependency pairs between modules (the bridge and the assembly left out)": sum(len(targets) for targets in edges.values()),
        "modules that still depend on the engine bridge": sum(1 for _id, _reads, _sends, deps in rows if BRIDGE_ID in deps),
        "largest strongly connected group": largest_group(edges),
        "reads answered by the engine bridge": bridge_reads,
        "reads answered by the assembly (the seat registry)": assembly_reads,
        "reads of legacy_* views": legacy_reads,
    }


def main():
    specs = game_assembly.build(None, False).applied.specs
    for label, value in summary(specs).items():
        print("%s: %d" % (label, value))
    if "--modules" in sys.argv:
        for module_id, reads, sends, depended_on in sorted(module_rows(specs), key=lambda row: -len(row[3])):
            print("  %-16s reads %3d  sends %3d  modules depended on %2d" % (module_id, len(reads), len(sends), len(depended_on)))


if __name__ == "__main__":
    main()
