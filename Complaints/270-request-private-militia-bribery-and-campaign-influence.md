# Request: raise a private militia, bribe a warlord or influence a campaign

**Status:** open

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md`, item 2 (active diplomacy and military command).

## What is wrong

Military events are a passive roll against the founder's protection. The player cannot raise armed men, pay an invading commander to go elsewhere, or support one side of a campaign. `sim/world/military_logistics.py` derives what an army consumes and how far it can march, but nothing in the engine decides or buys anything with it.

## Why it matters

A founder with great wealth and no way to turn it into force or influence has only one answer to invasion: spend on generic protection. Players and the review both read this as a missing lever, and other actors (states, later other players) will need the same mechanism.

## What it would take

Make force an ordinary purchase: men with food, equipment and pay, drawn through the labour and supply rules, usable by any actor. Bribery is a transfer to another actor that changes its decision, so it needs an actor with decisions (see 105 and 185). Do not script outcomes (`CLAUDE.md` 4.1, 4.3).
