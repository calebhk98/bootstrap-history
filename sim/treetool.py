#!/usr/bin/env python3
"""Tech-tree merge and PER-TECHNOLOGY audit.

The point of this file is the `judge` command.

The first version of this project graded itself on ONE number: what year the
simulation reached a transistor. That is the wrong test. A tree can produce a
plausible-looking end date while being wrong about almost every node in it.
The right test is whether each technology, taken ON ITS OWN, is honestly
specified: does it declare the capabilities it actually needs, is its cost
proportionate, could someone holding only its prerequisites really build it.

`judge` scores every node in isolation and reports the defects by name.

    python3 sim/treetool.py merge          # branches -> tech_tree.json
    python3 sim/treetool.py judge          # score every node, summary
    python3 sim/treetool.py judge --full   # every defect, node by node
    python3 sim/treetool.py judge --id X   # one node's report card
    python3 sim/treetool.py judge --grade D  # only nodes at or below D
"""
import argparse, json, os, re, sys, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
BR   = os.path.join(DATA, "branches")
TREE = os.path.join(DATA, "tech_tree.json")

def load_trades():
    """Read the trade list from prices.json rather than hardcoding it, so adding
    a trade to the price file is enough to make it usable."""
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    return set(trade for trade in prices["wage_rates_denarii_per_hour"] if not trade.startswith("_"))

# Schema v2. `yrs`, `sus` and `gov` are v1 and are backfilled, not demanded.
# Only these are genuinely required. Everything else has a sane default, because
# rejecting a whole node over a missing `up` throws away real work.
# Availability is described by prerequisites, capabilities, and costs rather
# than a universal numeric rank.
REQUIRED = ["id","name","cat","pre","note"]
DEFAULTS = {"ph":60,"lab":{},"mat":{},"cap":200,"up":40,"risk":0.15,"rev":0,
            "sch":0,"art":1,"conf":"C","kb":""}

def _num(v, d=0.0):
    """Branch authors sometimes write a number as a string, or as a range like
    '200-400'. Coerce rather than crash, and fall back to the default."""
    if isinstance(v, (int, float)): return float(v)
    if isinstance(v, str):
        match = re.findall(r"-?\d+(?:\.\d+)?", v)
        if match: return float(match[0])
    return float(d)


def normalise_v2(n):
    for field, value in DEFAULTS.items():
        n.setdefault(field, json.loads(json.dumps(value)))
    for field, default in (("ph",60),("cap",200),("up",40),("risk",0.15),("rev",0),
                 ("sch",0),("art",1)):
        n[field] = _num(n.get(field), default)
    n["risk"] = min(0.95, max(0.0, n["risk"]))
    for fld in ("lab","mat"):
        if not isinstance(n.get(fld), dict): n[fld] = {}
        else: n[fld] = {code: _num(value, 0) for code, value in n[fld].items()}
    if not isinstance(n.get("pre"), list): n["pre"] = []
    if not isinstance(n.get("traits"), list): n["traits"] = []
    """Accept either schema and leave the node in v2 shape with v1 fields
    backfilled, so the simulator and the audit keep working during the change."""
    if "build_yrs" not in n and "yrs" in n:
        years = float(n.get("yrs", 0) or 0)
        if years >= 5:
            n["build_yrs"], n["adopt_yrs"] = min(3.0, years / 3.0), years
        else:
            n["build_yrs"], n["adopt_yrs"] = years, 0.0
    n.setdefault("build_yrs", 0.0); n.setdefault("adopt_yrs", 0.0)
    n["yrs"] = max(float(n["build_yrs"]), float(n["adopt_yrs"]))
    n.setdefault("req_any", []); n.setdefault("traits", [])
    n.setdefault("dev_years", None); n.setdefault("dev_people", None)
    # v1 scalars are derived from traits so old code paths still run
    n.setdefault("gov", 0); n.setdefault("sus", 0)
    return n

# ---------------------------------------------------------------- MERGE
def load_aliases():
    path = os.path.join(BR, "ALIASES.json")
    if not os.path.exists(path):
        return {}, set()
    aliases = json.load(open(path))
    return aliases.get("alias", {}), set(aliases.get("drop", []))


def load_prices():
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    return set(material for material in prices["purchase_prices_denarii"] if not material.startswith("_"))


def cmd_merge(a):
    goods = load_prices()
    TRADES = load_trades()
    alias, dropset = load_aliases()
    base = json.load(open(TREE))
    # Ids retired by deduplication. Branch files still contain both spellings
    # of a technology that two authors invented independently, so without this
    # the next merge silently resurrects every duplicate.
    retired = base.get("meta", {}).get("merged_duplicate_ids", {})
    nodes = {node["id"]: normalise_v2(node) for node in base["nodes"]}
    for node in nodes.values():
        node.setdefault("_src", "core")
    errs, warns, added = [], [], 0

    for filename in sorted(os.listdir(BR)):
        if not filename.endswith(".json") or filename == "ALIASES.json":
            continue
        try:
            batch = json.load(open(os.path.join(BR, filename)))
        except Exception as e:
            errs.append("%s: unparseable JSON: %s" % (filename, e))
            continue
        if not isinstance(batch, list):
            errs.append("%s: top level is not a list" % filename)
            continue

        # Branch authors routinely refer to their OWN nodes without the file's
        # id prefix: a file of ag2_* nodes asks for "coulter" when it means
        # "ag2_coulter". Left alone the prereq resolver below silently drops
        # those edges, which makes the technology look cheaper and earlier than
        # it is. Repair them here, but only where the fix is unambiguous.
        own = {node["id"] for node in batch if isinstance(node, dict) and "id" in node}
        prefixes = set()
        for node_id in own:
            if "_" in node_id:
                prefixes.add(node_id.split("_", 1)[0] + "_")
        for node in batch:
            if not isinstance(node, dict):
                continue
            fixed = []
            for prereq in node.get("pre", []):
                if prereq in own or prereq in nodes:
                    fixed.append(prereq)
                    continue
                cands = {prefix + prereq for prefix in prefixes if prefix + prereq in own}
                if len(cands) == 1:
                    q = cands.pop()
                    fixed.append(q)
                    warns.append("%s: %s self-ref '%s' -> '%s'" % (filename, node.get("id", "?"), prereq, q))
                else:
                    fixed.append(prereq)
            if "pre" in node:
                node["pre"] = fixed

        for node in batch:
            missing = [field for field in REQUIRED if field not in node]
            if missing:
                errs.append("%s: %s missing fields %s" % (filename, node.get("id", "?"), missing))
                continue
            if node["id"] in retired:
                warns.append("%s: %s was merged into %s, skipping"
                             % (filename, node["id"], retired[node["id"]]))
                continue
            if node["id"] in nodes:
                warns.append("%s: duplicate id %s, keeping the first" % (filename, node["id"]))
                continue
            # Tier 9 meant UNOBTAINABLE and that concept was abolished: nothing
            # is unobtainable, only elsewhere. A new branch reintroduced it on
            normalise_v2(node)
            # resolve trade aliases rather than silently dropping the labour,
            # which would make the technology look cheaper than it is
            lab = {}
            for trade, hours in node["lab"].items():
                resolved_trade = alias.get(trade, trade)
                if resolved_trade in TRADES:
                    lab[resolved_trade] = lab.get(resolved_trade, 0) + hours
                else:
                    warns.append("%s: %s unknown trade '%s', dropped" % (filename, node["id"], trade))
            node["lab"] = lab
            materials = {}
            for material, q in node["mat"].items():
                resolved_material = alias.get(material, material)
                if resolved_material not in goods:
                    # generic fallbacks for the shapes authors actually write:
                    # "mat_beeswax" -> "beeswax_kg", "plaster" -> "plaster_kg"
                    for cand in (resolved_material[4:] + "_kg" if resolved_material.startswith("mat_") else None,
                                 resolved_material + "_kg", resolved_material.replace("mat_", "")):
                        if cand and cand in goods:
                            resolved_material = cand
                            break
                if resolved_material in dropset or material in dropset:
                    warns.append("%s: %s '%s' is a technology not a material, dropped" % (filename, node["id"], material))
                    continue
                if resolved_material in goods:
                    materials[resolved_material] = materials.get(resolved_material, 0) + q
                else:
                    warns.append("%s: %s UNPRICED material '%s', dropped" % (filename, node["id"], material))
            node["mat"] = materials
            # Branch authors keep writing the RECIPE PROSE into the kb link
            # field. Left alone it reports as a broken link to a file whose
            # name is a sentence. Move it to note where note is empty and
            # clear the field, so it reports as an honest documentation gap.
            kb_field = str(node.get("kb", "")).strip()
            if kb_field and not re.match(r"^\d\d_[A-Za-z0-9_]+\.md(#|$)", kb_field):
                if not str(node.get("note", "")).strip():
                    node["note"] = kb_field
                kb_field = ""
            node["kb"] = kb_field
            node["_src"] = filename
            nodes[node["id"]] = node
            added += 1

    # resolve prerequisites
    dangling = collections.Counter()
    for node in nodes.values():
        node["pre"] = [retired.get(prereq, prereq) for prereq in node["pre"]]
        for group in node.get("req_any", []):
            group["options"] = {retired.get(option, option): quantity for option, quantity in group.get("options", {}).items()}
        keep = []
        for prereq in node["pre"]:
            if prereq in nodes:
                keep.append(prereq)
            else:
                dangling[prereq] += 1
                warns.append("%s: dropped unresolvable prereq '%s'" % (node["id"], prereq))
        node["pre"] = keep

    # break any cycles by dropping the back edge, reporting each one
    order, state = [], {}
    def dfs(i, stack):
        if state.get(i) == 2:
            return
        if state.get(i) == 1:
            back = stack[-1]
            nodes[back]["pre"] = [prereq for prereq in nodes[back]["pre"] if prereq != i]
            errs.append("CYCLE broken: removed %s -> %s" % (back, i))
            return
        state[i] = 1
        for prereq in list(nodes[i]["pre"]):
            dfs(prereq, stack + [i])
        state[i] = 2
        order.append(i)
    for node_id in list(nodes):
        dfs(node_id, [])

    base["nodes"] = [nodes[node_id] for node_id in sorted(nodes)]
    base["meta"]["goal_node"] = "point_contact_transistor"
    _write_json(base, TREE, a)

    print("merged  : %d nodes (%d added from branches)" % (len(nodes), added))
    print("errors  : %d" % len(errs))
    for e in errs[:40]:
        print("   " + e)
    print("warnings: %d" % len(warns))
    for warning in warns[:25]:
        print("   " + warning)
    if len(warns) > 25:
        print("   ... %d more" % (len(warns) - 25))
    if dangling:
        print("\nmost-wanted unresolved prereq ids (candidates for new nodes):")
        for prereq_id, value in dangling.most_common(20):
            print("   %-40s wanted by %d nodes" % (prereq_id, value))
    return 0


# ---------------------------------------------------------------- JUDGE
CAP_PREFIX = "cap_"

# Categories that are IDEAS, not artefacts. A theorem needs no furnace, and an
# earlier version of this audit cheerfully demanded a vacuum rung for Boolean
# algebra because the word "vacuum tube" appeared in its note. Keyword matching
# on prose is a blunt instrument and this is the guard rail.
ABSTRACT_CATS = {"mathematics","physics","theory","knowledge","social","institution",
                 "foundation","capability","unobtainable","information","method","logic",
                 "computing_theory","organization","organisation"}

# Deliberately narrow. A word that merely MENTIONS a capability is not evidence
# that the technology needs it; only words naming the physical operation count.
HEAT_WORDS = ("furnace","kiln","smelt","forge","calcin","roast","anneal","sinter",
              "crucible","blast furnace","retort","molten","tempering","quench")
TOL_WORDS  = ("tolerance","machined","bored","lathe","gauge block","ball bearing",
              "lead screw","piston","cylinder bore","micrometer","ground surface","lapped")
VAC_WORDS  = ("vacuum","evacuat","getter","cathode ray","discharge tube","incandescent",
              "torr","exhausted envelope")
PUR_WORDS  = ("zone refin","single crystal","ultrapure","semiconductor grade","dopant",
              "parts per billion","high purity","electrorefin")
ELEC_WORDS = ("dynamo","electric motor","electrolysis","electroplat","arc lamp",
              "generator","alternating current","transformer","electric furnace")


def closure(nodes, k):
    seen, stack = set(), [k]
    while stack:
        ancestor_id = stack.pop()
        if ancestor_id in seen:
            continue
        seen.add(ancestor_id)
        stack.extend(nodes[ancestor_id]["pre"])
    return seen


def judge_node(n, nodes, stats):
    """Score one technology using its declared graph and category, not a rank."""
    defects = []
    if n["cat"] in ABSTRACT_CATS:
        if len(n["note"]) < 60:
            defects.append(("NOTE-THIN", "note is %d characters" % len(n["note"])))
        if n["conf"] not in ("A", "B", "C"):
            defects.append(("NO-CONF", "confidence not stated"))
        return max(0, 100 - len(defects) * 12), defects

    ancestry = closure(nodes, n["id"])
    caps = {node_id for node_id in ancestry if node_id.startswith(CAP_PREFIX)}
    text = (n["name"] + " " + n["note"]).lower()
    unob = [node_id for node_id in ancestry if nodes[node_id]["cat"] == "unobtainable"]
    physical = bool(n.get("mat")) or n.get("cap", 0) >= 200
    if not caps and physical and len(ancestry) >= 3 and n["cat"] not in (
            "social", "institution", "mathematics", "physics", "foundation",
            "information", "capability"):
        defects.append(("CAP-NONE", "physical work with no capability rung in its chain "
                              "(furnace, tolerance, vacuum, purity, or power)"))

    def want(words, prefix, label):
        if any(word in text for word in words) and not any(cap_id.startswith(prefix) for cap_id in caps):
            defects.append(("CAP-" + label, "reads as needing a %s rung but none appears "
                                      "in its prerequisite chain" % label.lower()))
    want(HEAT_WORDS, "cap_heat_", "HEAT")
    want(TOL_WORDS, "cap_tol_", "TOL")
    want(VAC_WORDS, "cap_vac_", "VAC")
    want(PUR_WORDS, "cap_pure_", "PURITY")
    if any(word in text for word in ELEC_WORDS) and not any(cap_id.startswith("cap_power_") for cap_id in caps):
        defects.append(("CAP-POWER", "electrical work with no power rung in its chain"))

    if len(n["pre"]) < 2 and 10 <= len(ancestry) < 25:
        defects.append(("SHALLOW", "%d direct prerequisite(s) and an ancestry only %d nodes deep"
                             % (len(n["pre"]), len(ancestry))))
    if unob and n["cat"] != "unobtainable":
        defects.append(("BLOCKED", "depends on %s, which is marked UNOBTAINABLE"
                             % ", ".join(sorted(unob)[:3])))

    category = n["cat"]
    med_cost = stats["cost"].get(category, 1)
    cost = n["_total_cost"]
    if med_cost > 0 and cost > med_cost * 25:
        defects.append(("COST-HIGH", "costs %s den, about %.0fx the median for category %s"
                               % (f"{cost:,.0f}", cost / med_cost, category)))
    if n["ph"] > 2000:
        defects.append(("HOURS-HIGH", "%s founder-hours, which is %.1f%% of a working life"
                                % (f"{n['ph']:,}", 100.0 * n["ph"] / 72000)))
    if len(ancestry) >= 3 and n["ph"] == 0 and n["cat"] not in ("capability", "material"):
        defects.append(("HOURS-ZERO", "non-foundational work costs the founder no hours"))
    if n.get("adopt_yrs", 0) >= 5 and n["yrs"] < 1:
        defects.append(("NO-FLOOR", "long adoption has a calendar floor under a year"))
    if len(n["note"]) < 60:
        defects.append(("NOTE-THIN", "note is %d characters" % len(n["note"])))
    if not n.get("kb") and n["cat"] not in ("capability", "material", "unobtainable"):
        defects.append(("NO-RECIPE", "no knowledge-base link"))
    if n["conf"] not in ("A", "B", "C"):
        defects.append(("NO-CONF", "confidence not stated"))
    if len(ancestry) >= 3 and not n.get("traits") and n["sus"] == 0 and n["gov"] == 0 \
            and n["cat"] not in ("capability", "material", "unobtainable", "mathematics", "physics"):
        defects.append(("SOCIAL-FLAT", "no traits and no scalar gov/sus"))

    weights = {"NO-RECIPE": 1, "CAP-NONE": 3, "CAP-HEAT": 2, "CAP-TOL": 2,
               "CAP-VAC": 2, "CAP-PURITY": 2, "CAP-POWER": 2, "SHALLOW": 3,
               "BLOCKED": 3, "COST-HIGH": 1, "HOURS-HIGH": 1, "HOURS-ZERO": 1,
               "NO-FLOOR": 1, "NOTE-THIN": 2, "NO-CONF": 1, "SOCIAL-FLAT": 1}
    penalty = sum(weights.get(code, 1) for code, _ in defects)
    return max(0, int(round(100 - penalty * 6))), defects

def grade(s):
    return "A" if s >= 90 else "B" if s >= 78 else "C" if s >= 64 else "D" if s >= 50 else "F"


def cmd_judge(a):
    tree = json.load(open(TREE))
    nodes = {node["id"]: node for node in tree["nodes"]}
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    wages = {trade: value["rate"] for trade, value in prices["wage_rates_denarii_per_hour"].items() if not trade.startswith("_")}
    goods = {material: value["p"] for material, value in prices["purchase_prices_denarii"].items() if not material.startswith("_")}
    for node in nodes.values():
        node["_total_cost"] = (sum(wages.get(trade, 0) * hours for trade, hours in node["lab"].items())
                            + sum(goods.get(material, 0) * quantity for material, quantity in node["mat"].items()) + node["cap"])

    by_category_cost = collections.defaultdict(list)
    for node in nodes.values():
        by_category_cost[node["cat"]].append(node["_total_cost"])
    stats = {"cost": {cat: statistics.median(value)
                      for cat, value in by_category_cost.items()}}

    results = {}
    for node_id, node in nodes.items():
        results[node_id] = judge_node(node, nodes, stats)

    if a.id:
        if a.id not in nodes:
            near = [node_id for node_id in nodes if a.id.lower() in node_id.lower()]
            raise SystemExit("unknown node. near matches: %s" % (", ".join(near[:10]) or "none"))
        node, (score, node_defects) = nodes[a.id], results[a.id]
        print("%s  [%s]" % (node["name"], node["id"]))
        print("=" * 78)
        print("grade %s (%d/100)   %s   confidence %s"
              % (grade(score), score, node["cat"], node["conf"]))
        print("direct prerequisites : %d   full ancestry : %d nodes"
              % (len(node["pre"]), len(closure(nodes, a.id)) - 1))
        print("cost %s den   founder-hours %s   calendar floor %.1f yr   risk %.0f%%"
              % (f"{node['_total_cost']:,.0f}", f"{node['ph']:,}", node["yrs"], 100 * node["risk"]))
        caps = sorted(cap_id for cap_id in closure(nodes, a.id) if cap_id.startswith("cap_"))
        print("capability rungs in its chain: %s" % (", ".join(caps) if caps else "NONE"))
        print("\n%s\n" % node["note"])
        if node_defects:
            print("DEFECTS")
            for code, msg in node_defects:
                print("  [%s] %s" % (code, msg))
        else:
            print("No defects found by the automated checks.")
        return 0

    dist = collections.Counter(grade(score) for score, _ in results.values())
    defects = collections.Counter()
    for score, node_defects in results.values():
        for code, _ in node_defects:
            defects[code] += 1

    print("PER-TECHNOLOGY AUDIT: every node judged on its own, not on the end date")
    print("=" * 78)
    print("nodes judged : %d" % len(nodes))
    print("mean score   : %.1f/100" % statistics.mean(score for score, _ in results.values()))
    print("grades       : " + "  ".join("%s %d (%.0f%%)" % (grade_letter, dist[grade_letter], 100.0 * dist[grade_letter] / len(nodes))
                                        for grade_letter in "ABCDF"))
    print("\nDEFECTS BY FREQUENCY")
    for code, value in defects.most_common():
        print("   %-12s %4d  (%.0f%% of nodes)" % (code, value, 100.0 * value / len(nodes)))
    print("\nWORST NODES")
    worst = sorted(results.items(), key=lambda x: x[1][0])[:20]
    for node_id, (score, node_defects) in worst:
        print("   %-34s %3d %s  %s" % (node_id[:34], score, grade(score), ", ".join(code for code, _ in node_defects[:4])))
    if a.grade:
        floor = "FDCBA".index(a.grade.upper())
        print("\nALL NODES AT GRADE %s OR WORSE" % a.grade.upper())
        for node_id, (score, node_defects) in sorted(results.items(), key=lambda x: x[1][0]):
            if "FDCBA".index(grade(score)) <= floor:
                print("   %-34s %3d %s  %s" % (node_id[:34], score, grade(score), ", ".join(code for code, _ in node_defects)))
    if a.full:
        print("\nFULL REPORT")
        for node_id, (score, node_defects) in sorted(results.items(), key=lambda x: x[1][0]):
            if node_defects:
                print("\n%s  %d %s" % (node_id, score, grade(score)))
                for code, message in node_defects:
                    print("    [%s] %s" % (code, message))
    _write_json({node_id: {"score": score, "grade": grade(score), "defects": [code for code, _ in node_defects]}
                 for node_id, (score, node_defects) in results.items()},
                os.path.join(DATA, "judgement.json"), a)
    if not getattr(a, "dry_run", False):
        print("\nwrote data/judgement.json")
    return 0


# ---------------------------------------------------------------- REPAIR
PREFIX_MODULE = {
 "fud_":"75_agriculture_food.md","prn_":"80_information_printing.md",
 "lnd_":"85_transport_civil.md","sea_":"85_transport_civil.md","air_":"85_transport_civil.md",
 "pwr_":"40_power_precision.md","chm_":"20_chemistry.md","met_":"10_metallurgy.md",
 "prc_":"40_power_precision.md","med_":"70_medicine_biology.md","civ_":"85_transport_civil.md",
 "opt_":"30_glass_optics.md","tex_":"90_textiles.md","hom_":"91_household.md",
 # schema v2 branches
 "exp_":"95_expeditions.md","fin_":"96_finance.md","mil_":"97_military.md",
 "ch2_":"20_chemistry.md","el2_":"50_electricity.md","mfg_":"40_power_precision.md",
 "md2_":"70_medicine_biology.md","tr2_":"92_vehicles_flight.md","mt2_":"10_metallurgy.md",
 "tx2_":"90_textiles.md","ag2_":"75_agriculture_food.md","in2_":"30_glass_optics.md",
 "cv2_":"85_transport_civil.md","en2_":"93_energy.md","if2_":"80_information_printing.md",
 "sc2_":"60_mathematics_method.md",
}
# com_ splits: calculation and logic go to module 94, everything that moves a
# signal down a wire or through the air goes to module 50.
COMPUTING_WORDS = ("calc","comput","boolean","binary","logic","punch","hollerith",
                   "crypt","informatio","flip_flop","register","accumulator","memory",
                   "core","drum","tape","compiler","stored_program","error_","slide_rule",
                   "napier","difference_engine","analytical_engine","arithmometer",
                   "comptometer","ring_counter","integrated_circuit","photolith")
HEAT_BY_TIER = {0:"cap_heat_0700",1:"cap_heat_1100",2:"cap_heat_1300",3:"cap_heat_1300",
                4:"cap_heat_1600",5:"cap_heat_1600"}
TOL_BY_TIER  = {0:"cap_tol_1mm",1:"cap_tol_1mm",2:"cap_tol_100um",3:"cap_tol_10um",
                4:"cap_tol_10um",5:"cap_tol_1um"}
VAC_BY_TIER  = {3:"cap_vac_1torr",4:"cap_vac_1e3",5:"cap_vac_1e6"}
PUR_BY_TIER  = {3:"cap_pure_2N",4:"cap_pure_4N",5:"cap_pure_6N"}
PWR_BY_TIER  = {3:"cap_power_water",4:"cap_power_electric",5:"cap_power_grid"}

SOCIAL_DEFAULT = {
 # category substring -> (gov, sus) applied only where BOTH are still zero
 "military":(3,6), "weapon":(3,6), "explosive":(3,10), "chem":(0,6), "medicine":(2,4),
 "agricult":(3,0), "food":(2,0), "transport":(2,1), "rail":(3,1), "ship":(3,1),
 "aviation":(3,10), "flight":(3,10), "electr":(1,8), "power":(2,3), "metal":(2,2),
 "textile":(-1,1), "household":(0,1), "print":(-1,2), "media":(-1,3), "optic":(1,3),
 "instrument":(1,3), "civil":(2,0), "mining":(2,1), "precision":(1,1), "comput":(0,4),
 "communic":(3,3), "glass":(1,2),
}

def cmd_repair(a):
    """Fix what the audit can fix mechanically, and MARK every inference.

    A tree whose capability prerequisites were inferred by a script is better
    than one where they are missing, but only if it says so. Every edge added
    here is recorded in the node so a reader can discount it.
    """
    tree = json.load(open(TREE))
    nodes = {node["id"]: node for node in tree["nodes"]}
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    wages = {trade: value["rate"] for trade, value in prices["wage_rates_denarii_per_hour"].items() if not trade.startswith("_")}
    goods = {material: value["p"] for material, value in prices["purchase_prices_denarii"].items() if not material.startswith("_")}
    for node in nodes.values():
        node["_total_cost"] = (sum(wages.get(trade,0)*hours for trade,hours in node["lab"].items())
                            + sum(goods.get(material,0)*quantity for material,quantity in node["mat"].items()) + node["cap"])
    by_category_cost = collections.defaultdict(list)
    for node in nodes.values():
        by_category_cost[node["cat"]].append(node["_total_cost"])
    stats = {"cost": {cat: statistics.median(value)
                      for cat, value in by_category_cost.items()}}

    counts = collections.Counter()
    for ident, node in list(nodes.items()):
        if node["cat"] in ABSTRACT_CATS:
            continue
        score, defects = judge_node(node, nodes, stats)
        codes = {code for code, _ in defects}
        added = []
        def add(cap_id):
            # NEVER create a cycle. cap_heat_1100 depends on refractory_fireclay, so
            # giving refractory_fireclay a furnace rung (its note is full of furnace
            # words) makes the graph eat itself. An earlier version did exactly that.
            if not cap_id or cap_id in nodes and cap_id in node["pre"]:
                return
            if cap_id not in nodes:
                return
            if node["id"] in closure(nodes, cap_id):
                counts["cycle-forming edges refused"] += 1
                return
            node["pre"].append(cap_id); added.append(cap_id)
        # Capability gaps remain visible for human review. A prose keyword
        # heuristic cannot safely infer engineering prerequisites.
        if codes & {"CAP-NONE", "CAP-HEAT", "CAP-TOL", "CAP-VAC", "CAP-PURITY", "CAP-POWER"}:
            counts["capability gaps LEFT VISIBLE (not guessed at)"] += 1
        if added:
            counts["capability edges inferred"] += len(added)
            node["note"] = node["note"].rstrip() + (" [AUDIT: capability prerequisite(s) %s were "
                "inferred by sim/treetool.py repair, not stated by the author. Treat "
                "them as a floor, not a specification.]" % ", ".join(added))
        # documentation level
        if not node.get("kb"):
            if ident.startswith("com_"):
                doc_module = ("94_computing.md" if any(word in ident for word in COMPUTING_WORDS)
                       else "50_electricity.md")
            else:
                doc_module = next((value for pre, value in PREFIX_MODULE.items() if ident.startswith(pre)), None)
            if doc_module:
                node["kb"] = doc_module; node["kb_level"] = "module"; counts["module-level doc links"] += 1
            else:
                node["kb_level"] = "none"; counts["still undocumented"] += 1
        else:
            node["kb_level"] = "recipe" if "#" in node["kb"] else "module"
        # social model
        if "SOCIAL-FLAT" in codes:
            haystack = (node["cat"] + " " + ident).lower()
            for category_marker, (gov_default, sus_default) in SOCIAL_DEFAULT.items():
                if category_marker in haystack:
                    node["gov"], node["sus"] = gov_default, sus_default
                    counts["social defaults applied"] += 1
                    node["note"] = node["note"].rstrip() + (" [AUDIT: State interest and suspicion "
                        "were unset and have been defaulted from the category.]")
                    break
        if "NO-FLOOR" in codes:
            node["yrs"] = max(node["yrs"], 2.0); counts["calendar floors raised"] += 1
    tree["nodes"] = [nodes[node_id] for node_id in sorted(nodes)]
    _write_json(tree, TREE, a)
    print("REPAIR PASS")
    for ident, value in counts.most_common():
        print("   %-32s %d" % (ident, value))
    return 0


def cmd_apply_caps(a):
    """Apply reviewer-assigned capability rungs from data/caps_fix_*.json.

    Unlike the keyword heuristic this replaces, every edge here was chosen by a
    reviewer looking at one node at a time with the failure modes of the previous
    attempt written into their brief. Each edge is still validated: it must name a
    real node, it must not already be present, and it must not create a cycle.
    """
    import glob
    tree = json.load(open(TREE))
    nodes = {node["id"]: node for node in tree["nodes"]}
    applied = refused = empty = unknown = 0
    reasons = {}
    for path in sorted(glob.glob(os.path.join(DATA, "review", "caps_fix_*.json"))):
        try:
            fixes = json.load(open(path))
        except Exception as e:
            print("unparseable: %s (%s)" % (os.path.basename(path), e))
            continue
        for node_id, fix in fixes.items():
            if node_id not in nodes:
                unknown += 1
                continue
            add = fix.get("add") or []
            if not add:
                empty += 1
                continue
            node = nodes[node_id]
            got = []
            for cap_id in add:
                if cap_id not in nodes:
                    refused += 1
                    continue
                if cap_id in node["pre"]:
                    continue
                if node_id in closure(nodes, cap_id):
                    refused += 1          # would make the graph eat itself
                    continue
                node["pre"].append(cap_id)
                got.append(cap_id)
                applied += 1
            if got:
                reasons[node_id] = (got, fix.get("reason", ""))
                node["note"] = node["note"].rstrip() + (
                    " [REVIEWED: prerequisite(s) %s added by a reviewer working node by node. "
                    "Reason: %s]" % (", ".join(got), fix.get("reason", "not given")))
    tree["nodes"] = [nodes[node_id] for node_id in sorted(nodes)]
    _write_json(tree, TREE, a)
    print("APPLY REVIEWER-ASSIGNED PREREQUISITES")
    print("   edges applied                    %d" % applied)
    print("   nodes judged to need none        %d" % empty)
    print("   edges refused (unknown or cycle) %d" % refused)
    print("   unknown node ids                 %d" % unknown)
    print("\nsample of what was added:")
    for node_id, (got, why) in list(reasons.items())[:12]:
        print("   %-34s + %-38s %s" % (node_id[:34], ", ".join(got)[:38], why[:70]))
    return 0


# WRITING IS A CHOICE, AND IT WAS NOT BEING OFFERED. Every one of this tool's
# four subcommands rewrote a committed data file - tech_tree.json (2.8 MB) or
# judgement.json (244 KB) - unconditionally, at the end of its run, with no way
# to ask any of them merely to LOOK. So `judge`, which reads as a report
# command and prints a report, silently replaced 244 KB of committed game data
# as a side effect of being run; an agent doing nothing but timing it wiped the
# file and only noticed because git said so. A tool whose read-only-sounding
# verb mutates the repository is a trap, and it caught the first person to
# walk past it.
#
# --dry-run says what would be written and writes nothing. The default is
# unchanged - these commands still write, because that is what they are for
# and existing callers depend on it - so this only adds a way to be careful.
def _write_json(obj, path, a, indent=1):
    """json.dump, unless --dry-run was asked for."""
    if getattr(a, "dry_run", False):
        print("would write %s (--dry-run: not written)" % os.path.basename(path))
        return
    json.dump(obj, open(path, "w"), indent=indent)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    subparsers.add_parser("merge")
    subparsers.add_parser("apply-caps")
    subparser = subparsers.add_parser("repair")
    subparser.add_argument("--infer-caps", action="store_true",
                   help="guess missing capability rungs from keywords. OFF BY DEFAULT: an "
                        "independent review found a 100 percent error rate on the edges this "
                        "produced. Every edge it adds must be reviewed by hand.")
    subparser = subparsers.add_parser("judge")
    subparser.add_argument("--full", action="store_true")
    subparser.add_argument("--id")
    subparser.add_argument("--grade")
    # ON EVERY SUBCOMMAND, not only the ones that look dangerous: all four
    # write a committed data file, and which ones those are is exactly the
    # thing a person running this for the first time does not know.
    for command_parser in subparsers.choices.values():
        command_parser.add_argument("--dry-run", action="store_true",
                         help="say what would be written, write nothing")
    args = parser.parse_args()
    return {"merge": cmd_merge, "judge": cmd_judge, "repair": cmd_repair,
            "apply-caps": cmd_apply_caps}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
