# 00 - Arrival Briefing: your first thousand days

You are a competent modern adult. You speak Latin and Koine Greek. You carry
roughly three kilogrammes of unminted gold (about 10,300 denarii, comfortable
but well short of the equestrian census of 100,000) and this guide. It is
roughly 100 AD, Trajan is emperor, and you are going to die of something
ordinary in about thirty years.

Read this file before you do anything clever.

---

## The four things that are actually true

**1. You will not see a transistor.** Nobody alive will. The simulator in
`sim/` puts the median at **385 AD**, about 285 years out, across 600 runs of
the best strategy I could write. Your job is not to build a transistor.
Your job is to build the *institution and the corpus* that builds it, and to get
them through two pandemics and a fifty-year civil war that you know are coming
and nobody else does.

**2. Your own hours are the scarce resource, not money.** You have about 2,400
useful hours a year and about thirty years, so roughly 72,000 hours, total,
forever. The full tree in `data/tech_tree.json` demands **215,600**, about three whole
working lifetimes. You are short by a factor of three before you start, and no
amount of money closes that gap. Only other people do. Every hour you spend doing something a hired man could do is
an hour stolen from the only things nobody else can do: **teaching, writing, and
deciding what to build next.**

**3. The highest-value things you can do are almost free.** The ablation study
(`sim/simulator.py sensitivity`) says the four biggest single items in the tree
are: write the corpus, print it, disperse it, and make paper. Not the blast
furnace. Not the steam engine. Writing things down and copying them.

**4. The most dangerous thing about you is that you are interesting.** Rome
executes magicians. Your chemistry looks exactly like magic. Read
`03_SOCIAL_POLITICS.md` before you light anything on fire.

---

## Days 1 to 180: do nothing impressive

The strongest temptation is to arrive and start inventing. Resist it. Every
bootstrap plan that fails, fails in the first year, because the planner acted
confidently on assumptions that were wrong.

- **Convert some gold, slowly, in more than one city.** A stranger appearing with
  an equestrian fortune in unminted bullion attracts the *fiscus* and the local
  bandits in roughly that order. Sell in small lots to *argentarii* in different
  towns. Expect to lose 10-20% to spreads and to being obviously foreign.
- **Learn what things actually cost.** Every price in `data/prices.json` is my
  estimate from published scholarship, and the ones marked [C] are guesses.
  Replace them with observed prices in your first month. This single act will
  improve every plan in this guide.
- **Learn the law.** Who has *imperium* here. What the local *collegia* are
  licensed for. Whether you can own land as a peregrine (you cannot, in most
  cases, without *ius commercii*). What gets people prosecuted in this province.
- **Find out who is ill and rich.** This is your entry to patronage.
- **Say nothing about the future. Ever.** Not to a friend, not to a lover, not
  drunk. Predicting the emperor's death is treason and predicting anything else
  is how you become someone who predicts the emperor's death.

## Days 180 to 1,000: the four things that must be started early

Do these in parallel, because three of them are limited by the calendar and not
by you.

| Start by | Why it cannot wait |
|---|---|
| **Nitre beds** | 12 to 24 months of biology. No money accelerates it. Everything in nitrogen chemistry, and therefore nitric acid, waits behind it. Roman *nitrum* is sodium carbonate; there is no saltpetre in the Roman economy to buy. |
| **Lens grinding** | Your first revenue AND the gift that buys your first patron. Reading spectacles for a literate elite that goes presbyopic at forty and has no remedy at all. |
| **A patron** | Everything legal, everything cheap, and roughly a 40% reduction in the chance of being denounced. |
| **The standards** | Define your units and make the master artefacts before you write a single recipe down. Every number you record without them is worthless to whoever reads it in 250 AD. |

And one thing to start writing on day one and never stop: **the corpus**.
6,000 of your hours over ten years. It is the largest single call on your life
and it is the one the model says you must not cut.

## The single hardest deadline you have

The simulator sweeps the founder's lifespan (`sweep lifespan`) and finds a
cliff, not a slope:

| You survive | You succeed |
|---|---|
| 10 years | **0%** |
| 15 years | **0%** |
| 20 years | 48% |
| 28 years (the median draw) | 86% |
| 45 years | 88% |

Living a very long time buys you almost nothing that living an ordinary long
time did not. **Everything hinges on whether the school exists and the corpus is
started by roughly year 20.** After that your personal survival is close to
irrelevant to the outcome, which is a strange and clarifying thing to know about
your own life.

It also means: use your medical knowledge on yourself and your first students,
early. Boil your water. Do not let a cut go septic. The difference between dying
15 years in and 28 years in is the difference between certain failure and 86%.

## The one-page decision rule

When you are deciding what to do next, in order:

1. Does it teach someone? Do it.
2. Does it get written down and copied? Do it.
3. Does it have a calendar floor you cannot buy down (growing, curing, maturing,
   a generation of diffusion)? Start it now, even if you cannot use it yet.
4. Does it pay for itself within five years? Do it, and hand it to a freedman.
5. Does it only make you personally more impressive? **Do not do it.**

## The specific ways runs end badly, in order of frequency

From 600 simulated runs of the recommended strategy:

| Failure | Share | The fix |
|---|---|---|
| The founder died without training successors and the school dispersed | 16% | Found the school in your first fifteen years. It is the pivot of the whole game. |
| Denounced as a magician, property seized | 5% | Patron, licensed collegium, citizenship, and never work alone at night. |
| Ran out of time | ~1% | Usually a staffing ceiling, meaning the revenue was never built. |

Under the greedy "rush straight at the goal" strategy, **zero runs in 600
succeeded**. It gets stuck on `atomic_theory`, of all things,
because it never trained a second natural philosopher and that node needs two.

Under a bare topological ordering of the *technical* prerequisites, five runs
in 600 succeeded, because the technical graph does not require you to become a
citizen, find a patron, or teach anybody, and you cannot do a single step of it
without all three.

That is the whole lesson of this project in one sentence: **the bottleneck is
never the machine, it is the number of people who understand it.**
