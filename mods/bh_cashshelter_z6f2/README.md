# Cash Shelter (bh_cashshelter_z6f2)

Ways to lodge coin with someone else, elsewhere, so a disaster that takes the founder's purse cannot take it
(`Complaints/closed/165-disasters-take-cash.md`).

## What the engine takes today

Every hazard takes from the acting household's own purse (`household.capital`), by the engine's own arithmetic:

- fire (`FIRE_CAPITAL_LOSS`), plague (`PLAGUE_CASH_LOSS_SHARE` times the staff share killed) and debasement
  (`REAL_EROSION_CASH_LOSS_SHARE` times the erosion) take a share of the purse and nothing else;
- a sack and banditry take theft shares by kind of holding (`sim/engine/theft_exposure.py`): most of the purse is
  coin and is mostly guarded, so they take far more of the portable goods than of the purse;
- a treasury or eminence confiscation takes a share of the purse less what is concealed.

None of them reaches another actor's purse. The mod therefore needs no engine change: money moved through
`ledger.transfer` to another actor is simply not in the purse the hazards read.

## How a player turns it on

1. `python3 sim/simulator.py mod-allow bh_cashshelter_z6f2` (reads `hooks.py`; the mod ships Python).
2. In any game, the commands exist under the mod's namespace. Nothing happens until you use one; no civilisation,
   policy or shipped number changes.

Commands (typed, or JSON with a `text` field such as `{"cmd":"bh_cashshelter_z6f2:deposit","text":"strongroom 5000"}`):

- `bh_cashshelter_z6f2:exposure` (read): what each hazard would take from the purse now (cash and goods), what the
  state could count, and each holder: your claim, the share of it the holder could pay today, the fee a year.
- `...:deposit <holder> <amount|all>`, `...:withdraw <holder> <amount|all>`.
- `...:letter <issuer> <honourer> <amount|all>`: a letter of credit; the coin goes holder to holder, never through
  your purse.

Holders (`holder_types.json`): `strongroom` (a temple elsewhere) and `merchant_house` (a trading partner).

## What it models

- A holder is an ordinary actor with its own purse (created on the first deposit, saved with the game). The engine
  already charges every actor's coin the guard cost (`charge_actors_for_keeping_coin`) and theft
  (`charge_actors_for_theft`), so the holder's purse shrinks by its own state, not by a number in this mod.
- A deposit is a claim. The custody fee is taken from the claim each year: the engine's guard cost on that coin
  plus the engine's expected theft on it, times one plus the holder's markup. Carrying the coin out and back costs porters' hours priced at the unskilled
  hour, paid to the guards' edge.
- Counterparty risk: a holder has a yearly chance of being looted. If its purse is below what it owes, every claim is
  paid in the same share and the rest is lost.
- Fees accrue lazily: they are settled for all elapsed years at the next deposit, withdrawal or letter, so they
  cannot be avoided by not looking.

## Labelled heuristics (all in `holder_types.json`, each with its retirement)

Carriage hours per tonne, custody markup, yearly failure chance and loss share per holder type, and the letter of
credit's fee share. Each names what should replace it (a holder with a tile and route freight, a holder that prices
its own loss record, regional hazards that carry a place).

## Known limits

- The costs are small. The engine's coin guard cost is a tiny share of the coin a year (`exposure` prints the
  fee a year for your claim), so fees and carriage are slight beside the holder's failure chance. The real price of sheltering is counterparty risk and
  money that is not in the purse when you want to spend it.
- The state's confiscation, and the treasury notice, count only the purse. Nothing models the state finding a
  deposit, so lodging coin also hides it from confiscation; that is stronger than the real world and is the one
  place the shelter may be too generous. The mod registers its claims with `register_wealth_claims` when the engine
  has it; see `Complaints/566-confiscation-ignores-claims-on-other-actors.md` (proof of concept on branch
  `engine-confiscation-counts-claims`).
- Debasement lowers the worth of all coin (`money_real`); a holder's coin is not spared.
- The mod does not shelter goods, land or the people a plague and a sack take.
- Endowments are not built: nothing in the engine would let an irrevocable gift differ from a deposit.
- Dated hazards are not listed by `exposure` (the `risk` screen lists them and respects fog).
- A saved game that holds a holder cannot be loaded unless the mod is installed and allowed.
