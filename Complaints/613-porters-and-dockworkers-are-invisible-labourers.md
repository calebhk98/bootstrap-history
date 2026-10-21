# Porters and dockworkers have no trade, so the largest labour group of a society without draught animals is hidden

**Status:** partly - porter and dockworker trades exist and carriage books to them; a whole-game run with real porter workforces is not yet checked (see "What is left")

Part of Complaint 530 (Most ancient occupations have no trade, and their hours are booked as farming). Depends on 609.

**What was wrong.** Land carriage on foot was a route mode whose hours were `labourer`, and port loading was a fixed
hours-per-tonne booked to the unskilled trade. In a society without draught animals (the Mexica) porters were among the
largest labour groups, so the labour market never saw the demand for them (see also 552).

**What is built.** `data/world/trades.json` has `porter` and `dockworker` trades (training 0: anyone can take them up at
once; no sourced fatality rate, so zero with the absence statement). `data/world/geography/route_modes/modes.json` gives
foot `crew_trade: porter` and sail `handling_trade: dockworker`. `routes_carriage` passes the trade,
`EconomySetup.carriage_handling_trade` carries it, and `Crew.hours_by_trade` (`sim/economy/carriage_hours.py`) books
handling to it. `CARRIAGE_CREW_UNSKILLED_SHARE` (a labelled heuristic) now applies only to modes whose trade asks more
training than the unskilled one. `occupation_groups.json` lists both in the transport group. Test:
`sim/tests/test_porters_and_dockworkers.py`.

**What is left.**

- Verify in a whole game that porter workforces form: `python3 -m sim.tests --slow --only occupational_distribution,carriage_hours --jobs 1`
  and a multi-year `mexica_1500` run (a 2-year `economy-check --civs mexica_1500 --years 2` ran clean when this was built).
- `PORT_HANDLING_HOURS_PER_TONNE` stays a labelled heuristic: no source found (a port-economics page gives a longshore crew
  5 to 10 tons an hour but not the crew size, so no per-worker figure follows).
- The sea handling money (`handling_rates`) is still priced at the unskilled wage; porter and dockworker wages come from the
  labour market, not from it.

**Research needed.** Hours of porter and longshore labour per tonne (Roman Ostia and Portus portage, tlamemeh loads and
daily distances from a primary or monograph source, such as Hassig, Aztec Warfare and Trade and Conquest, which has not been opened).
The foot mode's 27 kg and 22 km a day sit near Wikipedia "Tlamemeh" (23 kg, 21 to 25 km a day; secondary).

**Research pass (source-porter-hours).** No figure was replaced; no opened source supports a better one.
Opened: Law and Rodway, Himalayan Journal 64 (2008), "Lowland porters in the Solu Khumbu" (Nepal; commercial porters carry far
above body weight, "a 24 year old man who weighed 52 kg carrying a 90 kg load from Jiri to Kakou, a six-day walk"; no km a day,
so no daily distance follows; Nepal is a different society and a paid-by-weight market, not a Mexica relay).
Wikipedia "Tlamemeh" re-opened: quotes "carrying on average 23 kilos" and "daily commute of 21 to 25 kilometers", with no
inline citation and no Hassig page. Not opened (503/403): Bastien et al. 2005 (Science), Malville 1999 (only seen as quoted in
search summaries), the Karwansaray blog quoting Hassig pp. 32-33 for a load and a five-league stage. Port hours per tonne:
searches for Ostia and Portus saccarii and early-modern stevedoring found no per-worker rate; the one opened-in-summary source
gives pay per ton, not hours. Still open: open Hassig (Aztec Warfare 1988, pp. 32-35) in print, Bastien 2005 full text, and a
port-history rate for tons per gang-day with the gang size.
