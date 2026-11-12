# Port handling hours are unsourced, and sea handling money is priced at the unskilled wage

**Status:** closed - sourced and the handling money repriced at the dockworker wage

**What is wrong.**
- `sea_freight.PORT_HANDLING_HOURS_PER_TONNE` (`sim/geography/sea_freight.py`, read in `sim/markets/port_setup.py` and
  `sim/freight/models.py`) is a labelled heuristic with no source: no opened source gives a per-worker rate of tonnes handled per
  hour (a port-economics page gives a longshore crew's tons an hour but not the crew size).
- The sea handling money (`handling_rates`, `sim/markets/port_setup.py`) is priced at the unskilled wage, while the dockworker
  hours it stands for are hired at the dockworker wage the labour market clears.

**What it would take.** A sourced handling rate (tons per gang-day and the gang size, from a port history), opened and cited,
replacing the constant; and the handling money priced at the dockworker wage of the port's area. Research leads are in
Complaint 613's closed file (Hassig, Aztec Warfare, pp. 32-35, for tlamemeh loads; Ostia and Portus saccarii).

**Resolved.**
- `PORT_HANDLING_HOURS_PER_TONNE` 2.0 to 4.8 worker-hours per tonne (loading plus unloading), confidence C, derived from two opened pages:
  porteconomicsmanagement.org/?p=5664, "The typical productivity level of a longshoremen crew was 5 to 10 tons per hour"; and
  marereport.namma.org/?p=412, a gang of "the ten men in the hold of the ship plus the two winchmen and hatch tender" with four dock
  workers and a foreman, eighteen in all. 18 / 7.5 tonnes an hour = 2.4 worker-hours per tonne per end, 4.8 for two ends. A winch-era
  gang, so a lower bound for earlier ports.
- `port_setup.handling_wage` prices the sea handling money at the dockworker wage (the mode's `handling_trade`), falling back to the
  unskilled wage when there is no quote; the handling trades are now among the trades whose opening wage is quoted. Tests in
  `sim/tests/test_porters_and_dockworkers.py`.
