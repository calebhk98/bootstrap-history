#!/usr/bin/env python3
"""Migrate the tree to schema v2.

Four changes, each answering a specific criticism of v1:

1. `gov` and `sus` become `traits`. How a society reacts is a property of the
   SOCIETY, not the technology, so the technology carries tags and the
   civilization file carries weights. See data/civilizations/_SCHEMA.md.
2. `yrs` splits into `build_yrs` (physically constructing the thing) and
   `adopt_yrs` (the economy absorbing it). Research time is not a category,
   because the founder carries the blueprints.
3. Tier 9 UNOBTAINABLE is abolished. Nothing is unobtainable. Those nodes now
   depend on the expedition that reaches the place the material is.
4. `req_any` substitution groups, so that a steam engine can burn wood and be
   made of bronze, badly, instead of being impossible without coal and steel.
"""
import json, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.path.join(ROOT, "data", "tech_tree.json")

# --- 1. traits ---------------------------------------------------------------
CAT_TRAITS = {
 "military":["military"], "weapon":["military"], "explosive":["military"],
 "medicine":["medical"], "surg":["medical"], "health":["medical"], "pharma":["medical"],
 "agricult":["food"], "food":["food"], "crop":["food"], "livestock":["food"], "preserv":["food"],
 "transport":["infrastructure","commerce"], "rail":["infrastructure","commerce"],
 "ship":["infrastructure","commerce"], "naval":["military","infrastructure"],
 "navig":["infrastructure","commerce"], "aviat":["spectacle","military"], "flight":["spectacle","military"],
 "power":["infrastructure"], "energy":["infrastructure"], "electr":["inexplicable","infrastructure"],
 "chem":["inexplicable"], "acid":["inexplicable"], "metal":["infrastructure"], "mining":["infrastructure"],
 "machine":["labour_saving"], "precision":["labour_saving"], "tool":["labour_saving"],
 "textile":["labour_saving","commerce"], "cloth":["labour_saving","commerce"],
 "household":["luxury"], "domestic":["labour_saving","luxury"], "personal":["luxury"],
 "print":["information","status_threatening"], "media":["information","status_threatening"],
 "information":["information"], "signal":["information","military"], "communic":["information","military"],
 "comput":["information"], "optic":["spectacle"], "instrument":["spectacle"], "measure":[],
 "civil":["infrastructure"], "structur":["infrastructure"], "construct":["infrastructure"],
 "glass":["luxury"], "expedition":["commerce","military"], "finance":["commerce"],
 "commerce":["commerce"], "institution":["status_threatening"], "social":["status_threatening"],
 "capability":[], "material":[], "mathematics":["information"], "physics":["information"],
 "semicond":["inexplicable"], "luxury":["luxury"],
}
def derive_traits(n):
    t = set()
    hay = (n.get("cat","") + " " + n["id"]).lower()
    for k, v in CAT_TRAITS.items():
        if k in hay:
            t.update(v)
    # old scalars carry real information; use them, then discard them
    if n.get("gov", 0) >= 2: t.add("military") if "milit" in hay else t.add("infrastructure")
    if n.get("gov", 0) <= -1: t.add("status_threatening")
    s = n.get("sus", 0)
    if s >= 10: t.add("inexplicable")
    if 5 <= s < 10: t.add("spectacle")
    txt = (n["name"] + " " + n.get("note","")).lower()
    if any(w in txt for w in ("displac","replace.*labour","labour-saving","labour saving")): t.add("labour_saving")
    if any(w in txt for w in ("burial","omen","heaven","dissect","cadaver","corpse","temple")): t.add("religious_adjacent")
    if any(w in txt for w in ("firearm","musket","pistol","rifle","handgun","revolver")): t.add("weapon_democratising")
    return sorted(t)

def main():
    tree = json.load(open(TREE))
    # A ONE-TIME MIGRATION REFUSES TO RUN TWICE. This script's own SUBS dict
    # below is a SNAPSHOT of what substitution looked like at the moment v1
    # became v2, not a rule that stays true forever: point_contact_transistor
    # was in it then (single_crystal or silicon_path), and a later, separate
    # fix removed that requirement from the live tree outright - the 1947
    # device used polycrystalline germanium, with no pulled crystal and no
    # zone refining, and the node's own note says so. Nothing here updated
    # when that fix landed, because nothing expected this script to run
    # again. A player found exactly that gap from the outside - the node's
    # text promising polycrystalline germanium while something, somewhere,
    # still gated it on single_crystal/silicon_path - and traced it to this
    # literal. The live tree turned out to be clean; this file, left armed to
    # fire a second time, was the one place the contradiction could still
    # come back from. Refusing to re-run is cheaper and more durable than
    # trying to keep every literal below in step with every later hand-fix to
    # the tree it was migrating away from.
    if tree.get("meta", {}).get("schema_version") == 2:
        print("tech_tree.json is already schema v2 (migrated once already). "
              "This script is a ONE-TIME v1->v2 migration, not a rule to "
              "reapply: its SUBS/EXPED/REWRITE tables are a snapshot from "
              "the moment of migration, and later hand-fixes to the live "
              "tree (for example, removing point_contact_transistor's stale "
              "single_crystal/silicon_path substitution group once the node "
              "was corrected to need neither) would be silently reverted by "
              "running this again. Nothing to do.")
        return 0
    nodes = {n["id"]: n for n in tree["nodes"]}
    c = collections.Counter()

    for n in nodes.values():
        # 1. traits
        if "traits" not in n:
            n["traits"] = derive_traits(n); c["traits derived"] += 1
        # 2. time split
        if "build_yrs" not in n:
            y = float(n.get("yrs", 0))
            # a long "yrs" on a heavy node was always diffusion, not construction
            if y >= 5 and n["tier"] >= 3:
                n["build_yrs"], n["adopt_yrs"] = min(3.0, y / 3.0), y
            else:
                n["build_yrs"], n["adopt_yrs"] = y, 0.0
            c["time split"] += 1
        n.setdefault("req_any", [])
        n.setdefault("dev_years", None); n.setdefault("dev_people", None)

    # 3. abolish tier 9
    EXPED = {
      "mat_natural_rubber":"exp_coastal_africa", "mat_gutta_percha":"exp_trade_route_extend",
      "mat_quinine":"exp_americas_factory", "mat_chile_nitrate":"exp_americas_factory",
      "mat_newworld_crops":"exp_americas_factory", "mat_platinum_bulk":"exp_africa_circumnavigation",
      "mat_cryolite":"exp_pacific_arctic_or_synthetic", "med_cocaine_unobtainable":"exp_americas_factory",
      "fud_potato_tier9":"exp_americas_factory", "fud_maize_tier9":"exp_americas_factory",
      "fud_chocolate_tier9":"exp_americas_factory",
    }
    REWRITE = {
      "mat_natural_rubber":("Natural rubber","NOT UNOBTAINABLE. Hevea is Amazonian, but Landolphia and Funtumia vines in West and Central Africa yield real rubber and were the basis of a large industry in the 1890s. West Africa is COASTAL SAILING from the Pillars of Hercules and Hanno the Carthaginian did it around 500 BC. You need a voyage down a coast and the knowledge of which vine to tap, not an ocean crossing."),
      "mat_gutta_percha":("Gutta percha","NOT UNOBTAINABLE. Palaquium latex from Malaya, reached by extending east the India route Rome already sails annually. Indian and Malay traders already carry it partway."),
      "mat_quinine":("Quinine from cinchona","NOT UNOBTAINABLE, only Andean. Malaria is endemic around Rome, which makes this worth an ocean crossing by itself. Once you have it, TRANSPLANT it: the Dutch and British both moved cinchona out of Peru and broke the monopoly."),
      "mat_chile_nitrate":("Sodium nitrate","NOT UNOBTAINABLE, and also not needed. Bengal saltpetre is on a route Rome already sails and supplied the world's gunpowder for centuries, and nitre beds work anywhere."),
      "mat_newworld_crops":("New World crops","NOT UNOBTAINABLE. These are CROPS, not commodities: you need seed stock once and then you grow them forever. One successful voyage home with potato seed changes the caloric ceiling of European agriculture permanently."),
      "mat_platinum_bulk":("Platinum","NOT UNOBTAINABLE. Colombian and Ural placers. The Urals are reachable overland through Scythian and Sarmatian trade without crossing any ocean."),
      "mat_cryolite":("Cryolite, or a synthetic fluoride bath","NOT UNOBTAINABLE. Ivigtut in Greenland is the only workable natural deposit, but a synthetic fluoride bath made from your own hydrofluoric acid works, which is what industry moved to anyway."),
      "med_cocaine_unobtainable":("Cocaine from coca","NOT UNOBTAINABLE, only Andean. The first effective local anaesthetic."),
      "fud_potato_tier9":("The potato","NOT UNOBTAINABLE. Two to four times the calories per hectare of wheat on poor ground. One voyage, then you grow it forever."),
      "fud_maize_tier9":("Maize","NOT UNOBTAINABLE. One voyage for seed stock."),
      "fud_chocolate_tier9":("Cacao","NOT UNOBTAINABLE. One voyage for seed stock, then transplant."),
    }
    for k, exp in EXPED.items():
        if k not in nodes: continue
        n = nodes[k]
        n["tier"] = 4
        n["cat"] = "located_material"
        if exp in nodes and exp not in n["pre"]:
            n["pre"].append(exp)
        if k in REWRITE:
            nm, note = REWRITE[k]
            n["name"] = nm
            n["note"] = note + " See data/world/geography.json for where it is and what reaching it costs."
        n["risk"] = max(n.get("risk", 0.2), 0.25)
        n["ph"] = max(n.get("ph", 0), 60)
        c["unobtainable abolished"] += 1

    # 4. substitution groups on the nodes where substitution genuinely exists
    SUBS = {
      "steam_atmospheric": [
        {"group":"fuel","options":{"coal_coke":1.0,"charcoal_industrial":0.7,"mat_charcoal":0.7,"firewood_kg":0.45}},
        {"group":"pressure_vessel","options":{"mat_bulk_steel":1.0,"finery_puddling":0.75,"mat_wrought_iron":0.6,"mat_bronze":0.45,"mat_copper":0.35}}],
      "steam_watt": [
        {"group":"fuel","options":{"coal_coke":1.0,"mat_charcoal":0.7,"firewood_kg":0.45,"mat_petroleum_refined":0.95}},
        {"group":"pressure_vessel","options":{"mat_bulk_steel":1.0,"mat_wrought_iron":0.6,"mat_bronze":0.4}}],
      "steam_high_pressure": [
        {"group":"fuel","options":{"coal_coke":1.0,"mat_charcoal":0.6,"mat_petroleum_refined":1.0}},
        {"group":"pressure_vessel","options":{"mat_bulk_steel":1.0,"mat_wrought_iron":0.45}}],
      "blast_furnace": [
        {"group":"fuel","options":{"coal_coke":1.0,"charcoal_industrial":0.8,"mat_charcoal":0.8}},
        {"group":"blast","options":{"bellows_water_blown":1.0,"cap_power_steam":1.2,"cap_power_muscle":0.35}}],
      "cementation_steel": [{"group":"carburiser","options":{"mat_charcoal":1.0,"bone_kg":0.8,"coal_kg":0.6}}],
      "copper_refining": [{"group":"conductor_stock","options":{"cap_pure_4N":1.0,"copper_fire_refined":0.7}}],
      "dynamo": [{"group":"conductor","options":{"copper_refining":1.0,"copper_fire_refined":0.75,"mat_aluminium":0.6,"iron_bar_kg":0.3}},
                 {"group":"insulation","options":{"mat_shellac":1.0,"silk_kg":0.95,"mat_natural_rubber":1.0,"linen_kg":0.5,"mat_bitumen":0.45}}],
      "telegraph_electric": [{"group":"conductor","options":{"copper_refining":1.0,"copper_fire_refined":0.8,"iron_bar_kg":0.45}},
                             {"group":"insulation","options":{"mat_gutta_percha":1.0,"mat_shellac":0.7,"mat_bitumen":0.55,"glass_clear":0.8}}],
      "printing_press": [{"group":"substrate","options":{"rag_paper":1.0,"parchment_sheet":0.35,"papyrus_sheet":0.3}},
                         {"group":"type_metal","options":{"antimony_kg":1.0,"lead_kg":0.6,"mat_bronze":0.5}}],
      "glass_clear": [{"group":"flux","options":{"potash_soda":1.0,"natron_kg":0.95,"wood_ash_kg":0.7}}],
      "nitre_beds": [{"group":"nitrate_source","options":{"exp_trade_route_extend":1.4,"manure_kg":1.0}}],
      "railway": [{"group":"rail_metal","options":{"bessemer_openhearth":1.0,"finery_puddling":0.55,"mat_cast_iron":0.3}}],
      "vacuum_pumps": [{"group":"working_fluid","options":{"mercury_supply":1.0,"mat_olive_oil":0.5}}],
      "arc_light_lamp": [{"group":"conductor","options":{"copper_refining":1.0,"mat_aluminium":0.6}}],
      # point_contact_transistor USED TO BE HERE, gated on single_crystal or
      # silicon_path - wrong the day it was written, not only in hindsight:
      # Bardeen and Brattain's 1947 device ran on ordinary polycrystalline
      # germanium, with neither a pulled single crystal nor zone refining,
      # and the node's own note has always said so. A later fix removed the
      # group from the live tree (point_contact_transistor's req_any is now
      # []; see ge_reduction in `pre` instead, which is what the device
      # actually needed). Deleted here too, not left disarmed-but-present,
      # because the schema_version guard above is the thing that stops this
      # file from ever overwriting the tree again - this entry existing at
      # all, even unused, invites exactly the "just re-run it to be sure"
      # mistake that would revive the contradiction.
    }
    for k, groups in SUBS.items():
        if k in nodes:
            nodes[k]["req_any"] = groups
            c["substitution groups added"] += 1

    tree["meta"]["schema_version"] = 2
    tree["nodes"] = [nodes[i] for i in sorted(nodes)]
    json.dump(tree, open(TREE, "w"), indent=1)
    print("MIGRATION TO SCHEMA v2")
    for k, v in c.most_common():
        print("   %-32s %d" % (k, v))
    tr = collections.Counter(t for n in nodes.values() for t in n["traits"])
    print("\ntrait distribution:")
    for k, v in tr.most_common():
        print("   %-24s %d" % (k, v))
    return 0

if __name__ == "__main__":
    sys.exit(main())
