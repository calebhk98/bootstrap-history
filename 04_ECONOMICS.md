# 04 - Economics: labour, materials and what it all costs

All figures computed from `data/tech_tree.json` and `data/prices.json` by
`sim/simulator.py costs`. Regenerate them after any edit; do not trust a number
copied into prose over the number in the data file.

**Wage basis.** A 10-hour day and about 250 working days a year, so 2,500
worker-hours per person-year. Unskilled 2-4 sestertii a day, skilled artisan
4-8, master 8-16. One denarius = 4 sestertii.

**Confidence.** Wages are [B]. Bulk commodity prices are [C]: my estimates,
anchored to silver through ratios implied by the Edict of Diocletian, which is
301 AD and denominated in a collapsed currency, so I use it for ratios only.
**Replace every [C] price with an observed one in your first month.**

**A caveat this section's own rule requires.** The tree has grown from 1,176
nodes to 2,833 since the table below was rolled up, and `simulator.py costs`
no longer has a by-domain grouping mode at all (today it prints only the N
most expensive nodes and a "best return on capital" list) - so the table
cannot currently be regenerated the way this file's own header promises.
Whole-tree totals that CAN be reproduced today, from `simulator.py validate`:
**total capital 21,446,337 den, total founder-hours 422,405** across all 2,833
nodes. Read the domain table below for its shape - where the money and the
hours go relative to each other - not for its absolute numbers, which predate
both the tree's growth and the goal moving from `point_contact_transistor` to
`junction_transistor`.

---

## 1. The whole programme, by domain

1,176 nodes rolled up, at a point in the project's history `simulator.py
costs` can no longer reproduce (see the caveat above).

| Domain | Nodes | Your hours | Total cost (den) | Revenue at maturity (den/yr) |
|---|---:|---:|---:|---:|
| miscellaneous (a long tail of 60+ small categories) | 140 | 20,040 | 401,131 | 32,320 |
| energy and power | 107 | 22,280 | 446,293 | 223,200 |
| optics and instruments | 88 | 17,750 | 157,868 | 49,180 |
| precision | 70 | 10,750 | 88,354 | 24,390 |
| materials | 70 | 2,910 | 154,000 | 0 |
| transport | 69 | 10,120 | 10,056,014 | 81,960 |
| household | 58 | 4,740 | 16,406 | 14,785 |
| textiles | 56 | 5,260 | 119,318 | 75,630 |
| ships and navigation | 55 | 7,300 | 127,616 | 10,400 |
| metallurgy and mining | 54 | 14,100 | 648,952 | 200,250 |
| aviation | 46 | 7,070 | 16,323 | 7,530 |
| chemicals | 45 | 12,770 | 557,133 | 193,400 |
| food and agriculture | 42 | 6,630 | 31,690 | 7,050 |
| media and information | 37 | 14,120 | 114,110 | 21,600 |
| communications | 34 | 3,750 | 159,806 | 53,450 |
| capabilities | 33 | 4,950 | 211,800 | 0 |
| medicine | 33 | 3,990 | 32,614 | 20,550 |
| knowledge and method | 28 | 11,930 | 38,686 | 3,900 |
| computing | 27 | 4,220 | 213,256 | 5,300 |
| institutions | 23 | 11,200 | 312,527 | 27,700 |
| electrical | 21 | 8,530 | 1,058,837 | 239,700 |
| civil engineering | 21 | 2,240 | 9,768 | 400 |
| semiconductors | 10 | 8,250 | 443,949 | 70,000 |
| ~~unobtainable~~ | ~~7~~ | ~~0~~ | ~~0~~ | ~~0~~ |
| military | 2 | 700 | 10,724 | 6,000 |
| **TOTAL** | **1176** | **215,600** | **15,427,174** | **1,368,695** |

*The "unobtainable" row is struck through because that tier no longer exists:
the seven materials it counted (rubber, gutta-percha, quinine, Chile
saltpetre and the rest) were moved to tier 4, each reachable through an
`exp_*` expedition node, once the project decided nothing in the material
layer should be flagged impossible outright. See `ROME_BOOTSTRAP.md`.*

---

## 1a. What the totals mean

| | |
|---|---|
| Total capital to build everything | **15.4 million denarii**, about 62 senatorial fortunes |
| Total founder-hours demanded | **215,600**, about **three whole working lifetimes** |
| Founder-hours available in one life | 72,000 |
| Total revenue at full maturity | 1.37 million denarii a year |

**One node, the railway, costs 10 million of the 15.4 million.** That is not an
error, it is the honest shape of the thing: a demonstration line of about 4 km
needs 400 tonnes of rail steel, and a network needs an order of magnitude more.
Heavy transport infrastructure dwarfs everything else in the tree, which is why
its calendar floor is a generation and why it cannot be done by an institute, only
by a state.

Against that, look at `household`: 58 technologies, 16,406 denarii for the whole
domain, and it contains the chimney, the water trap, the Argand lamp, hard soap
and the washing machine. **The domain with the most human benefit per denarius is
the cheapest one in the table.** If you only ever finish one branch, finish that
one.


## 2. What these tables actually say

**Read the table again and compare two rows.** `media and information` takes
14,120 of your own hours, among the very highest in the tree, for 114,110
denarii, which is under one percent of the total. `transport` takes 10,120 of
your hours for **10.06 million denarii**, two thirds of everything.

The same asymmetry runs through the whole table. `knowledge and method` is 28
nodes, 11,930 of your hours, and 38,686 denarii. `electrical` is 21 nodes, 8,530
of your hours, and 1.06 million denarii.

That asymmetry is the whole strategic geometry of this problem:

- **Money buys things. It does not buy understanding.** The expensive branches
  are expensive in denarii and cheap in founder-hours, because once specified
  they can be handed to a competent freedman and a large workforce.
- **The cheap branches are the ones only you can do.** Writing the corpus,
  teaching mathematics, establishing the method. Nobody in the Empire can do
  those for you, at any price, until you have made someone who can.
- Therefore: **spend money freely and hours miserably.** The failure mode of
  every simulated run that dies is a founder who spent his hours on apparatus.

## 3. The total is unaffordable, and that is the point

The full tree costs about **4.6 million denarii**, which is roughly 19 senatorial
fortunes, and **215,600 of your hours** against the 72,000 you will ever have.

Neither number is meant to be paid by you. They are paid by:

1. **Compounding revenue.** The programme's own products fund it. Note the
   revenue column totals about 806,900 denarii a year at full maturity, which
   pays back the entire capital cost in about 6 years, if you live long
   enough to get there, which you do not.
2. **The State.** Once the optical telegraph exists, imperial funding is worth
   more than every product you sell.
3. **Economic growth.** This is the term most bootstrap plans forget.
   Industrialisation pays for itself: each diffused technology raises output
   across the whole Empire, and a share comes back to you as demand, taxes and
   patronage. In the simulator, removing this term makes the industrial
   revolution mathematically unaffordable, which is false, and the reason it is
   false is that the revolution funds itself.

## 4. Transport dominates everything, so build on water

The single most important economic fact in the Empire, and the one most likely
to wreck a plan drawn on a map: **sea freight costs roughly one-fortieth to
one-sixtieth of land freight per tonne-kilometre.** Moving grain 500 km overland
roughly doubles its price.

Consequences, all of them binding:
- A blast furnace consumes about 180 tonnes of charcoal per campaign in this
  model. Charcoal is bulky and worth about 0.03 denarii a kilogramme. Hauling it
  40 km overland can cost more than the fuel.
- **Every facility goes on navigable water.** Ostia, Puteoli, the Rhône, the
  Rhine, the Guadalquivir, the Nile. A workshop sited for convenience rather
  than for water is a workshop that will strangle on its own supply chain.
- Ore, flux, fuel and finished metal should ideally never touch a road.

## 5. Charcoal is the real ceiling on iron, not ore

Pre-coke ironmaking is limited by forest, not by mines, and it deforests
regions. The charcoal node in the tree carries 200 *iugera* of dedicated
coppice land for exactly this reason. Coppice rotation is 15 to 20 years, so the
land must be acquired long before the furnace is lit. Coking coal breaks the
ceiling permanently and is the reason `coal_coke` sits where it does in the
recommended order.

## 6. Two honest warnings about these numbers

**The revenue figures are the weakest thing in this project.** They are
estimates of net profit from enterprises that do not exist in a market I have
reconstructed from secondary scholarship. The ablation study found that removing
the amalgam mirror business *improves* the outcome, which I think is an artefact
of exactly this weakness rather than a real result.

**Slavery is modelled far too thinly.** Roman labour is cheap partly because
much of it is coerced, which suppressed the business case for every
labour-saving device in this document. The model treats labour as a market with
a manumission option. That understates the problem, and the honest version of
the answer is in `03_SOCIAL_POLITICS.md` section 7: compete where headcount
cannot substitute, which is precision, chemistry and optics.

## 7. Bounties: buying other people's hours with money

The third way to get something built, alongside doing it yourself and hiring
labour by the hour, is to **post a public prize**.

> *Decem milia sestertium ei vitrario qui primus mihi attulerit sphaerulam
> vitream puram, milii grano parem.*
> Ten thousand sesterces to the first glassworker who brings me a clear sphere of
> glass the size of a millet grain.

This is a genuinely different economic instrument and it is the one that best
fits your actual constraint. Hiring labour by the hour still costs you the hours
of **specifying and supervising** the work. A prize costs you only the hours of
**writing the notice**. You are converting denarii, which you can regenerate,
into somebody else's attention, which you cannot.

**Terms modelled in the simulator** (`bounties` in a strategy file):

| | |
|---|---|
| Price | about **2.5x** the honest cost of the work |
| Your hours saved | **65%** |
| Supervision slots consumed | **none**, which is the real advantage |
| Side effect | +2 suspicion. A public prize makes you conspicuous. |

**Where a bounty works, and where it cannot.** The craft must already exist in
the Empire, and the artisan must be able to **recognise success without
understanding why it works**. A glassworker can tell a clear bead from a cloudy
one. A smith can tell whether a plate is flat by the marking. Neither needs your
theory. That is why the eligible set in the model is limited to tier 0 to 2
nodes in glass, metallurgy, precision, power, agriculture, instruments and
information.

You cannot post a bounty for zone refining. Nobody in the Empire would know what
to aim at, or how to tell if they had hit it. Past about tier 3, the only people
who can recognise success are people you trained, and at that point you are back
to paying wages.

**Measured effect**, 400 runs each: bounties move the median from 391 AD to
**385 AD** and lift the success rate from 78% to 80%. Real but modest. They help
most in the first thirty years, when your hours are the binding constraint and
the cash premium is affordable relative to what an unmade lens is costing you in
delay.
