"""Ore dressing by hand: repeated crush-and-sieve cycles. Standalone.

Every recipe that crushes and washes rock before smelting or amalgamating
charges the same hours per tonne of rock, so the lead, direct silver, jarosite
and lode gold routes cannot drift apart (Complaints/333).
"""
from sim.constants import declare

CRUSH_SIEVE_CYCLES = declare(
    "CRUSH_SIEVE_CYCLES", 5, kind="engineering_estimate",
    unit="crush-and-sieve passes the ore makes before smelting",
    source="Strabo, Geography 3.2.10 (Perseus, read), citing Polybius on the "
           "New Carthage silver mines: the ore is crushed and sieved through "
           "sieves held in running water, the residue pounded again, and "
           "this is done five times before the ore is smelted.",
    confidence="B",
    why="Sets how many times every tonne of rock passes through hand "
        "crushing and sieving.")

MELLE_PROCESSING_WORKERS = declare(
    "MELLE_PROCESSING_WORKERS", 100, kind="engineering_estimate",
    unit="workers crushing, separating, smelting and refining at the modelled mine",
    source="Bettenay 2022, Metalla 26.2, workforce section (p. 77, read): "
           "processing staff in later documented operations run from 30 "
           "percent (early Kongsberg, Berg 1988) to 50-65 percent (Slovak "
           "operations, Vozar 2000) of staff, about as many as work the mine, "
           "so a Melle workforce of 250-300 divides about equally into "
           "mining, processing and forest: 83 to 100 each. The upper end is "
           "taken, matching his 100 face miners.",
    confidence="C",
    why="Sets the labour that turns a tonne of mined ore into smelting "
        "concentrate, from an attested staff share instead of a guessed "
        "per-cycle throughput.")

MELLE_WORKING_DAYS_PER_YEAR = declare(
    "MELLE_WORKING_DAYS_PER_YEAR", 300, kind="engineering_estimate",
    unit="days per year", source="Bettenay 2022, Table 4, note 3 (six days "
    "a week less a few saints' days).", confidence="C",
    why="Converts the Melle processing staff into worker-days.")

MELLE_ORE_TONNES_PER_YEAR = declare(
    "MELLE_ORE_TONNES_PER_YEAR", 2250.0, kind="engineering_estimate",
    unit="tonnes of ore presented for crushing per year",
    source="Bettenay 2022, Table 4, realistic model, 'Total ore mined by all "
           "miners per year'.", confidence="C",
    why="The tonnage the Melle processing staff handles.")

MELLE_LEAD_TONNES_PER_YEAR = declare(
    "MELLE_LEAD_TONNES_PER_YEAR", 52.0, kind="engineering_estimate",
    unit="tonnes of final lead per year",
    source="Bettenay 2022, Table 4, realistic model.", confidence="C",
    why="Lets the smelting share of the Melle processing staff be taken out.")

SMELTING_LABOUR_HOURS_PER_TONNE_LEAD = declare(
    "SMELTING_LABOUR_HOURS_PER_TONNE_LEAD", 359.0, kind="temporary_heuristic",
    unit="labourer-hours per tonne of lead for furnace, smith, roasting, "
         "bellows and cupel",
    source=None, confidence="D",
    why="The lead recipe charges these separately from dressing (furnaceman "
        "200, smith 15, roasting 18, bellows 46, cupel 80), so the Melle "
        "processing staff's dressing share is its total less this. The "
        "recipe's own heuristics, not a source.")


def processing_worker_days_per_tonne_ore():
    """Worker-days a tonne of ore costs in crushing, separating and smelting,
    from the Melle staff share and output."""
    return (MELLE_PROCESSING_WORKERS * MELLE_WORKING_DAYS_PER_YEAR
            / MELLE_ORE_TONNES_PER_YEAR)


def _dressing_hours_per_tonne_ore():
    from sim.world.mine_fire_setting import MINING_SHIFT_HOURS
    smelting_per_tonne_ore = (SMELTING_LABOUR_HOURS_PER_TONNE_LEAD
                              * MELLE_LEAD_TONNES_PER_YEAR / MELLE_ORE_TONNES_PER_YEAR)
    return (processing_worker_days_per_tonne_ore() * MINING_SHIFT_HOURS
            - smelting_per_tonne_ore)


TONNES_ROCK_PER_LABOURER_HOUR_PER_CYCLE = declare(
    "TONNES_ROCK_PER_LABOURER_HOUR_PER_CYCLE",
    CRUSH_SIEVE_CYCLES / _dressing_hours_per_tonne_ore(),
    kind="engineering_estimate",
    unit="tonnes of rock crushed and sieved per labourer-hour, per cycle",
    source="Derived: the dressing hours a tonne of ore costs at Melle "
           "(processing worker-days from Bettenay's staff share and output, "
           "times Agricola's seven-hour shift, less smelting) spread over "
           "Polybius's five cycles. No source gives a throughput per cycle: "
           "Polybius gives none; Agricola Book VIII (Hoover, read in full "
           "for rates) describes sorting, pounding and washing without "
           "tonnages or man-days; Kakavoyannis 2001 (BSA 96, read) gives "
           "about 33 workers to a Laurion washery but no tonnage; "
           "Morin-Hamon 2023 gives washery dimensions only.",
    confidence="C",
    why="Hand crushing and sieving throughput, fixed by the attested share "
        "of staff working on processing rather than guessed.")


def dressing_hours_per_tonne_rock():
    """Labourer-hours to crush and sieve one tonne of rock through every cycle."""
    return CRUSH_SIEVE_CYCLES / TONNES_ROCK_PER_LABOURER_HOUR_PER_CYCLE
