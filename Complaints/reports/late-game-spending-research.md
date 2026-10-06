# Research: late-game spending, remaining items of Complaint 190

Research for `Complaints/190-late-game-uses-for-money.md`. Written on branch
`late-game-spending-research` (from `structural-dedupe-and-owner-decisions`).
No code or data was changed and no tests were run. Engine claims were read in
the files cited; commands to re-measure are given where a number would
otherwise be quoted.

Source tags: **read** = page content read in a search result or known text
read in full; **snippet** = search-result excerpt only; **recalled** = from
memory of the literature, not re-checked this session. Figures quoted are
cited; none is a simulator value.

## What a benefaction is, and what it can reach

The fifteen works in `data/branches/56_benefactions.json` are ordinary nodes
with `rev_hours` 0, derived `up_hours`, `mechanics.upkeep_full`, and
`capability.scalable` (`literacy` or `population`) for repeatable units
(`data/branches/MECHANICS.md`, section Benefactions). The effect fields they
actually set, with the engine reader:

| Field | Used by | Engine reader |
|---|---|---|
| `schooling_flow` | free school, library | `_schooling_flow`, `effective_schooling_flow`, `_advance_literacy` in `sim/engine/society_adoption.py` (moves `literacy_general` and `literacy_elite` toward their ceilings; printing diffusion multiplies it) |
| `standing` | most | reputation floor, `sim/engine/society_state_pressure.py` |
| `staff_capacity` | research foundation, patronage | labour capacity, `sim/labour/` |
| `hazard_counters` kind `staff_loss` / `output_factor` | hospital, water works, grain dole, harbour, underwriting | `HAZARD_COUNTERS` in `sim/engine/projects_completion.py`, `hazard_relief` in `sim/engine/hazard_relief.py`, `_shock_staff_loss` and `_shock_output_factor` in `sim/engine/society_hazards.py` |
| `protection`, `patron_protection`, `alarm_factor`, `eminence_hazard_factor` | games, temple, state subvention | `update_protection` in `sim/engine/society_state_pressure.py` |
| `credit_line`, `debt_rate_discount` | house bank | `sim/engine/economy_credit.py` (the household's own credit) |
| `reach`, `supervision_room` | harbour, telegraph, expedition | `solve_prices_reach` and labour supervision |

Other channels that exist but no benefaction uses: `corpus` (knowledge hedge;
`sim/engine/mechanics.py`, loss in `_sack_corpus_loss` in
`sim/engine/society_hazards.py`), `disease_burden` (`_disease_burden` in
`sim/engine/core.py`, weights in `data/civilizations/_TECH_EFFECTS.json`),
`state_credit` (lets a state borrow; `sim/agents/government.py`
`credit_ceiling`), `labour_productivity`, `market_standing`, `room_places`.

Two engine facts matter for every row below.

1. The hazard counters act on the founder's own household hazards, not on the
   nation's population. Nothing a benefaction does today changes national
   mortality or national recovery. National disease burden moves only through
   `disease_burden` holders.
2. A transfer primitive exists: `pay_state(amount, purpose)` in
   `sim/engine/society_actors.py` calls `ledger.transfer(household, treasury)`.
   Only the requisition and military-supply code calls it
   (`sim/engine/society_state_pressure.py`); no player command or node does.
   The state's debt is its negative `money` (`debt()` in `sim/agents/borrowing.py`).

## Existing nodes that already name each item

Measured by scanning `data/branches/[0-9]*.json` for the ids and reading the
fields:

| Node | State |
|---|---|
| `fin_museum` | venture with upkeep and revenue, no `mechanics` |
| `prn_newspaper_institution`, `fin_newspaper_business` | ventures, no `mechanics`; the first carries trait `status_threatening` and negative `gov` |
| `fin_gambling_house`, `fin_lottery` | ventures, no `mechanics`, no prerequisites (house) |
| `exp_colony_administration` | venture with a `precaution` only |
| `civ_street_lighting`, `hom_electric_lighting` | no upkeep or revenue (street lighting) / venture with no `mechanics` (home) |
| `fin_public_debt` | `state_credit` only; no payoff |
| `md2_child_clinic`, `md2_maternal_clinic` | knowledge nodes, no `mechanics` |

## 1. Museums

| Item | Content |
|---|---|
| Historical effect | The Ashmolean (1683) was built to display collections, teach from them and hold a library, lecture room and chemical laboratory, open to the public (read: Pitt Rivers / Ashmolean history pages from the search). The British Museum was founded in 1753 and opened in 1759, as collections began to call themselves "public" (read). Effects: preservation of specimens and texts against loss, teaching and research material for a university, prestige for the donor. |
| Mechanism to act through | Preservation: `corpus` (`rank`, `loss_chance`, `fraction_lost`, `dispersed`) reduces knowledge lost in a sack; a collection is a physical hedge. Training: `schooling_flow` (small, as for the library) and `staff_capacity` scholars. Prestige: `standing`. Admission revenue stays with the existing venture; a benefaction sets `rev_hours` 0 so the free-admission case is the benefaction, the ticketed case stays `fin_museum`. |
| Data-only or engine | Data-only. A new `ben_public_museum` node: `pre` `fin_museum` plus `ben_public_library`, `mechanics`: `capability.scalable` `literacy`, `corpus` (a rank between `corpus_written` and `corpus_dispersal`, read the rank scale in `data/branches/00_core.json`), `schooling_flow` smaller than the library, `standing`, optionally `staff_capacity` for curators. Check that a second `corpus` holder is honoured (`best_corpus_node` takes the best, so a museum matters only below the best hedge; `redundant_with` in `capability` can express that). |
| Fields set | `upkeep_full`, `capability`, `corpus`, `schooling_flow`, `standing`, `staff_capacity` |

## 2. Newspapers

| Item | Content |
|---|---|
| Historical effect | The annual number of newspapers printed in England rose from under a million to fourteen million between 1690 and 1780, after the Licensing Act lapsed in 1695 (read, search result). Advertising was needed to pay for the stamp duty, and provincial papers spread late in the century (read). Coffee houses and reading rooms spread news (read). Literacy rose alongside, about 60 per cent of men and 30 per cent of women signing their names by 1800 (snippet, an approximate figure of the search summary, treat as unverified). Effects: price and news information for merchants (recalled), political pressure and exposure of officials (recalled), reading practice that supports literacy (recalled). |
| Mechanism to act through | Reading practice: `schooling_flow` (like the library, "teaches by example"). Information spread: the `information` trait already drives `information_diffusion_index` and `_diffusion_pace` in `sim/engine/society_diffusion.py` (a corpus and literacy accelerate it). Price information: `reach` (multiplier on market reach), as the telegraph benefaction does. Political pressure on officials: state attention is `state_notice` and `alarm_factor` (a paper that criticises the state raises alarm; a paper the founder owns raises `eminence_hazard_factor`). The existing node already has `status_threatening` and `gov` -2, so a state may forbid it. |
| Data-only or engine | Data-only for the effects above. What is not expressible: a paper that turns public opinion against the state (needs state legitimacy, which does not exist as a field; see `Complaints/` search for legitimacy), and per-town circulation. Give the benefaction both a boost and a hazard: `schooling_flow`, `reach`, `eminence_hazard_factor` above one, `alarm_factor` above one. |
| Fields set | `upkeep_full`, `capability` (`literacy`), `schooling_flow`, `reach`, `standing`, `alarm_factor`, `eminence_hazard_factor` with `hint_when_running` |

## 3. Gambling houses and lotteries

| Item | Content |
|---|---|
| Historical effect | The English state ran lotteries from 1694 to 1826, about one hundred and seventy lottery loans, as a way to raise public money and retire or fund debt (read: Wikipedia and a Queen's University thesis abstract). Genoa's draw on the names of Great Council members is the model of the modern lottery (read). Houses took a cut of winnings; they were licensed, taxed or banned, and attracted violence (the node's own note; recalled). |
| Mechanism to act through | Revenue and licence: the existing `fin_gambling_house` and `fin_lottery` ventures already have revenue; what is missing is the state's reaction. Licensing as a state favour is `patron_protection` and `state_approval`. Prohibition risk is `group_prohibition_of` in `sim/engine/interest_groups.py`. Social harm (debt bondage, violence) has no ready field except `eminence_hazard_factor` and `alarm_factor`; bondage exists as `bondage_debt` on the household (`sim/engine/core_step_phases.py`) but is not linked to gambling. |
| Data-only or engine | A gambling house is not a benefaction; it is already a venture. The data change is to add `pre` (a licence or state-favour precondition, for example `fin_government`), a `protection` need and `alarm_factor` above one so that it works as "profitable, risky, banned unless licensed". The state lottery is a transfer to the treasury from the venture's revenue: needs a revenue-share-to-state field (engine, small: the tax code in `sim/agents/government.py` `assess`/`collect` already taxes income, so a per-concern levy is the new piece). Not a spend of money, so low priority for Complaint 190. |
| Fields set | `pre`, `alarm_factor`, `eminence_hazard_factor`, `protection`; new levy field for the state share |

## 4. Colonies

| Item | Content |
|---|---|
| Historical effect | The Dutch East India Company founded the Cape in 1652 as a refreshment station of 80 employees, to grow fruit and vegetables and run a hospital, because sailor mortality, scurvy above all, was high; the economy rested on shipping and farming, and mortality was high, higher in smallpox outbreaks (read). Jamestown lost about two of every three colonists in the winter of 1609 to 1610 when the neighbours stopped trading and besieged the fort (read). Effects: settlement of land, supply bases that lower voyage losses, a risk of heavy loss to starvation, disease and war, and a cost to a company or a state. |
| Mechanism to act through | Supply base effect: `reach` and `supplies_material_by_sea_route` (`sim/engine/economy_materials.py`), and `hazard_counters` `output_factor` for voyage losses. Risk of loss: `precaution` and the failure roll in `sim/engine/projects_completion.py`; `apply_staff_survival` for losing settlers. These capture a trading post. |
| Data-only or engine | Trading post: data-only (this is `exp_colony_administration` plus a benefaction wrapper). A settlement with land, people and a local economy: needs engine state that does not exist. The geography package has tiles, regions and `labour_settlement.py` (where the household lives and a town's people, tied to the home nation's tile shares), and `sim/world/land.py` has tile lands for the civilisation's `home_regions`, but there is no owned territory, no population that is not the home nation's, and no second market. The audit `Complaints/reports/action-and-construction-node-audit.md` already lists "a built work has no place and no size" as engine work. Colonies need: tile ownership by an actor, a settled population with its own demography, a link route, and a defence and disease model for the frontier. |
| Fields set | Trading post: `reach`, `hazard_counters`, `precaution`, `standing`. Real colony: none; new state |

## 5. Paying off a state's debt outright

| Item | Content |
|---|---|
| Historical effect | Walpole used a sinking fund in the 1720s; the rate on government securities fell from six to five per cent in 1717 and from five to four per cent in 1727 (snippet, a search summary of an older text; the fall is associated with the fund, not proved caused by it). The fund was often raided: only a small part of the money paid in was applied to debt (snippet, figures cited by the result: about 24 million of about 200 million pounds). Pitt's 1786 reform shielded it from raiding and paid off some ten million pounds before the wars (snippet). Effects: lower yields and better state credit if the repayment is credible, and a smaller interest bill; also the state was more free to borrow again in war (recalled). |
| Mechanism to act through | A transfer from household to treasury already exists as `pay_state`. The state's borrowing rate comes from `borrower_rate(market_rate, standing_discount, used)` in `sim/agents/borrowing.py` with `used` the debt over `credit_ceiling`; paying debt down lowers `used`, which lowers the rate, which is the historical mechanism, and `credit_standing` is `state_capacity`. The unfunded part of the state's budget and its levy follow `sim/agents/government.py` `seek_shortfall` and `levy_rates`, so a smaller interest bill should reduce the levy on taxpayers including the founder. |
| Data-only or engine | Needs a new effect type: an action, not a standing effect. A node cannot express "transfer this sum once". Options: (a) a command (`pay state debt <amount>`) calling `pay_state`, with a log line and a favour effect (`state_approval`, `patron_protection` step); (b) a repeatable node whose completion fires a one-off transfer, which needs a completion hook akin to `grants` in `sim/engine/projects_completion.py` (a "transfers" field). Option (b) keeps content in data (CLAUDE.md 4.7). Whether a household payment may exceed the state's debt must be decided: the state's `money` can go positive, which then is a reserve, not a repayment. Check with `python3 sim/simulator.py` state screens; no command prints the state's debt directly (look at `state_treasury().record` fields). The existing `ben_state_subvention` is an upkeep-based favour, not a debt payment. |
| Fields set | New: `transfer_to_state` (amount scaled by `book_money`, optional `only_to_debt`); existing `patron_protection`, `alarm_factor`, `standing` |

## 6. Electric city lighting

| Item | Content |
|---|---|
| Historical effect | Electric light let activity continue after dark and factories run round the clock, for example Lancashire textile mills (snippet; popular summary, treat as weak). Reviews of street lighting find lower crime, an average of about one fifth across the reviewed studies, though night-only studies show no effect (snippet, College of Policing toolkit and others). Gas lighting preceded it (the node note). Effects: longer working and trading hours, less street crime and accidents, a coal and capital demand for the generating plant (recalled). |
| Mechanism to act through | Demand for coal: `warmth_and_light` in `data/world/needs.json` is satisfied by fuels; the model says "Lighting is not modelled" (`sim/world/climate_needs.py`), so an electric supply does not replace candle or oil demand. Generating demand: the power ladder (`electricity_gate`, `sim/engine/economy_electricity.py`) already makes electrical nodes draw generated electricity, so a lighting works that sets `electricity_gate` creates coal or hydro demand with no new code. Crime and accident reduction: `hazard_counters` (`staff_loss`) for founder staff losses, plus `protection` and `standing`. Working hours: no field; labour capacity reads headcount and hours as a fixed trade day. |
| Data-only or engine | A benefaction `ben_city_electric_lighting` is data-only: `pre` `civ_street_lighting`, `hom_electric_lighting`; `electricity_gate`, `hazard_counters` `staff_loss` small, `protection`, `standing`. Real effects on working hours and consumption of light need engine work: a lighting need in `needs.json` and a day-length field in labour. Note that `civ_street_lighting` has no upkeep, so it is not a venture; the benefaction should carry the upkeep. |
| Fields set | `upkeep_full`, `capability` (`population`), `electricity_gate`, `hazard_counters`, `protection`, `standing` |

## 7. Disaster relief and reconstruction

| Item | Content |
|---|---|
| Historical effect | After the Lisbon earthquake of 1755, Pombal had the army put out fires and clear debris, fixed food and building-material prices, erected tents for shelter and feeding, and replanned the centre with prefabricated standard parts; the centre was largely rebuilt within thirty years and no one died of hunger (read, summaries). The London fire of 1666 destroyed most of the walled city but few lives; rebuilding rules required brick and stone, and fire insurance followed (the `england_1300.json` hazard note, read). Effects: lower deaths in the year after, faster rebuilding of capital stock, better future fire safety. |
| Mechanism to act through | The founder-side effect exists: `hazard_counters` `staff_loss` and `output_factor` (hospital, grain dole, underwriting). Nation-side effect: the civilisation's hazards carry sack, staff loss and output factors (`data/civilizations/*.json`, `_resolve_hazard_condition` in `sim/engine/society_hazards.py`), but the nation's population is `sim/world/demography.py`, which responds to food and `disease_burden`, not to relief. A grain dole of the nation's size could act through nutrition (`nutrition_ratio` in `Population.step`), but no node feeds that. |
| Data-only or engine | Founder-side relief after a disaster: data-only (another `hazard_counters` node, for example fire and flood brigades countering `output_factor`). A one-off relief outlay after a named disaster, and recovery of the nation's population and stock: needs an effect type (a reactive purchase tied to a hazard event, like the sum in the debt row) and a link from relief to demography (food supplied to the population raising `nutrition_ratio`). Neither exists. |
| Fields set | Now: `hazard_counters`, `protection`, `standing`. Later: transfer or food-supply effect on demography |

## 8. Endowments with chosen beneficiaries

| Item | Content |
|---|---|
| Historical effect | Charitable trusts and endowed schools and colleges directed money to named classes of beneficiaries (poor scholars, a town, a trade), often as land held in trust, as the existing `endowment_land` prerequisite reflects (recalled). Effects: the endowed body persists beyond the donor, subject to the trustees' fidelity and to land value. |
| Mechanism to act through | Each benefaction already has one fixed beneficiary by design. A choice among beneficiaries is a choice among nodes, which is data (one node per beneficiary type, for example a school for the poor, a school for craftsmen's sons). The per-unit effect depends on `capability.scalable`. A beneficiary that is a trade or a region requires the labour pool to know the trade of the schooled: `schooling_flow` is a single nation-wide number and `labour_productivity` takes a `trade`. |
| Data-only or engine | Beneficiary by node: data-only, using `labour_productivity` (`trade`, `bonus`) and `staff_capacity` by trade for a craft school. Beneficiary by region or social group: engine (schooling is not split by place or group; `literacy_general` and `literacy_elite` are the only two). |
| Fields set | `labour_productivity`, `staff_capacity`, `schooling_flow` |

## 9. Political settlements

| Item | Content |
|---|---|
| Historical effect | Buying off or settling a faction (guild, nobles, a regional elite) with money or concessions so it stops pressing the state or the founder: tax farms, offices, pensions, compensation to guilds hurt by a new technique (recalled; see the compensation of machine-breakers' trades and of Dutch regents in many city histories, not checked). Effect: lower pull of the group on the state and lower prohibition risk. |
| Mechanism to act through | Interest groups are actors (`sim/agents/group.py`); a group's `strength`, `claim` and `demands` come from lost income against the state's capacity (`state_response`). The state makes good a `claim`, the rest being raised from taxpayers including the founder (`group_levy_reasons` in `sim/engine/interest_groups.py`). A direct payment of a group's claim would reduce the levy and the group's pull. Prohibition is checked by `group_prohibition_of`, and protection above the opposition line lets a founder build despite a ban. |
| Data-only or engine | Engine. There is no way to pay a group: a transfer from household to a group record (`ledger.transfer` accepts actors; a group's `money` may not be tracked) and a rule that a paid group lowers `lost_income` or `grievance`. As a data-only partial: a `protection` or `patron_protection` benefaction already buys state favour. |
| Fields set | New: a payment command or `transfer_to_group`; existing `protection` |

## 10. School and clinic rollouts with coverage targets

| Item | Content |
|---|---|
| Historical effect | Public schooling and clinic networks were extended by programme (a school in every parish, a clinic in every district) with coverage targets such as enrolment and vaccination rates (recalled). Effects: literacy and survival rise with coverage and level off near a ceiling. |
| Mechanism to act through | Schooling: the free school and library already scale by units with diminishing returns (`per_sqrt_unit`), bounded by `capability.scalable` `literacy` (`literate_capacity`), and literacy approaches a ceiling logistically (`_advance_literacy`); this is the same shape as coverage. Clinics: `disease_burden` is the weighted share of listed technologies held; clinic nodes could be listed with a weight in `data/civilizations/_TECH_EFFECTS.json`. |
| Data-only or engine | A rollout as more units of the existing benefactions: data-only today. A target with a count that the player sets and that is shown against coverage: engine, in the UI and in the unit cap (a `coverage` figure per benefaction, population served per unit). Clinics: data-only for a `ben_district_clinics` node with `disease_burden`, but adding a weight changes the denominator for all runs (re-record `python3 -m sim.tests.fingerprint` and check `data/civilizations/_TECH_EFFECTS.json` first); also `md2_child_clinic` and `md2_maternal_clinic` have no upkeep and so are not operable. |
| Fields set | `schooling_flow`, `disease_burden`, `hazard_counters`, `standing` |

## Summary table

| Item | Verdict | Why |
|---|---|---|
| Museums | Data-only | `corpus`, `schooling_flow`, `standing` |
| Newspapers | Data-only (effects partial) | `schooling_flow`, `reach`, `alarm_factor`; political legitimacy missing |
| Gambling houses | Mostly data (gating, risk); state levy is engine | Already a venture; needs `pre`, risk fields |
| Electric city lighting | Data-only for power demand and safety; engine for hours and light demand | `electricity_gate`, `hazard_counters` |
| Disaster relief (founder side) | Data-only | `hazard_counters` |
| Disaster relief (national) | Engine | No link to demography |
| Paying state debt | New effect type (one-off transfer) | `pay_state` exists, no command or node field |
| Colonies (trading post) | Data-only | `reach`, `precaution` |
| Colonies (settlement) | Engine state missing | Territory, settled population |
| Endowments by trade | Data-only | `labour_productivity`, `staff_capacity` |
| Endowments by place or group | Engine | Schooling not split |
| Political settlements | Engine | No payment to a group |
| School and clinic rollouts | Data-only as more units; targets are engine | `per_sqrt_unit` already models coverage |

## Ready now (data only, existing effect fields)

1. `ben_public_museum` (corpus hedge, small schooling flow, standing).
2. `ben_newspaper_endowment` or a free press (schooling flow, reach, alarm and eminence factors with a hint).
3. `ben_city_electric_lighting` (electricity gate, small staff-loss counter, protection, standing), with upkeep on the benefaction because `civ_street_lighting` has none.
4. `ben_fire_and_flood_brigades` (disaster relief at household level, `hazard_counters`).
5. `ben_craft_school` and other beneficiary-specific schools (`labour_productivity` by trade, `staff_capacity`).
6. `ben_district_clinics` (`disease_burden`), after checking the weight table and re-recording the fingerprint.
7. Gambling house and lottery gating (`pre`, `alarm_factor`, `protection`) as an edit of the existing ventures.
8. A trading-post wrapper for `exp_colony_administration` (`reach`, `hazard_counters`).

## Needs a new effect type

* One-off transfers: a `transfer_to_state` field (a `grants`-like completion hook) or a command over `pay_state`, for paying debt, for disaster relief outlays and for political settlements (the last also needs a payee that is a group).
* A per-concern state levy for licensed gambling and lotteries.
* A coverage target and reporting for rollouts.

## Needs engine state that does not exist

* Colonies: owned territory, a settled population with its own demography, a link route, frontier risk. Related to the "place and size" gap in the action and construction audit.
* National disaster recovery: a relief to nutrition and a stock-rebuild link in demography.
* Newspaper political effect: a state legitimacy field and public opinion.
* Electric light: a lighting need in `data/world/needs.json` and a working-day length in labour.
* Beneficiary by place or social group: schooling split beyond general and elite literacy.

## Open questions for the owner

* Should a payment to the state be allowed to build a surplus (a reserve), or only reduce debt?
* Is a debt payoff meant to give favour (`patron_protection`) as well as a lower rate, or should the lower rate be the only effect, as the historical mechanism says?

## Sources

* Newspapers: Jeremy Black, the English press in the long eighteenth century (via Gale essay), History Today on newspapers and politics, UCLA history of the book chapter (search results, read as snippets).
* Street lighting: College of Policing crime reduction toolkit, Significance magazine on ambient light (snippets).
* Sinking fund: Wikipedia article on the sinking fund, a full-text econbiz volume on the Industrial Revolution (snippets).
* Lotteries: Wikipedia on lotteries and the Million Lottery, Queen's University thesis on the English state lottery-loan, and the Historical Journal article on abolition (snippets).
* Colonies: Wikipedia, History of the Cape Colony before 1806; Historic Jamestowne, the starving time (snippets).
* Museums: Pitt Rivers Museum history pages and the Ashmolean (snippets).
* Disaster relief: ALNAP on the reconstruction of Lisbon, The Conversation on Lisbon's recovery (snippets).
