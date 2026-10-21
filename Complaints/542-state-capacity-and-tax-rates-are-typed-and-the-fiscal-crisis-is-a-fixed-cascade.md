# State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade

**Status:** open - split into 620, 621, 622, 623, 624, 625, 626 (620 is closed for collection only, in Complaints/; 656 follows from 626)

Reference (an outside design note, not code-aware): the tax a state can actually collect should depend
on its administrators and its reach (Egypt's single river corridor was easy to survey; a far
province is not). Han's light land tax rode on heavy poll tax, a month of corvée a year per adult
man, two years of conscription and the salt and iron monopolies. A state short of money borrowed
from citizens, contractors or temples (Rome in the Second Punic War repaid part in public land),
debased its coin, demanded goods in kind, or fell into arrears with its soldiers.

## What the code does

- **Rates and capacity are typed.** Each civilisation's `state_revenue` list declares form, base and
  rate (`data/civilizations/*.json`, assessed in `sim/agents/revenue.py`), and `state_capacity` is a
  typed number (`sim/agents/cast.py`, `records.py`). The bases are modelled quantities, which is
  right. Nothing derives capacity from officials, scribes, literacy or distance from the capital;
  `ADMINISTRATIVE_SPAN` (`sim/agents/tuning.py`) sizes the officials kept, not what they can collect.
- **Labour dues** exist (621, closed): a form on `labour_days` takes days from household time for works
  or conscripts (`sim/agents/revenue_labour.py`). Soldiers beyond them are a typed `standing_army` share paid at wage.
- **Taxes in kind exist for grain only** (`paid_in`, `sim/agents/government_stores.py`).
- **Borrowing** is from the general loanable pool once a technology allows it
  (`sim/agents/government.py`, `borrowing.py`), with its lenders named and a default on its record
  (623, closed). There is no repayment in land (538).
- **Debasement** cuts the metal in the coin (`sim/agents/government_coinage.py`), but domestic money
  prices fixed at load do not follow (Complaint 272, closed with that gap noted).
- **Crisis.** Short of money, `Government.advance` cuts every line by the same share, books arrears,
  shrinks the army, debases if it can, raises levies on visible taxpayers, and soldiers mutiny below a
  loyalty line (`sim/agents/group_servants.py`). These all happen in a fixed order, so no ruler chooses
  among them, and higher tax never drives peasants off the land (486, 538).
- **No tax farming** (538): collection is a wage line (`sim/agents/budget_works.py`).

## What it would take

- Collectible share derived from the officials and literate staff a state employs and the travel
  time from its seat to each tile (freight and routes exist), replacing typed `state_capacity` for
  collection.
- Corvée and conscription as labour levies in days per adult, drawn from household time, with
  commutation to cash as a state choice.
- Kind levies on any good; named state creditors (citizens, contractors, temples); repayment in land
  once land titles exist (538); default.
- Debasement reaching domestic prices through the money supply (272).
- The crisis responses as choices of the state actor, each with its consequences, so a player state
  and an AI state face the same menu (481, 482).
- Tax rates as a state choice once the consequences exist; the civilisation file keeps only the
  starting rates.

## Split

Children, in order of work:

- 620: A state's collectible share is a typed `state_capacity`, not derived from officials, literacy and distance
- 621: There is no corvée or conscription term: labour levies do not exist
- 622: Taxes in kind exist for grain only
- 623: The state borrows from the pool: no named creditors, no repayment in land and no default
- 624: Debasement cuts the metal in the coin but domestic money prices do not follow
- 625 (closed): The fiscal crisis is a fixed cascade, not choices of the state actor
- 626 (closed): Tax rates are typed in the civilisation file and are not a state choice
- 656: A higher tax rate has no consequence beyond revenue and a typed burden weight (follows from 626)
