"""Declared numbers the resources module owns: mines, deposits, prospecting, woodland and nitre beds.

A price in labour hours is a hours constant; the module multiplies it by what one hour is worth (the view
`money_per_labour_hour`) where it is used."""
from sim.constants import declare

MINE_LEAD_YEARS = declare(
    "MINE_LEAD_YEARS", 3.0, kind="engineering_estimate",
    unit="years", source="Sinking a shaft, arranging drainage, "
         "building access roads and hiring a crew for a pre-modern "
         "working plausibly takes on this order of time; not tied to "
         "an attested figure for a specific Roman mine.",
    confidence="C",
    why="How long a new mining tranche takes to come into production "
        "after capital is committed - the delay that stopped a "
        "playtester from treating mine investment as instantaneous.")

GENERIC_MINE_DEPTH_CLASS = declare(
    "GENERIC_MINE_DEPTH_CLASS", "shallow_vein", kind="temporary_heuristic",
    unit="depth class of deposits.py", source=None, confidence="D",
    why="Depth of the workings assumed for a material with no named "
        "deposits; replace with per-material deposit data.")

GENERIC_MINE_HARDNESS_CLASS = declare(
    "GENERIC_MINE_HARDNESS_CLASS", "medium", kind="temporary_heuristic",
    unit="hardness class of deposits.py", source=None, confidence="D",
    why="Rock hardness assumed for a material with no named deposits; "
        "replace with per-material deposit data.")

MINE_CEILING_BASE_IMPERIAL = declare(
    "MINE_CEILING_BASE_IMPERIAL", 20000.0, kind="temporary_heuristic",
    retire="Complaint 660 follow-up: ceiling from tonnes an inspector can keep registered",
    unit="tonnes/year (base, before state reach and revenue scale)",
    source=None, confidence="D",
    why="Base standing-mine ceiling for an imperial patron before "
        "state reach, geology and mining technology are applied. "
        "No fiscal or organisational-capacity data backs this figure; "
        "it is a tuned starting point for the four patronage tiers "
        "this method distinguishes.")

MINE_CEILING_STATE_SCALE_IMPERIAL = declare(
    "MINE_CEILING_STATE_SCALE_IMPERIAL", 60000.0, kind="temporary_heuristic",
    retire="Complaint 660 follow-up: ceiling from tonnes an inspector can keep registered",
    unit="tonnes/year per unit of inspection reach (share of people whose claims its inspectors check)", source=None,
    confidence="D",
    why="How much further a more capable state extends the imperial-"
        "tier ceiling. Tuned, not derived from any state-capacity "
        "output relationship.")

MINE_CEILING_BASE_STRANGER = declare(
    "MINE_CEILING_BASE_STRANGER", 3000.0, kind="temporary_heuristic",
    retire="Complaint 660 follow-up: ceiling from tonnes an inspector can keep registered",
    unit="tonnes/year (base)", source=None, confidence="D",
    why="As MINE_CEILING_BASE_IMPERIAL, for a stranger with no "
        "citizenship or patron - still a real production ceiling, per "
        "this method's own docstring, so an unpatronised founder is "
        "never simply shut out of mining.")

MINE_CEILING_STATE_SCALE_STRANGER = declare(
    "MINE_CEILING_STATE_SCALE_STRANGER", 4000.0, kind="temporary_heuristic",
    retire="Complaint 660 follow-up: ceiling from tonnes an inspector can keep registered",
    unit="tonnes/year per unit of inspection reach", source=None,
    confidence="D",
    why="As MINE_CEILING_STATE_SCALE_IMPERIAL, for the stranger tier.")

REVENUE_SCALE_CAP_MULTIPLE = declare(
    "REVENUE_SCALE_CAP_MULTIPLE", 5.0, kind="temporary_heuristic",
    unit="multiple on the base ceiling (maximum)", source=None,
    confidence="D",
    why="How much a household's own revenue can multiply a standing "
        "ceiling (mine land or forest land) beyond its patronage-tier "
        "base, capped so a very rich household still cannot organise "
        "an unbounded enterprise from revenue alone. Reused identically "
        "for forest_land_ceiling() below. Tuned, not derived from any "
        "attested relationship between income and organisational "
        "capacity.")

REVENUE_SCALE_LABOUR_HOURS = declare(
    "REVENUE_SCALE_LABOUR_HOURS", 1210000.0, kind="temporary_heuristic",
    unit="labour hours/year of revenue for +100% ceiling", source=None,
    confidence="D",
    why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
        "How much annual revenue it takes to double a standing "
        "ceiling via REVENUE_SCALE_CAP_MULTIPLE, reused identically in "
        "forest_land_ceiling() below. Tuned, not derived from any "
        "attested income-to-capacity relationship.")

DEPLETION_HALF_LIFE_YRS = declare(
    "DEPLETION_HALF_LIFE_YRS", 120.0, kind="temporary_heuristic",
    unit="intensity-years for yield to fall from 1.0 toward the floor",
    source="Order-of-magnitude anchor: real long-worked Old World "
           "deposits (Rio Tinto, Laurion's near-surface ore) went from "
           "rich to markedly poorer and needed new technique over "
           "several human generations, not one and not a thousand.",
    confidence="C",
    why="How many intensity-years of mining at full land-ceiling "
        "pace it takes a deposit's yield to visibly decline - see the "
        "class comment above for why this is INTENSITY-years (working "
        "hard relative to what the ground supports) rather than "
        "calendar years. Deliberately round rather than fitted to any "
        "single citation, per that comment.")

DEPLETION_FLOOR = declare(
    "DEPLETION_FLOOR", 0.5, kind="temporary_heuristic",
    unit="fraction of day-one yield (minimum)", source=None,
    confidence="D",
    why="However worked-out a deposit gets, a working never falls "
        "below half its original yield - the easy half of a deposit "
        "running out does not mean the hard half is worthless. "
        "Deliberately never zero: see the class comment above for why "
        "a floor reaching zero would be the abolished 'unobtainable' "
        "category returning under a new name. The specific half-yield "
        "floor is chosen for that reason, not measured from any real "
        "deposit's long-run decline curve.")

MINING_COST_SCALE_FLOOR = declare(
    "MINING_COST_SCALE_FLOOR", 0.4, kind="temporary_heuristic",
    unit="dimensionless multiple on book capex/opex (minimum)",
    source=None, confidence="D",
    why="However much mining technology cheapens a fresh deposit, it "
        "never costs less than 0.4x book, per this method's own "
        "docstring ('not free'). A defensive bound to keep the "
        "technology-versus-depletion tension a real decision rather "
        "than a runaway, not a derived limit.")

MINING_COST_SCALE_CEILING = declare(
    "MINING_COST_SCALE_CEILING", 2.5, kind="temporary_heuristic",
    unit="dimensionless multiple on book capex/opex (maximum)",
    source=None, confidence="D",
    why="However depleted and untooled a working is, it never costs "
        "more than this multiple of book price, so a fully worked-out "
        "deposit is a real cost penalty rather than an effectively "
        "infinite one. A defensive bound, not a derived limit (this "
        "method's own docstring quotes 'at most 2x book' for the "
        "fully-depleted case, which is a description of the typical "
        "outcome, not this literal ceiling).")

MOTHBALL_CUT_SHARE = declare(
    "MOTHBALL_CUT_SHARE", 0.5, kind="temporary_heuristic",
    unit="fraction of capacity cut per mothballing pass", source=None,
    confidence="D",
    why="How much of a worst-value material's workings are cut in one "
        "mothballing pass, so the survivors keep their own real "
        "commissioning year and depletion clock rather than whole "
        "workings being arbitrarily chosen to survive or not (see this "
        "method's own docstring). A round fraction chosen for that "
        "property, not derived from any real decommissioning practice.")

FOREST_HA_PER_MILLION_KM2_BASE = declare(
    "FOREST_HA_PER_MILLION_KM2_BASE", 1100.0, kind="engineering_estimate",
    unit="hectares/(million km2 of home land) (base, before state reach)",
    source=
    "Re-derived from the same empire-wide charcoal anchor as the old "
    "FOREST_HA_PER_REGION_BASE (500,000 t/yr implying ~667,000 ha "
    "managed empire-wide at a flat charcoal yield per hectare that "
    "CHARCOAL_PER_HA no longer holds; re-derive against the forest increment), converted "
    "from hectares-per-region to hectares-per-million-km2 using Rome's "
    "own home land area (9.5175 million km2 across its seven home "
    "regions, the map folder (data/world/geography/)) as the calibration point, so "
    "that Rome's own pre-revenue ceiling is essentially unchanged by "
    "the switch from counting labels to reading area.",
    confidence="C",
    why="Base standing-woodland ceiling per million km2 of home land "
        "held, before state reach is applied. the geography data carries "
        "no per-region forest figure the way it does for minerals, so "
        "this is still built from a proxy and checked against the one "
        "real empire-wide anchor available, not measured region by "
        "region -- but the proxy is now land area (a physical quantity "
        "every region already carries) rather than a count of however "
        "many labels that area happens to be filed under.")

FOREST_HA_PER_MILLION_KM2_PER_SC = declare(
    "FOREST_HA_PER_MILLION_KM2_PER_SC", 2575.0, kind="engineering_estimate",
    unit="hectares/(million km2 of home land) per unit of forest reach (share of people whose woodland tenure its foresters keep)",
    source="Same empire-wide charcoal anchor and Rome-area calibration "
    "as FOREST_HA_PER_MILLION_KM2_BASE.",
    confidence="C",
    why="How much a more capable state (able to hold woodland tenure "
        "at scale) extends the per-area woodland ceiling - checked "
        "against the same empire-wide total as the base figure, not "
        "independently measured.")

PROSPECT_HOURS_PER_PERSON_DAY = declare(
    "PROSPECT_HOURS_PER_PERSON_DAY", 10.0, kind="temporary_heuristic",
    unit="hours of the mining trade per person-day of prospecting", source=None, confidence="D",
    why="Turns the effort geography's prospecting takes (person-days) into the hours the mining trade's "
        "wage is paid for; the length of a working day, which the construction data states as ten hours.")

AUTO_PROSPECT_PERSON_DAYS = declare(
    "AUTO_PROSPECT_PERSON_DAYS", 2000.0, kind="temporary_heuristic",
    unit="person-days per tile per automatic search",
    source=None, confidence="D",
    why="How much prospecting the automatic mine buys on the held tile with most undiscovered resource "
        "when the deposits found have no room for the material it is short of; a round figure, not "
        "derived from how long a survey party took.")

FOREST_LABOUR_HOURS_PER_HA = declare(
    "FOREST_LABOUR_HOURS_PER_HA", 5000.0, kind="temporary_heuristic",
    unit="labour hours per hectare", source=None, confidence="D",
    why="Purchase price of a hectare of coppice woodland. No attested "
        "attested land-price figure backs this; it exists mainly so "
        "`quote forest` and the purchase itself agree on a real price "
        "at all, per the comment above.")

NITRE_LABOUR_HOURS_PER_M2 = declare(
    "NITRE_LABOUR_HOURS_PER_M2", 40.0, kind="temporary_heuristic",
    unit="labour hours per square metre", source=
    "The figure step() used before this was given a proper `quote` "
    "path (spend / 2.0), carried forward unchanged so buying a bed the "
    "new way costs exactly what the old automatic policy always paid.",
    confidence="D",
    why="Cost to lay one square metre of nitre bed. Not sourced to any "
        "attested saltpetre-works price; a carried-forward implementation "
        "constant.")

NITRE_YIELD_T_PER_M2 = declare(
    "NITRE_YIELD_T_PER_M2", 0.0008, kind="temporary_heuristic",
    unit="tonnes saltpetre/square metre/year", source=None,
    confidence="D",
    why="How much saltpetre one square metre of nitre bed yields a "
        "year. No attested nitre-bed yield figure backs this; it is "
        "sized only to be 'cheap to lay and slow to yield' (see the "
        "comment above), a qualitative target rather than a measured "
        "rate.")

NITRE_SHORTAGE_SAFETY_BUFFER = declare(
    "NITRE_SHORTAGE_SAFETY_BUFFER", 1.20, kind="temporary_heuristic",
    unit="multiple on the bare tonnage deficit", source=None,
    confidence="D",
    why="Extra bed recommended over the bare measured deficit, so a "
        "tiny later change in the portfolio does not put the player "
        "straight back into shortage. Twenty per cent is a round, "
        "plausible safety margin, not derived from how much the "
        "portfolio typically moves.")

AUTO_FOREST_CAPITAL_LABOUR_HOURS_PER_HA = declare(
    "AUTO_FOREST_CAPITAL_LABOUR_HOURS_PER_HA", 36300.0, kind="temporary_heuristic",
    unit="labour hours of capital held per hectare bought", source=None, confidence="D",
    why="How much capital the optimizer holds for each hectare of charcoal forest its mining "
        "policy buys alongside an ore shortfall, so the forest never takes the whole purse. "
        "Tuned, not measured.")

NITRE_BED_SPEND_CEILING_LABOUR_HOURS = declare(
    "NITRE_BED_SPEND_CEILING_LABOUR_HOURS", 40300.0, kind="temporary_heuristic",
    unit="labour hours per year", source=None, confidence="D",
    why="Yearly ceiling on the optimizer's automatic nitre-bed spending, a flat amount of work "
        "rather than a share of the shortfall that beds cannot close. Tuned, not measured.")
