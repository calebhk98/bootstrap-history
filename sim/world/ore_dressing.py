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

TONNES_ROCK_PER_LABOURER_HOUR_PER_CYCLE = declare(
    "TONNES_ROCK_PER_LABOURER_HOUR_PER_CYCLE", 0.1, kind="temporary_heuristic",
    unit="tonnes of rock crushed and sieved per labourer-hour, per cycle",
    source="One labourer pounding with a hammer on a stone anvil and "
           "working a hand sieve in water, about a tonne in a ten-hour "
           "shift, every cycle taking the whole stream (no cycle is taken "
           "to see less rock than the one before). No throughput is given "
           "in Polybius; Agricola, De re metallica Book VIII (pounding and "
           "sieving) was not opened. Consistency check only: Bettenay 2022 "
           "(Metalla 26.2) has processing staff about equal to mine staff, "
           "and five cycles at this rate cost the same order of hours as "
           "mining a tonne of hard ore (python3 sim/world/deposits.py).",
    confidence="D",
    why="LABELLED HEURISTIC: the per-cycle throughput of hand crushing and "
        "sieving, not measured for Roman practice.")


def dressing_hours_per_tonne_rock():
    """Labourer-hours to crush and sieve one tonne of rock through every cycle."""
    return CRUSH_SIEVE_CYCLES / TONNES_ROCK_PER_LABOURER_HOUR_PER_CYCLE
