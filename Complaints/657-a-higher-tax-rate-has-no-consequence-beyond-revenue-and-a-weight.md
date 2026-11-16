# A higher tax rate has no consequence beyond revenue and a typed burden weight

**Status:** partly - the base answers a raise by hiding, flight and unrest; both hiding constants are now sourced ballparks (confidence C); what remains is non-sourcing work (the immunity and flight items under Still open) and a pre-modern check of the curve

Follows from 626 (tax rates as a state choice).

**What is wrong now.** Nothing in the list that opened this complaint: the AI state's menu foresees unrest, a harvest tax reaches the
land demand, the farm-hours choice and the producers' run, plant and entry decisions (`harvest_tax.py`, the plan, close and entry
kernels and their reference functions), and `FISCAL_BURDEN_WEIGHT` is deleted. The hiding constants' missing source is
below (Sourcing the hiding curve).

**Why it matters.** Without a full response of the base there is a ceiling to taxation only at the rate cap, and a state
cannot lose by overtaxing in every way a real one does (CLAUDE.md 4.1: the outcome should come from lower-level state, not
from a typed elasticity).

**What it would take.** Finish the payers' own choices (households and firms compare what they keep with what they could keep
elsewhere), then the AI state values the loss of base as a consequence of a raise. Test: raising a rate on a base whose payers
can leave lowers the base next year; an AI state with the loss in its menu raises a rate less than one without.

## Built

- **Harvest tax and farm effort.** `sim/agents/tax_burden.py` `harvest_share_taken` reads the state's present rates
  (levers included), the tiles each form covers and the share its officials reach. Its only reader is
  `sim/campaigns/stability.py`: the farm-hands leg (the labour package's farm allocation and `farm_intake`) is deleted, so
  nothing yet takes the harvest tax into a household's choice of farm hours against the wage; that choice belongs to the
  economy's plots and farm producers and is open.
- **Land tax reaches the owner's holding.** `tax_burden.land_tax_share_of_rent` turns a form on `land_rent` or `land_value`
  into a share of the rent; `YearInputs.land_tax_share_of_rent` carries it to `land_market.settle_year` and
  `titles.settle_tenancies`: a lessor whose managing cost plus the tax exceed the rent lets the title go (`titles.release`, 538).
- **Poll tax** acts through household cash: `taxes._collect_money` pays no more than the purse holds, and an unpaid remainder
  is an arrear.
- **Income is hidden from a rising rate.** `sim/agents/evasion.py` `hidden_share`: a payer hides the share at which the last
  unit's saving equals the rising cost of hiding it, up to a ceiling, so a higher rate hides more and a state whose
  officials reach more is hidden from less. `revenue.taxed_actors` assesses only declared income; `fiscal_response.rate_raise_yield`
  nets the extra hiding. The economy's forms hide by the same rule through `EconomySetup.hiding`
  (`sim/markets/port_setup.py`), so the economy imports nothing from the actors. Customs duties on border imports
  are not under it. `HIDEABLE_SHARE_OF_INCOME` and `HIDING_MARGINAL_COST_AT_CEILING` (`sim/agents/tuning_evasion.py`) are
  labelled heuristics with `retire` 657.
- Tests: `test_tax_evasion.py`, `test_tax_evasion_economy.py`, `test_tax_flight_and_liability.py`.

- **Flight is the migration rule.** `sim/labour/market/migration.py` scores each route by the income kept after the state's take
  in that area (`YearInputs.taxed_share`) less the move's cost, which now includes the expected penalty of recapture
  (`Route.expected_penalty`, from `sim/agents/flight.py` `expected_penalty_of_leaving`: the chance of recapture at the
  state's reach on the tile he goes to times what he owes with the penalty at that reach). Taxed land a fleeing tenant leaves
  is released to no holder by `sim/economy/titles_flight.py` `tenant_flees` (538's rule).
- **Liability is a state choice.** `sim/agents/liability.py`: individual, or collective per unit, where the stayers split the
  unit's assessment (the merismos). Tested for the sourced spiral: under collective liability a shock raises the stayers'
  take and a larger share leaves each year; under individual liability the take and the share leaving stay flat.
- **Levers** (`sim/agents/government_levers_tax.py`, through `lever`/`levers`): `liability`, `amnesty` (share of arrears
  waived), `immunity` (years a taker of deserted land owes nothing; `flight.share_after_immunity`) and `remission` (every
  form's rate, read through `government_levers.revenue_forms`, so revenue and `tax_burden` see it).
- **Hiding and Yitzhaki.** A penalty in proportion to the tax unpaid leaves the rate out of the choice; the rate effect in
  `evasion.py` comes only from the hiding-cost curve, which stays labelled (`HIDING_MARGINAL_COST_AT_CEILING`).
- Tests: `test_tax_flight_and_liability.py`.

- **Flight is wired into the year.** `YearInputs.taxed_share_by_tile`, `state_reach_by_tile`, `amnesty_share` and `immunity_years` are filled
  by `sim/markets/port_flight.py` from `sim/agents/flight_inputs.py` (the state's income forms times its reach on the tile, under its liability rule
  with the people who fled counted out of those who remain). `sim/economy/flight_routes.py` turns them into `YearInputs.taxed_share` and each route's
  `expected_penalty` (the actors' `flight.expected_penalty_of_leaving`, handed in as `EconomySetup.flight`, so the economy imports no actor). After the
  labour year `sim/economy/flight_step.py` runs `flight_year.py`: tenants of an area people left leave their land (`titles_flight.tenant_flees`), the leavers
  are kept as `EconomyRecord.fugitives` with what they owe, and a fugitive returns by the migration rule run backwards (his refuge's income against home's after the take,
  less the arrears, `flight.arrears_owed_by_fugitive`, with the amnesty lever; `flight.share_after_immunity` on the take he meets at home).
- **The AI state's menu counts flight and has the tax-response levers.** `fiscal_flight.py` calls the migration rule for the share of payers who leave at a take
  (only those who can reach a tile the officials do not); `rate_raise_yield` nets the base lost that way on forms on income. The menu offers `remission`
  (only where a cut yields more), `amnesty` (where people have fled) and `liability` (collective, where the leavers' assessment on the stayers recovers more than the extra flight loses),
  and `Government.pull_tax_response_levers` sets the levers the choice covered money with.
- Tests: `test_tax_flight_wiring.py` (rules called with built inputs; the engine's year is covered only by the whole-game smoke topics).

- **The AI state's menu foresees unrest.** `sim/agents/fiscal_unrest.py` calls `unrest.grievance` and `unrest.unrest` (the rules the
  stability phase reads) on the extra take of an option: a take above the one people are used to is their grievance, the share it
  makes discontented does not pay it, so `net_of_unrest` is the money the option still raises and `lost_per_money_kept` is the
  consequence (`unrest_lost`) the policies value. The levy, the demand in kind, a rate raise and collective liability go through
  it (`fiscal_response._taxed_option`). `FISCAL_BURDEN_WEIGHT` and the `income_taken` consequence are deleted. Unrest is counted
  from the extra take alone (hunger and the liability burden of the tiles are not in the menu's reading). Test: `test_fiscal_unrest.py`,
  `test_state_fiscal_response.py` (a rate raise is offered for less than its gross yield).
- **Harvest tax reaches land demand and farm hours.** `tax_burden.harvest_share_by_material` (the figure `stability.py` reads, per
  material) goes to the economy as `EconomyYearInputs.harvest_share_by_good` and `EconomySetup.harvest_share_by_good`; `sim/economy/harvest_tax.py`
  nets it off the output prices in `land_market.demands_of`, in `land_bid_year.best_margin` (a household's land bid) and in
  `labour_ask_floor.plot_return_per_hour` (the next plot hour against the wage, so `plot_hours_kept` and the wage floor fall with the tax).
  Tests: `test_economy_harvest_tax.py`, `test_economy_land_market.py`, `test_economy_labour_ask_floor.py`.
- **Remission** is offered exactly where a cut yields more (`rate_cut_yield`), which is past the rate that yields most; it is not
  offered below it by design (tested in `test_tax_flight_wiring.py`).

**Still open.** (a) Immunity is read only where a fugitive weighs returning to deserted land: released land is still never taken up by anyone else (nothing in the economy
fills a title below one on a tile except a clearer's new ground), so a taker's years without tax are not applied after the first comparison. All net outflow from a taxed area is
treated as flight (no split of the part that is not about tax); a fugitive's refuge is the area that gained most that year, not tracked per person; arrears accrue as a year's take at
the area's subsistence, not the person's income, and `Route.expected_penalty` counts this year's take only. The levy and the demand in kind do not net flight (they net unrest). Whole-game effect
not measured (a slow topic and the fingerprint are needed). Whole-game effect of the harvest tax on runs not measured (a slow topic and the fingerprint are needed).

## Research needed

No source on pre-modern tax pressure, flight and abandonment was opened, so the hiding constants
have none (see Sourcing the hiding curve below). The question: how did taxpayers respond to a heavier take in the Roman and medieval worlds, by form (flight of
tenants and the abandoned land of the late empire, anachoresis in Roman Egypt, concealment, evasion, revolt), and at what
share of the harvest did each begin? Sources to open: Roman Egypt tax-flight papyri studies, the Codex Theodosianus on agri
deserti, and medieval English peasant flight and tallage studies. A response curve fitted to those is a validation of the
mechanism, not an input to it.

## Sourcing the hiding curve

**Searched, nothing usable opened (2026-11):** web searches for Roman Egypt census and tax evasion (Monson and Scheidel,
*Fiscal Regimes and the Political Economy of Premodern States*, 2015, pp. 229-257, is named as the general introduction but
its text was not reachable; the ResearchGate and academia.edu papers on evasion in Roman Egypt returned HTTP 403 or search
snippets only); pre-modern concealment shares and bribe costs (Mughal, Ming, medieval: only modern evasion studies and
popular essays); Zhang Juzheng's 1581 Ming land survey (opened *Fir and Empire*, Appendix A, "Forests in Tax Data": surveys
"added nearly a quarter more farmland", read there as reregistering forest converted to farmland, and registration figures are
"at best indexes of fiscal acreage"; it does not give a hideable share or a cost of hiding). No source found.

**Searched again (second pass), one partial datum:** Habib, *The Agrarian System of Mughal India* (archive.org
`the-agrarian-system-of-mughal-india-1556-to-1707`, OCR text, read for concealment, collusion and measurement): it describes
qanungos colluding with 'amils to make fictitious accounts and reduce assessments (Aurangzeb's order, ch. on revenue
assignments) and a patwari/qanungo commission of two per cent of the revenue (*Ain*, I, p. 300, "sad-dot"), but gives no share of
land found off the rolls by measurement. Ray Huang's *Taxation and Governmental Finance* and Ho Ping-ti's *Studies on the
Population of China* (archive.org borrowable only, HTTP 401) and the Cambridge chapter page (host not reachable) could not be
opened. The one figure opened: Arslan 2022, "Tahrir Defteri Verilerinin Nufus Hesaplamalari icin Guvenilirligine Dair Mukayeseli
bir Inceleme", Medeniyet Belleten 2/3, p. 21 (https://dergipark.org.tr/en/download/article-file/2568111): 95 adult men found
in the 1559-1561 Uskudar court records are absent from the 1560 tahrir, "approximately 14%" of the 676 registered adult men, a
lower bound; about 20 were exempt. That is persons off the rolls in one town, not an income share and not a response to
officials looking harder, so neither constant changes (0.5 and 0.5); the datum is recorded in `HIDEABLE_SHARE_OF_INCOME`'s
`why`. Still unsourced: the ceiling and the cost of the last unit hidden. Status stays partly.

**What it would take.** Open a work that gives, for a pre-modern agrarian state, either the share of land or income found
off the rolls when officials looked harder (cadastral resurveys: Ming 1581, Roman Egypt census cycle, Domesday, Mughal
`zabt`), or what concealment cost payers (fees to scribes and surveyors). Cite author, work, page. Set the two constants
from it, or replace them by the holdings model the `retire` text names. Candidates: Monson and Scheidel (eds.) 2015; Kiser and
Kane on tax farming; papyrological studies of Roman Egypt land declarations.

## Sourced (2026-11, ballpark standard)

- `HIDEABLE_SHARE_OF_INCOME` 0.5 -> 0.55, confidence C, now `engineering_estimate`. Congressional Research Service IF11887 (https://www.everycrsreport.com/reports/IF11887.html): IRS net misreporting 1 per cent of wages and salaries, 15 per cent of partnership and S-corporation income, 55 per cent of sole-proprietor income (2014-2016). The income class with no third-party reporting is the analogue for a state with none. Arslan 2022 (Uskudar tahrir, 14 per cent of men off the rolls) is a lower bound for persons.
- `HIDING_MARGINAL_COST_AT_CEILING` 0.5 kept, confidence C, derived: Anderson 2014 (https://dergipark.org.tr/en/download/article-file/1730550, average tax bribe 2.1 to 8.1 per cent of revenues across transition countries) over Alm, Martinez-Vazquez and McClellan 2016 (https://econpapers.repec.org/RePEc:eee:jeborg:v:124:y:2016:i:c:p:146-163, bribe-soliciting inspectors go with 4 to 10 points less of sales reported) gives 0.21 to 2.0 bribe per unit hidden; geometric middle 0.65. The range is wide; 0.5 sits inside it.
- Both are modern analogues, not pre-modern measurements. A pre-modern response curve (Roman and medieval) is still a validation target, not an input.

## Pass (2026-11, any-source bar)

Both constants kept; non-US and older evidence added to `HIDEABLE_SHARE_OF_INCOME`'s `source` in `sim/agents/tuning_evasion.py`. Opened: Kleven, Knudsen, Kreiner, Pedersen and Saez 2011 (Econometrica 79(3), Denmark): detected evasion 14.9 per cent of self-employment income against 1.1 per cent of personal income, 44.9 per cent of self-employed taxpayers adjusted; with the 3.28 multiplier the paper cites for the US, 14.9 x 3.28 = 49 per cent, near 0.55 (the detected figure alone is 3.7 times lower). Wikipedia, Tax evasion: UK 2016-17 tax gap 5.7 per cent; Scandinavian evasion about 3 per cent of personal taxes, about 30 per cent in the top 0.01 per cent of wealth. Wikipedia, Poll taxes of 1376-1381: the 1379 tax raised 18,600 pounds against 50,000 sought, "widespread evasion"; direction only. Medieval lay subsidy under-assessment and Mughal tax-farming: no source found. All still modern or loosely pre-modern analogues.
