# A treasury of coin weighs nothing and needs no vault

**Status:** open

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md`, item 5 (physical weight of bronze coinage).

## What is wrong

A fortune held as bronze cash coin is a large mass, yet holding it costs nothing in storage, guarding or transport. The review's arithmetic: a late-game treasury of tens of millions of cash is many tonnes of bronze. Coin mass is physical in the money model (`sim/engine/money_units.py`, 144) and `sim/world/transport.py` prices moving mass, but no screen or rule charges for keeping or moving money.

## Why it matters

A weightless treasury is a hardcoded outcome (`CLAUDE.md` 4.1) and it hides why people held wealth as land, goods or credit instead. It also makes confiscation and banditry (165) cheaper to shrug off.

## What it would take

Compute the mass of the coin held from the coin metal and the amount, charge storage and guarding as an actor cost, and let large transfers pay freight. Measure with a late-game save: held money converted to tonnes of coin metal. Which coin metal a civilisation uses is data.
