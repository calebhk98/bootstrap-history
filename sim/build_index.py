#!/usr/bin/env python3
"""Generate rome/knowledge/README.md: the index that links every tech-tree node
to the entry in the knowledge library that tells you how to actually do it.

Run after editing either the tree or any knowledge module:
    python3 rome/sim/build_index.py
It also reports broken links, which is the point of generating it rather than
maintaining it by hand.
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB   = os.path.join(ROOT, "knowledge")

TITLES = {
 "00_NONOBVIOUS_TRICKS.md": "The tricks that make everything else buildable. READ FIRST.",
 "10_metallurgy.md":        "Metallurgy, fuel and refractories",
 "20_chemistry.md":         "Chemistry, acids, alkalis and energetics",
 "30_glass_optics.md":      "Glass, optics and scientific instruments",
 "40_power_precision.md":   "Prime movers, machine tools and precision",
 "50_electricity.md":        "Electricity, magnetism and electrical machines",
 "55_semiconductors.md":    "Vacuum, high purity and semiconductors",
 "60_mathematics_method.md":"Mathematics, physics and the scientific method",
 "70_medicine_biology.md":  "Medicine, public health and biology",
 "75_agriculture_food.md":  "Agriculture, food and surplus",
 "80_information_printing.md":"Paper, printing and the survival of knowledge",
 "85_transport_civil.md":   "Transport, mining and civil engineering",
 "99_AUDIT.md":             "Adversarial audit of the technical modules",
}

def github_slug(heading):
    """Reproduce GitHub's heading-anchor algorithm.

    Lowercase, strip anything that is not a word character, space or hyphen,
    then turn spaces into hyphens. Underscores SURVIVE, which is the detail an
    earlier version of this script got wrong: it emitted "#zinc-metal" for a
    heading whose real anchor is "#zinc_metal---zinc-metal-by-downward-distillation".
    Every link in the generated index was silently broken.
    """
    s = heading.strip().lower()
    s = re.sub(r"[`*]", "", s)
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"\s+", "-", s).strip("-")


def main():
    tree = json.load(open(os.path.join(ROOT, "data", "tech_tree.json")))
    nodes = tree["nodes"]

    slugs = {}          # file -> {tech_id: github anchor slug for the whole heading}
    anchors, files = {}, sorted(f for f in os.listdir(KB)
                                if f.endswith(".md") and not f.startswith("_")
                                and f != "README.md")
    for f in files:
        txt = open(os.path.join(KB, f)).read()
        anchors[f], slugs[f] = set(), {}
        for line in txt.splitlines():
            m = re.match(r"^##\#?\s+`?([A-Za-z0-9_]+)`?(?=\s*[-:,])", line)
            if not m:
                continue
            tid = m.group(1)
            anchors[f].add(tid)
            slug = github_slug(line.lstrip("#").strip())
            slugs[f][tid] = slug
            # A heading may name SEVERAL ids before the dash, as
            # "### a, b, c - Name". Register them all against the same anchor,
            # otherwise everything after the first comma reports as undocumented.
            head = line.lstrip("#").split(" - ")[0]
            for extra in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", head):
                anchors[f].add(extra)
                slugs[f].setdefault(extra, slug)
            cur = tid
        # A module section covers a CLUSTER of nodes, not one. The heading names
        # a representative and an "Also covers:" line names the rest. Without
        # this, 700 nodes documented in a section still reported as undocumented
        # because their id was not a heading.
        cur = None
        for line in txt.splitlines():
            m = re.match(r"^##\#?\s+`?([A-Za-z0-9_]+)`?(?=\s*[-:])", line)
            if m:
                cur = m.group(1)
                continue
            a = re.match(r"^\s*(?:\*\*)?Also covers:?(?:\*\*)?\s*(.+)$", line, re.I)
            if a and cur:
                for tid in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", a.group(1)):
                    anchors[f].add(tid)
                    slugs[f].setdefault(tid, slugs[f].get(cur, cur))

    # Some nodes are institutional or political rather than technical, and their
    # "how to" lives in the top-level prose files rather than in a recipe module.
    parent_files = {f for f in os.listdir(ROOT) if f.endswith(".md")}

    by_file = collections.defaultdict(list)
    broken_file, broken_anchor, prose = [], [], []
    bydesign, gap = [], []
    for n in nodes:
        f, _, a = n["kb"].partition("#")
        f = os.path.basename(f)
        if not f:
            # Capability rungs, materials and unobtainables are DEFINED by the
            # tree itself and need no separate recipe. Anything else with no
            # link is a genuine documentation gap and is reported as one.
            (bydesign if n["cat"] in ("capability", "material", "unobtainable")
             else gap).append(n["id"])
        elif f in parent_files:
            prose.append((n, f, a))
        elif f in anchors:
            by_file[f].append((n, a))
            if a and a not in anchors[f]:
                broken_anchor.append((n["id"], n["kb"]))
        else:
            broken_file.append((n["id"], n["kb"]))

    out = ["# knowledge/ - the how-to library",
           "",
           "**This file is generated. Do not edit it.** Run `python3 rome/sim/build_index.py`.",
           "",
           "A tech tree that says *microscope requires glass* is useless to someone who does",
           "not already know that one melted bead of glass gives 250x. The tree in",
           "`../data/tech_tree.json` says WHAT and IN WHAT ORDER. These modules say HOW, at a",
           "level of detail a competent non-specialist can act on: masses, ratios,",
           "temperatures with Roman-observable proxies, vessel materials, how to tell it",
           "worked, how it fails, what it costs, and what it will do to you.",
           "",
           "## Start here",
           "",
           "**[`00_NONOBVIOUS_TRICKS.md`](00_NONOBVIOUS_TRICKS.md)** is the index of specific",
           "physical tricks: the glass-bead microscope, the three-plate method, downward zinc",
           "distillation, the Sprengel pump, zone refining, and the rest. If you read one file",
           "in this directory, read that one.",
           "",
           "## Modules",
           "",
           "| Module | Subject | Entries | Tree nodes it documents |",
           "|---|---|---:|---:|"]
    for f in files:
        out.append("| [`%s`](%s) | %s | %d | %d |"
                   % (f, f, TITLES.get(f, ""), len(anchors[f]), len(by_file.get(f, []))))
    out += ["",
            "### Nodes documented in the top-level prose files",
            "",
            "These are institutional, political and economic nodes. Their 'how to' is a",
            "strategy, not a procedure, so it lives outside the recipe library.",
            "",
            "| Node | Tier | Your hours | Documented in |", "|---|---:|---:|---|"]
    for n, f, a in sorted(prose, key=lambda x: (x[0]["tier"], x[0]["id"])):
        out.append("| `%s` | %d | %s | [`%s`](../%s) |" % (n["id"], n["tier"], f"{n['ph']:,}", f, f))

    out += ["",
            "## Every tech-tree node, and where its recipe lives",
            "",
            "Sorted by module, then by tier. `tier 0` is knowledge you carry in your head;",
            "`tier 5` is the semiconductor endgame.",
            ""]
    for f in files:
        if not by_file.get(f):
            continue
        out += ["### %s" % f, "",
                "| Node | Tier | Your hours | Recipe |", "|---|---:|---:|---|"]
        for n, a in sorted(by_file[f], key=lambda x: (x[0]["tier"], x[0]["id"])):
            link = ("[`%s`](%s#%s)" % (a, f, slugs[f].get(a, a))) if a else "_(module has no anchor)_"
            mark = "" if (not a or a in anchors[f]) else " **BROKEN**"
            out.append("| `%s` | %d | %s | %s%s |" % (n["id"], n["tier"], f"{n['ph']:,}", link, mark))
        out.append("")

    # Inline cross-references written inside the modules themselves. Nothing
    # validated these before, and 7 of them were broken.
    parent_md = {f for f in os.listdir(ROOT) if f.endswith(".md")}
    inline_bad = []
    for f in files:
        txt = open(os.path.join(KB, f)).read()
        for m in re.finditer(r"([0-9A-Za-z_]+\.md)#([A-Za-z0-9_]+)", txt):
            fn, an = m.group(1), m.group(2)
            if fn in anchors:
                if an not in anchors[fn]:
                    inline_bad.append((f, fn + "#" + an, "no such entry"))
            elif fn not in parent_md:
                inline_bad.append((f, fn + "#" + an, "no such file"))
    if inline_bad:
        out += ["## Broken cross-references inside the modules", ""]
        for a_, b_, c_ in inline_bad:
            out.append("- `%s` links to `%s`: %s" % (a_, b_, c_))
        out.append("")

    out += ["## Documentation coverage", "",
            "| status | nodes |", "|---|---:|",
            "| linked to a specific recipe entry | %d |" % sum(1 for f in files for n, a in by_file.get(f, []) if a),
            "| linked to a domain module, no specific entry | %d |" % sum(1 for f in files for n, a in by_file.get(f, []) if not a),
            "| documented in a top-level prose file | %d |" % len(prose),
            "| no link BY DESIGN (capability rungs, materials, unobtainables) | %d |" % len(bydesign),
            "| **undocumented, a real gap** | **%d** |" % len(gap), ""]
    if gap:
        out += ["The undocumented nodes, listed so the gap is visible rather than hidden:", "",
                "`" + "`, `".join(sorted(gap)) + "`", ""]

    if broken_file or broken_anchor:
        out += ["## Broken links", ""]
        for i, k in broken_file:
            out.append("- `%s` points at `%s`, which does not exist" % (i, k))
        for i, k in broken_anchor:
            out.append("- `%s` points at `%s`, but that module has no such `###` entry" % (i, k))
        out.append("")

    open(os.path.join(KB, "README.md"), "w").write("\n".join(out) + "\n")
    print("wrote knowledge/README.md")
    print("  modules indexed : %d" % len(files))
    print("  nodes linked    : %d recipe + %d prose = %d of %d"
          % (sum(len(v) for v in by_file.values()), len(prose),
             sum(len(v) for v in by_file.values()) + len(prose), len(nodes)))
    print("  no link by design: %d   undocumented gap: %d" % (len(bydesign), len(gap)))
    print("  broken files    : %d" % len(broken_file))
    print("  broken anchors  : %d" % len(broken_anchor))
    print("  broken inline   : %d" % len(inline_bad))
    for a_, b_, c_ in inline_bad:
        print("     %-28s -> %-44s %s" % (a_, b_, c_))
    for i, k in broken_file + broken_anchor:
        print("     %-32s -> %s" % (i, k))
    return 1 if (broken_file or broken_anchor or inline_bad) else 0

if __name__ == "__main__":
    sys.exit(main())
