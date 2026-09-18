#!/usr/bin/env python3
"""Generate knowledge/README.md: the index that links every tech-tree node
to the entry in the knowledge library that tells you how to actually do it.

Run after editing either the tree or any knowledge module:
    python3 sim/build_index.py
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
    slug = heading.strip().lower()
    slug = re.sub(r"[`*]", "", slug)
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"\s+", "-", slug).strip("-")


def main():
    tree = json.load(open(os.path.join(ROOT, "data", "tech_tree.json")))
    nodes = tree["nodes"]
    slugs = {}          # file -> {tech_id: github anchor slug for the whole heading}
    anchors, files = {}, sorted(filename for filename in os.listdir(KB)
                                if filename.endswith(".md") and not filename.startswith("_")
                                and filename != "README.md")
    for filename in files:
        txt = open(os.path.join(KB, filename)).read()
        anchors[filename], slugs[filename] = set(), {}
        for line in txt.splitlines():
            match = re.match(r"^##\#?\s+`?([A-Za-z0-9_]+)`?(?=\s*[-:,])", line)
            if not match:
                continue
            tid = match.group(1)
            anchors[filename].add(tid)
            slug = github_slug(line.lstrip("#").strip())
            slugs[filename][tid] = slug
            # A heading may name SEVERAL ids before the dash, as
            # "### a, b, c - Name". Register them all against the same anchor,
            # otherwise everything after the first comma reports as undocumented.
            head = line.lstrip("#").split(" - ")[0]
            for extra in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", head):
                anchors[filename].add(extra)
                slugs[filename].setdefault(extra, slug)
            cur = tid
        # A module section covers a CLUSTER of nodes, not one. The heading names
        # a representative and an "Also covers:" line names the rest. Without
        # this, 700 nodes documented in a section still reported as undocumented
        # because their id was not a heading.
        cur = None
        for line in txt.splitlines():
            match = re.match(r"^##\#?\s+`?([A-Za-z0-9_]+)`?(?=\s*[-:])", line)
            if match:
                cur = match.group(1)
                continue
            also_covers_match = re.match(r"^\s*(?:\*\*)?Also covers:?(?:\*\*)?\s*(.+)$", line, re.I)
            if also_covers_match and cur:
                for tid in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", also_covers_match.group(1)):
                    anchors[filename].add(tid)
                    slugs[filename].setdefault(tid, slugs[filename].get(cur, cur))

    # Some nodes are institutional or political rather than technical, and their
    # "how to" lives in the top-level prose files rather than in a recipe module.
    parent_files = {filename for filename in os.listdir(ROOT) if filename.endswith(".md")}

    by_file = collections.defaultdict(list)
    broken_file, broken_anchor, prose = [], [], []
    bydesign, gap = [], []
    for node in nodes:
        filename, _, anchor = node["kb"].partition("#")
        filename = os.path.basename(filename)
        if not filename:
            # Capability rungs, materials and unobtainables are DEFINED by the
            # tree itself and need no separate recipe. Anything else with no
            # link is a genuine documentation gap and is reported as one.
            (bydesign if node["cat"] in ("capability", "material", "unobtainable")
             else gap).append(node["id"])
        elif filename in parent_files:
            prose.append((node, filename, anchor))
        elif filename in anchors:
            by_file[filename].append((node, anchor))
            if anchor and anchor not in anchors[filename]:
                broken_anchor.append((node["id"], node["kb"]))
        else:
            broken_file.append((node["id"], node["kb"]))

    out = ["# knowledge/ - the how-to library",
           "",
           "**This file is generated. Do not edit it.** Run `python3 sim/build_index.py`.",
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
    for filename in files:
        out.append("| [`%s`](%s) | %s | %d | %d |"
                   % (filename, filename, TITLES.get(filename, ""), len(anchors[filename]), len(by_file.get(filename, []))))
    out += ["",
            "### Nodes documented in the top-level prose files",
            "",
            "These are institutional, political and economic nodes. Their 'how to' is a",
            "strategy, not a procedure, so it lives outside the recipe library.",
            "",
            "| Node | Your hours | Documented in |", "|---|---:|---|"]
    for node, filename, anchor in sorted(prose, key=lambda entry: (entry[0]["id"], entry[0]["ph"])):
        out.append("| `%s` | %s | [`%s`](../%s) |" %
                   (node["id"], f"{node['ph']:,}", filename, filename))

    out += ["",
            "## Every tech-tree node, and where its recipe lives",
            "",
            "Sorted by module, then by node id.",
            ""]
    for filename in files:
        if not by_file.get(filename):
            continue
        out += ["### %s" % filename, "",
                "| Node | Your hours | Recipe |", "|---|---:|---|"]
        for node, anchor in sorted(by_file[filename], key=lambda entry: (entry[0]["id"], entry[0]["ph"])):
            link = ("[`%s`](%s#%s)" % (anchor, filename, slugs[filename].get(anchor, anchor))) if anchor else "_(module has no anchor)_"
            mark = "" if (not anchor or anchor in anchors[filename]) else " **BROKEN**"
            out.append("| `%s` | %s | %s%s |" %
                       (node["id"], f"{node['ph']:,}", link, mark))
        out.append("")

    # Inline cross-references written inside the modules themselves. Nothing
    # validated these before, and 7 of them were broken.
    parent_md = {filename for filename in os.listdir(ROOT) if filename.endswith(".md")}
    inline_bad = []
    for filename in files:
        txt = open(os.path.join(KB, filename)).read()
        for match in re.finditer(r"([0-9A-Za-z_]+\.md)#([A-Za-z0-9_]+)", txt):
            linked_file, linked_anchor = match.group(1), match.group(2)
            if linked_file in anchors:
                if linked_anchor not in anchors[linked_file]:
                    inline_bad.append((filename, linked_file + "#" + linked_anchor, "no such entry"))
            elif linked_file not in parent_md:
                inline_bad.append((filename, linked_file + "#" + linked_anchor, "no such file"))
    if inline_bad:
        out += ["## Broken cross-references inside the modules", ""]
        for source_file, target_ref, reason in inline_bad:
            out.append("- `%s` links to `%s`: %s" % (source_file, target_ref, reason))
        out.append("")

    out += ["## Documentation coverage", "",
            "| status | nodes |", "|---|---:|",
            "| linked to a specific recipe entry | %d |" % sum(1 for filename in files for node, anchor in by_file.get(filename, []) if anchor),
            "| linked to a domain module, no specific entry | %d |" % sum(1 for filename in files for node, anchor in by_file.get(filename, []) if not anchor),
            "| documented in a top-level prose file | %d |" % len(prose),
            "| no link BY DESIGN (capability rungs, materials, unobtainables) | %d |" % len(bydesign),
            "| **undocumented, a real gap** | **%d** |" % len(gap), ""]
    if gap:
        out += ["The undocumented nodes, listed so the gap is visible rather than hidden:", "",
                "`" + "`, `".join(sorted(gap)) + "`", ""]

    if broken_file or broken_anchor:
        out += ["## Broken links", ""]
        for node_id, kb_link in broken_file:
            out.append("- `%s` points at `%s`, which does not exist" % (node_id, kb_link))
        for node_id, kb_link in broken_anchor:
            out.append("- `%s` points at `%s`, but that module has no such `###` entry" % (node_id, kb_link))
        out.append("")

    open(os.path.join(KB, "README.md"), "w").write("\n".join(out) + "\n")
    print("wrote knowledge/README.md")
    print("  modules indexed : %d" % len(files))
    print("  nodes linked    : %d recipe + %d prose = %d of %d"
          % (sum(len(value) for value in by_file.values()), len(prose),
             sum(len(value) for value in by_file.values()) + len(prose), len(nodes)))
    print("  no link by design: %d   undocumented gap: %d" % (len(bydesign), len(gap)))
    print("  broken files    : %d" % len(broken_file))
    print("  broken anchors  : %d" % len(broken_anchor))
    print("  broken inline   : %d" % len(inline_bad))
    for source_file, target_ref, reason in inline_bad:
        print("     %-28s -> %-44s %s" % (source_file, target_ref, reason))
    for node_id, kb_link in broken_file + broken_anchor:
        print("     %-32s -> %s" % (node_id, kb_link))
    return 1 if (broken_file or broken_anchor or inline_bad) else 0

if __name__ == "__main__":
    sys.exit(main())
