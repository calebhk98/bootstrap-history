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

    python3 rome/sim/treetool.py merge          # branches -> tech_tree.json
    python3 rome/sim/treetool.py judge          # score every node, summary
    python3 rome/sim/treetool.py judge --full   # every defect, node by node
    python3 rome/sim/treetool.py judge --id X   # one node's report card
    python3 rome/sim/treetool.py judge --grade D  # only nodes at or below D
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
    p = json.load(open(os.path.join(DATA, "prices.json")))
    return set(k for k in p["wage_rates_denarii_per_hour"] if not k.startswith("_"))

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
        m = re.findall(r"-?\d+(?:\.\d+)?", v)
        if m: return float(m[0])
    return float(d)


def normalise_v2(n):
    for k, v in DEFAULTS.items():
        n.setdefault(k, json.loads(json.dumps(v)))
    for k, d in (("ph",60),("cap",200),("up",40),("risk",0.15),("rev",0),
                 ("sch",0),("art",1)):
        n[k] = _num(n.get(k), d)
    n["risk"] = min(0.95, max(0.0, n["risk"]))
    for fld in ("lab","mat"):
        if not isinstance(n.get(fld), dict): n[fld] = {}
        else: n[fld] = {k: _num(v, 0) for k, v in n[fld].items()}
    if not isinstance(n.get("pre"), list): n["pre"] = []
    if not isinstance(n.get("traits"), list): n["traits"] = []
    """Accept either schema and leave the node in v2 shape with v1 fields
    backfilled, so the simulator and the audit keep working during the change."""
    if "build_yrs" not in n and "yrs" in n:
        y = float(n.get("yrs", 0) or 0)
        if y >= 5:
            n["build_yrs"], n["adopt_yrs"] = min(3.0, y / 3.0), y
        else:
            n["build_yrs"], n["adopt_yrs"] = y, 0.0
    n.setdefault("build_yrs", 0.0); n.setdefault("adopt_yrs", 0.0)
    n["yrs"] = max(float(n["build_yrs"]), float(n["adopt_yrs"]))
    n.setdefault("req_any", []); n.setdefault("traits", [])
    n.setdefault("dev_years", None); n.setdefault("dev_people", None)
    # v1 scalars are derived from traits so old code paths still run
    n.setdefault("gov", 0); n.setdefault("sus", 0)
    return n

# ---------------------------------------------------------------- MERGE
def load_aliases():
    f = os.path.join(BR, "ALIASES.json")
    if not os.path.exists(f):
        return {}, set()
    a = json.load(open(f))
    return a.get("alias", {}), set(a.get("drop", []))


def load_prices():
    p = json.load(open(os.path.join(DATA, "prices.json")))
    return set(k for k in p["purchase_prices_denarii"] if not k.startswith("_"))


def cmd_merge(a):
    goods = load_prices()
    TRADES = load_trades()
    alias, dropset = load_aliases()
    base = json.load(open(TREE))
    # Ids retired by deduplication. Branch files still contain both spellings
    # of a technology that two authors invented independently, so without this
    # the next merge silently resurrects every duplicate.
    retired = base.get("meta", {}).get("merged_duplicate_ids", {})
    nodes = {n["id"]: normalise_v2(n) for n in base["nodes"]}
    for n in nodes.values():
        n.setdefault("_src", "core")
    errs, warns, added = [], [], 0

    for fn in sorted(os.listdir(BR)):
        if not fn.endswith(".json") or fn == "ALIASES.json":
            continue
        try:
            batch = json.load(open(os.path.join(BR, fn)))
        except Exception as e:
            errs.append("%s: unparseable JSON: %s" % (fn, e))
            continue
        if not isinstance(batch, list):
            errs.append("%s: top level is not a list" % fn)
            continue

        # Branch authors routinely refer to their OWN nodes without the file's
        # id prefix: a file of ag2_* nodes asks for "coulter" when it means
        # "ag2_coulter". Left alone the prereq resolver below silently drops
        # those edges, which makes the technology look cheaper and earlier than
        # it is. Repair them here, but only where the fix is unambiguous.
        own = {n["id"] for n in batch if isinstance(n, dict) and "id" in n}
        prefixes = set()
        for i in own:
            if "_" in i:
                prefixes.add(i.split("_", 1)[0] + "_")
        for n in batch:
            if not isinstance(n, dict):
                continue
            fixed = []
            for p in n.get("pre", []):
                if p in own or p in nodes:
                    fixed.append(p)
                    continue
                cands = {pf + p for pf in prefixes if pf + p in own}
                if len(cands) == 1:
                    q = cands.pop()
                    fixed.append(q)
                    warns.append("%s: %s self-ref '%s' -> '%s'" % (fn, n.get("id", "?"), p, q))
                else:
                    fixed.append(p)
            if "pre" in n:
                n["pre"] = fixed

        for n in batch:
            missing = [k for k in REQUIRED if k not in n]
            if missing:
                errs.append("%s: %s missing fields %s" % (fn, n.get("id", "?"), missing))
                continue
            if n["id"] in retired:
                warns.append("%s: %s was merged into %s, skipping"
                             % (fn, n["id"], retired[n["id"]]))
                continue
            if n["id"] in nodes:
                warns.append("%s: duplicate id %s, keeping the first" % (fn, n["id"]))
                continue
            # Tier 9 meant UNOBTAINABLE and that concept was abolished: nothing
            # is unobtainable, only elsewhere. A new branch reintroduced it on
            normalise_v2(n)
            # resolve trade aliases rather than silently dropping the labour,
            # which would make the technology look cheaper than it is
            lab = {}
            for t, h in n["lab"].items():
                t2 = alias.get(t, t)
                if t2 in TRADES:
                    lab[t2] = lab.get(t2, 0) + h
                else:
                    warns.append("%s: %s unknown trade '%s', dropped" % (fn, n["id"], t))
            n["lab"] = lab
            mm = {}
            for m, q in n["mat"].items():
                m2 = alias.get(m, m)
                if m2 not in goods:
                    # generic fallbacks for the shapes authors actually write:
                    # "mat_beeswax" -> "beeswax_kg", "plaster" -> "plaster_kg"
                    for cand in (m2[4:] + "_kg" if m2.startswith("mat_") else None,
                                 m2 + "_kg", m2.replace("mat_", "")):
                        if cand and cand in goods:
                            m2 = cand
                            break
                if m2 in dropset or m in dropset:
                    warns.append("%s: %s '%s' is a technology not a material, dropped" % (fn, n["id"], m))
                    continue
                if m2 in goods:
                    mm[m2] = mm.get(m2, 0) + q
                else:
                    warns.append("%s: %s UNPRICED material '%s', dropped" % (fn, n["id"], m))
            n["mat"] = mm
            # Branch authors keep writing the RECIPE PROSE into the kb link
            # field. Left alone it reports as a broken link to a file whose
            # name is a sentence. Move it to note where note is empty and
            # clear the field, so it reports as an honest documentation gap.
            kb = str(n.get("kb", "")).strip()
            if kb and not re.match(r"^\d\d_[A-Za-z0-9_]+\.md(#|$)", kb):
                if not str(n.get("note", "")).strip():
                    n["note"] = kb
                kb = ""
            n["kb"] = kb
            n["_src"] = fn
            nodes[n["id"]] = n
            added += 1

    # resolve prerequisites
    dangling = collections.Counter()
    for n in nodes.values():
        n["pre"] = [retired.get(p, p) for p in n["pre"]]
        for gp in n.get("req_any", []):
            gp["options"] = {retired.get(o, o): q for o, q in gp.get("options", {}).items()}
        keep = []
        for p in n["pre"]:
            if p in nodes:
                keep.append(p)
            else:
                dangling[p] += 1
                warns.append("%s: dropped unresolvable prereq '%s'" % (n["id"], p))
        n["pre"] = keep

    # break any cycles by dropping the back edge, reporting each one
    order, state = [], {}
    def dfs(i, stack):
        if state.get(i) == 2:
            return
        if state.get(i) == 1:
            back = stack[-1]
            nodes[back]["pre"] = [p for p in nodes[back]["pre"] if p != i]
            errs.append("CYCLE broken: removed %s -> %s" % (back, i))
            return
        state[i] = 1
        for p in list(nodes[i]["pre"]):
            dfs(p, stack + [i])
        state[i] = 2
        order.append(i)
    for i in list(nodes):
        dfs(i, [])

    base["nodes"] = [nodes[i] for i in sorted(nodes)]
    base["meta"]["goal_node"] = "point_contact_transistor"
    _write_json(base, TREE, a)

    print("merged  : %d nodes (%d added from branches)" % (len(nodes), added))
    print("errors  : %d" % len(errs))
    for e in errs[:40]:
        print("   " + e)
    print("warnings: %d" % len(warns))
    for w in warns[:25]:
        print("   " + w)
    if len(warns) > 25:
        print("   ... %d more" % (len(warns) - 25))
    if dangling:
        print("\nmost-wanted unresolved prereq ids (candidates for new nodes):")
        for k, v in dangling.most_common(20):
            print("   %-40s wanted by %d nodes" % (k, v))
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
        c = stack.pop()
        if c in seen:
            continue
        seen.add(c)
        stack.extend(nodes[c]["pre"])
    return seen


def judge_node(n, nodes, stats):
    """Score one technology using its declared graph and category, not a rank."""
    d = []
    if n["cat"] in ABSTRACT_CATS:
        if len(n["note"]) < 60:
            d.append(("NOTE-THIN", "note is %d characters" % len(n["note"])))
        if n["conf"] not in ("A", "B", "C"):
            d.append(("NO-CONF", "confidence not stated"))
        return max(0, 100 - len(d) * 12), d

    cl = closure(nodes, n["id"])
    caps = {c for c in cl if c.startswith(CAP_PREFIX)}
    text = (n["name"] + " " + n["note"]).lower()
    unob = [c for c in cl if nodes[c]["cat"] == "unobtainable"]
    physical = bool(n.get("mat")) or n.get("cap", 0) >= 200
    if not caps and physical and len(cl) >= 3 and n["cat"] not in (
            "social", "institution", "mathematics", "physics", "foundation",
            "information", "capability"):
        d.append(("CAP-NONE", "physical work with no capability rung in its chain "
                              "(furnace, tolerance, vacuum, purity, or power)"))

    def want(words, prefix, label):
        if any(w in text for w in words) and not any(c.startswith(prefix) for c in caps):
            d.append(("CAP-" + label, "reads as needing a %s rung but none appears "
                                      "in its prerequisite chain" % label.lower()))
    want(HEAT_WORDS, "cap_heat_", "HEAT")
    want(TOL_WORDS, "cap_tol_", "TOL")
    want(VAC_WORDS, "cap_vac_", "VAC")
    want(PUR_WORDS, "cap_pure_", "PURITY")
    if any(w in text for w in ELEC_WORDS) and not any(c.startswith("cap_power_") for c in caps):
        d.append(("CAP-POWER", "electrical work with no power rung in its chain"))

    if len(n["pre"]) < 2 and 10 <= len(cl) < 25:
        d.append(("SHALLOW", "%d direct prerequisite(s) and an ancestry only %d nodes deep"
                             % (len(n["pre"]), len(cl))))
    if unob and n["cat"] != "unobtainable":
        d.append(("BLOCKED", "depends on %s, which is marked UNOBTAINABLE"
                             % ", ".join(sorted(unob)[:3])))

    category = n["cat"]
    med_cost = stats["cost"].get(category, 1)
    cost = n["_total_cost"]
    if med_cost > 0 and cost > med_cost * 25:
        d.append(("COST-HIGH", "costs %s den, about %.0fx the median for category %s"
                               % (f"{cost:,.0f}", cost / med_cost, category)))
    if n["ph"] > 2000:
        d.append(("HOURS-HIGH", "%s founder-hours, which is %.1f%% of a working life"
                                % (f"{n['ph']:,}", 100.0 * n["ph"] / 72000)))
    if len(cl) >= 3 and n["ph"] == 0 and n["cat"] not in ("capability", "material"):
        d.append(("HOURS-ZERO", "non-foundational work costs the founder no hours"))
    if n.get("adopt_yrs", 0) >= 5 and n["yrs"] < 1:
        d.append(("NO-FLOOR", "long adoption has a calendar floor under a year"))
    if len(n["note"]) < 60:
        d.append(("NOTE-THIN", "note is %d characters" % len(n["note"])))
    if not n.get("kb") and n["cat"] not in ("capability", "material", "unobtainable"):
        d.append(("NO-RECIPE", "no knowledge-base link"))
    if n["conf"] not in ("A", "B", "C"):
        d.append(("NO-CONF", "confidence not stated"))
    if len(cl) >= 3 and not n.get("traits") and n["sus"] == 0 and n["gov"] == 0 \
            and n["cat"] not in ("capability", "material", "unobtainable", "mathematics", "physics"):
        d.append(("SOCIAL-FLAT", "no traits and no scalar gov/sus"))

    weights = {"NO-RECIPE": 1, "CAP-NONE": 3, "CAP-HEAT": 2, "CAP-TOL": 2,
               "CAP-VAC": 2, "CAP-PURITY": 2, "CAP-POWER": 2, "SHALLOW": 3,
               "BLOCKED": 3, "COST-HIGH": 1, "HOURS-HIGH": 1, "HOURS-ZERO": 1,
               "NO-FLOOR": 1, "NOTE-THIN": 2, "NO-CONF": 1, "SOCIAL-FLAT": 1}
    penalty = sum(weights.get(code, 1) for code, _ in d)
    return max(0, int(round(100 - penalty * 6))), d

def grade(s):
    return "A" if s >= 90 else "B" if s >= 78 else "C" if s >= 64 else "D" if s >= 50 else "F"


def cmd_judge(a):
    tree = json.load(open(TREE))
    nodes = {n["id"]: n for n in tree["nodes"]}
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    wages = {k: v["rate"] for k, v in prices["wage_rates_denarii_per_hour"].items() if not k.startswith("_")}
    goods = {k: v["p"] for k, v in prices["purchase_prices_denarii"].items() if not k.startswith("_")}
    for n in nodes.values():
        n["_total_cost"] = (sum(wages.get(t, 0) * h for t, h in n["lab"].items())
                            + sum(goods.get(m, 0) * q for m, q in n["mat"].items()) + n["cap"])

    by_category_cost = collections.defaultdict(list)
    for n in nodes.values():
        by_category_cost[n["cat"]].append(n["_total_cost"])
    stats = {"cost": {cat: statistics.median(v)
                      for cat, v in by_category_cost.items()}}

    results = {}
    for k, n in nodes.items():
        results[k] = judge_node(n, nodes, stats)

    if a.id:
        if a.id not in nodes:
            near = [x for x in nodes if a.id.lower() in x.lower()]
            raise SystemExit("unknown node. near matches: %s" % (", ".join(near[:10]) or "none"))
        n, (s, d) = nodes[a.id], results[a.id]
        print("%s  [%s]" % (n["name"], n["id"]))
        print("=" * 78)
        print("grade %s (%d/100)   %s   confidence %s"
              % (grade(s), s, n["cat"], n["conf"]))
        print("direct prerequisites : %d   full ancestry : %d nodes"
              % (len(n["pre"]), len(closure(nodes, a.id)) - 1))
        print("cost %s den   founder-hours %s   calendar floor %.1f yr   risk %.0f%%"
              % (f"{n['_total_cost']:,.0f}", f"{n['ph']:,}", n["yrs"], 100 * n["risk"]))
        caps = sorted(c for c in closure(nodes, a.id) if c.startswith("cap_"))
        print("capability rungs in its chain: %s" % (", ".join(caps) if caps else "NONE"))
        print("\n%s\n" % n["note"])
        if d:
            print("DEFECTS")
            for c, msg in d:
                print("  [%s] %s" % (c, msg))
        else:
            print("No defects found by the automated checks.")
        return 0

    dist = collections.Counter(grade(s) for s, _ in results.values())
    defects = collections.Counter()
    for s, d in results.values():
        for c, _ in d:
            defects[c] += 1

    print("PER-TECHNOLOGY AUDIT: every node judged on its own, not on the end date")
    print("=" * 78)
    print("nodes judged : %d" % len(nodes))
    print("mean score   : %.1f/100" % statistics.mean(s for s, _ in results.values()))
    print("grades       : " + "  ".join("%s %d (%.0f%%)" % (g, dist[g], 100.0 * dist[g] / len(nodes))
                                        for g in "ABCDF"))
    print("\nDEFECTS BY FREQUENCY")
    for c, v in defects.most_common():
        print("   %-12s %4d  (%.0f%% of nodes)" % (c, v, 100.0 * v / len(nodes)))
    print("\nWORST NODES")
    worst = sorted(results.items(), key=lambda x: x[1][0])[:20]
    for k, (s, d) in worst:
        print("   %-34s %3d %s  %s" % (k[:34], s, grade(s), ", ".join(c for c, _ in d[:4])))
    if a.grade:
        floor = "FDCBA".index(a.grade.upper())
        print("\nALL NODES AT GRADE %s OR WORSE" % a.grade.upper())
        for k, (s, d) in sorted(results.items(), key=lambda x: x[1][0]):
            if "FDCBA".index(grade(s)) <= floor:
                print("   %-34s %3d %s  %s" % (k[:34], s, grade(s), ", ".join(c for c, _ in d)))
    if a.full:
        print("\nFULL REPORT")
        for k, (s, d) in sorted(results.items(), key=lambda x: x[1][0]):
            if d:
                print("\n%s  %d %s" % (k, s, grade(s)))
                for c, m in d:
                    print("    [%s] %s" % (c, m))
    _write_json({k: {"score": s, "grade": grade(s), "defects": [c for c, _ in d]}
                 for k, (s, d) in results.items()},
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
    nodes = {n["id"]: n for n in tree["nodes"]}
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    wages = {k: v["rate"] for k, v in prices["wage_rates_denarii_per_hour"].items() if not k.startswith("_")}
    goods = {k: v["p"] for k, v in prices["purchase_prices_denarii"].items() if not k.startswith("_")}
    for n in nodes.values():
        n["_total_cost"] = (sum(wages.get(t,0)*h for t,h in n["lab"].items())
                            + sum(goods.get(m,0)*q for m,q in n["mat"].items()) + n["cap"])
    by_category_cost = collections.defaultdict(list)
    for n in nodes.values():
        by_category_cost[n["cat"]].append(n["_total_cost"])
    stats = {"cost": {cat: statistics.median(v)
                      for cat, v in by_category_cost.items()}}

    counts = collections.Counter()
    for k, n in list(nodes.items()):
        if n["cat"] in ABSTRACT_CATS:
            continue
        score, defects = judge_node(n, nodes, stats)
        codes = {c for c, _ in defects}
        added = []
        def add(cap_id):
            # NEVER create a cycle. cap_heat_1100 depends on refractory_fireclay, so
            # giving refractory_fireclay a furnace rung (its note is full of furnace
            # words) makes the graph eat itself. An earlier version did exactly that.
            if not cap_id or cap_id in nodes and cap_id in n["pre"]:
                return
            if cap_id not in nodes:
                return
            if n["id"] in closure(nodes, cap_id):
                counts["cycle-forming edges refused"] += 1
                return
            n["pre"].append(cap_id); added.append(cap_id)
        # Capability gaps remain visible for human review. A prose keyword
        # heuristic cannot safely infer engineering prerequisites.
        if codes & {"CAP-NONE", "CAP-HEAT", "CAP-TOL", "CAP-VAC", "CAP-PURITY", "CAP-POWER"}:
            counts["capability gaps LEFT VISIBLE (not guessed at)"] += 1
        if added:
            counts["capability edges inferred"] += len(added)
            n["note"] = n["note"].rstrip() + (" [AUDIT: capability prerequisite(s) %s were "
                "inferred by rome/sim/treetool.py repair, not stated by the author. Treat "
                "them as a floor, not a specification.]" % ", ".join(added))
        # documentation level
        if not n.get("kb"):
            if k.startswith("com_"):
                mod = ("94_computing.md" if any(w in k for w in COMPUTING_WORDS)
                       else "50_electricity.md")
            else:
                mod = next((v for pre, v in PREFIX_MODULE.items() if k.startswith(pre)), None)
            if mod:
                n["kb"] = mod; n["kb_level"] = "module"; counts["module-level doc links"] += 1
            else:
                n["kb_level"] = "none"; counts["still undocumented"] += 1
        else:
            n["kb_level"] = "recipe" if "#" in n["kb"] else "module"
        # social model
        if "SOCIAL-FLAT" in codes:
            hay = (n["cat"] + " " + k).lower()
            for key, (g, su) in SOCIAL_DEFAULT.items():
                if key in hay:
                    n["gov"], n["sus"] = g, su
                    counts["social defaults applied"] += 1
                    n["note"] = n["note"].rstrip() + (" [AUDIT: State interest and suspicion "
                        "were unset and have been defaulted from the category.]")
                    break
        if "NO-FLOOR" in codes:
            n["yrs"] = max(n["yrs"], 2.0); counts["calendar floors raised"] += 1
    tree["nodes"] = [nodes[i] for i in sorted(nodes)]
    _write_json(tree, TREE, a)
    print("REPAIR PASS")
    for k, v in counts.most_common():
        print("   %-32s %d" % (k, v))
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
    nodes = {n["id"]: n for n in tree["nodes"]}
    applied = refused = empty = unknown = 0
    reasons = {}
    for f in sorted(glob.glob(os.path.join(DATA, "review", "caps_fix_*.json"))):
        try:
            fixes = json.load(open(f))
        except Exception as e:
            print("unparseable: %s (%s)" % (os.path.basename(f), e))
            continue
        for nid, fix in fixes.items():
            if nid not in nodes:
                unknown += 1
                continue
            add = fix.get("add") or []
            if not add:
                empty += 1
                continue
            n = nodes[nid]
            got = []
            for cap in add:
                if cap not in nodes:
                    refused += 1
                    continue
                if cap in n["pre"]:
                    continue
                if nid in closure(nodes, cap):
                    refused += 1          # would make the graph eat itself
                    continue
                n["pre"].append(cap)
                got.append(cap)
                applied += 1
            if got:
                reasons[nid] = (got, fix.get("reason", ""))
                n["note"] = n["note"].rstrip() + (
                    " [REVIEWED: prerequisite(s) %s added by a reviewer working node by node. "
                    "Reason: %s]" % (", ".join(got), fix.get("reason", "not given")))
    tree["nodes"] = [nodes[i] for i in sorted(nodes)]
    _write_json(tree, TREE, a)
    print("APPLY REVIEWER-ASSIGNED PREREQUISITES")
    print("   edges applied                    %d" % applied)
    print("   nodes judged to need none        %d" % empty)
    print("   edges refused (unknown or cycle) %d" % refused)
    print("   unknown node ids                 %d" % unknown)
    print("\nsample of what was added:")
    for nid, (got, why) in list(reasons.items())[:12]:
        print("   %-34s + %-38s %s" % (nid[:34], ", ".join(got)[:38], why[:70]))
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
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("merge")
    sub.add_parser("apply-caps")
    q = sub.add_parser("repair")
    q.add_argument("--infer-caps", action="store_true",
                   help="guess missing capability rungs from keywords. OFF BY DEFAULT: an "
                        "independent review found a 100 percent error rate on the edges this "
                        "produced. Every edge it adds must be reviewed by hand.")
    q = sub.add_parser("judge")
    q.add_argument("--full", action="store_true")
    q.add_argument("--id")
    q.add_argument("--grade")
    # ON EVERY SUBCOMMAND, not only the ones that look dangerous: all four
    # write a committed data file, and which ones those are is exactly the
    # thing a person running this for the first time does not know.
    for _sp in sub.choices.values():
        _sp.add_argument("--dry-run", action="store_true",
                         help="say what would be written, write nothing")
    a = p.parse_args()
    return {"merge": cmd_merge, "judge": cmd_judge, "repair": cmd_repair,
            "apply-caps": cmd_apply_caps}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
