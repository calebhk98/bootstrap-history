# Port handling hours are unsourced, and sea handling money is priced at the unskilled wage

**Status:** open - split from Complaint 613 when its porters and dockworkers were measured hired

**What is wrong.**
- `sea_freight.PORT_HANDLING_HOURS_PER_TONNE` (`sim/geography/sea_freight.py`, read in `sim/markets/port_setup.py` and
  `sim/freight/models.py`) is a labelled heuristic with no source: no opened source gives a per-worker rate of tonnes handled per
  hour (a port-economics page gives a longshore crew's tons an hour but not the crew size).
- The sea handling money (`handling_rates`, `sim/markets/port_setup.py`) is priced at the unskilled wage, while the dockworker
  hours it stands for are hired at the dockworker wage the labour market clears.

**What it would take.** A sourced handling rate (tons per gang-day and the gang size, from a port history), opened and cited,
replacing the constant; and the handling money priced at the dockworker wage of the port's area. Research leads are in
Complaint 613's closed file (Hassig, Aztec Warfare, pp. 32-35, for tlamemeh loads; Ostia and Portus saccarii).
