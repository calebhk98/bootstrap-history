# 03 - Social, Political and Legal Model

> There is a second file with this name: [`rome/knowledge/03_SOCIAL_POLITICS.md`](knowledge/03_SOCIAL_POLITICS.md).
> That one is the HOW-TO, one entry per social node, and is what the tech tree links to.
> This one describes the MODEL: how approval, suspicion and protection are computed.

*The technical tree is the easy half. This file is the half that gets you
killed, and it is the half the simulator models most aggressively.*

---

## 1. The three currencies you actually spend

Money is the least scarce of your resources. You have four ledgers:

| Ledger | Symbol in sim | Regenerates? | What exhausts it |
|---|---|---|---|
| Denarii | `capital` | Yes, from products | Everything |
| **Your own hours** | `personal_hours` | ~2,400/yr, and only while you live | Doing anything yourself |
| **Trained minds** | `scholars`, `artisans` | Slowly, via teaching | Death, plague, poaching, war |
| **Standing** | `patronage`, `imperial_favour`, `popular_favour` | Slowly | Spending it on permissions |
| **Suspicion** | `suspicion` | Decays slowly | Every impressive, inexplicable thing you do |

The binding constraint over a 40-year career is **your own hours**, and the
binding constraint over a 200-year programme is **trained minds**. Denarii are
a means of converting the first into the second. Every plan that fails, fails
because it spent the founder's hours on things a hired man could have done.

## 2. Identity and cover

**Recommended cover:** a Greek-speaking natural philosopher and physician of
Alexandria, of middling free birth, returning west with books and specimens.

Why this specific cover:
- Greek learning is prestigious in Rome; a Greek accent in Latin is expected of
  a philosopher and explains every verbal oddity you will produce.
- Alexandria explains any strange apparatus, chemical knowledge or foreign
  material as "from the Mouseion" or "from the Indian trade".
- A physician has a licence to be interested in bodies, plants, minerals and
  poisons, is exempt from certain civic burdens (immunities granted to doctors
  and teachers by Vespasian and confirmed later), and gets access to the rich.
- It is *not* a magician, not a prophet, not a priest of a new god. Those are
  the three identities that attract prosecution.

**Never claim:** foreknowledge of the future, divine revelation, or a new
religion. Any of the three converts you from an eccentric into a defendant.

**The "recovery" frame.** Present every innovation as the restoration of a lost
art, from Egyptian temple archives, Chaldean records, or the burned scrolls of
the Library. Romans reward antiquarianism and punish novelty. This costs you
nothing and buys you an enormous amount.

## 3. The patronage ladder

Rome is not a market for ideas. It is a network of personal obligation. You
must climb it in this order and you cannot skip a rung.

1. **A local patron** in a wealthy provincial town (Puteoli, Ostia, Capua,
   Alexandria, Ephesus). Cost: a spectacular but harmless gift. Reading lenses
   for an ageing magistrate are worth more than any argument.
2. **A senatorial or equestrian household.** Cure someone important, or make
   their estate visibly more profitable. Pliny the Younger's circle is exactly
   the type: rich, literate, publicly generous, obsessed with reputation.
3. **A provincial governor or the Prefect of Egypt.** Now you can get mineral
   rights, labour drafts and protection.
4. **The imperial household**, ideally via the *a rationibus* (finance) or the
   Praetorian Prefect rather than the emperor directly. Trajan's court is
   unusually receptive to engineers; Apollodorus of Damascus is the model.

**Costs of patronage** (simulator values, all **[C]** estimates):
| Rung | Entry gift | Annual maintenance | What it unlocks |
|---|---|---|---|
| Town patron | 500-2,000 den | 200 den | Workshop premises, legal cover, local labour |
| Senatorial household | 5,000-20,000 den or one great service | 1,000 den | Capital, land, introductions |
| Governor | a public benefaction, 20,000-50,000 den | 2,000 den | Mining concessions, corvée labour, immunity |
| Imperial | a militarily decisive demonstration | political risk | Everything, and a target on your back |

## 4. What the State wants, and what it will suppress

**The State will fund, protect and demand (high `gov_interest`):**
- Anything that moves information faster: optical semaphore, then telegraph.
  An empire's fundamental problem is that a message from Rome to the Rhine takes
  weeks. Solve that and you can name your price. **This is your single best
  political lever.**
- Military metallurgy: better steel, cheaper mass-produced arms and armour.
- Siege and artillery improvements; later, gunpowder.
- Observation balloons, signal rockets.
- Water supply, harbour works, drainage, mining output, road and bridge
  engineering. Trajan personally funds all of these.
- Army medicine. The legions already have *valetudinaria*; give them antisepsis,
  wound irrigation, and variolation and you will be a hero to the officer class.
- Grain supply, storage and preservation. The *annona* is the regime's single
  greatest anxiety.

**The State and the elite will resist (negative `gov_interest`, high `suspicion`):**
- Machinery that visibly displaces free urban labour. See the Vespasian
  precedent. Mitigation: site it in the provinces, frame it as enabling a new
  thing, employ freedmen conspicuously.
- Anything that could arm a rebel or a rival: distributed gunpowder is the
  clearest case. Gunpowder is the highest-variance decision in this entire
  document. It buys imperial favour instantly and it makes every provincial
  usurper more dangerous for the next two centuries, including during the
  Third Century Crisis, which is exactly when you need the Empire to hold
  together. **My recommendation: develop nitric acid, withhold corned powder
  from general knowledge, and release it only if you need to buy survival.**
- Cheap accurate literacy tools that break elite information control: printing
  is politically ambiguous. Frame it as multiplying the classics, not as
  publishing.
- Anything touching the mints, the grain dole, or divination.

**Capital-risk activities (do not do these):**
- Astrology, prophecy, or any statement about the emperor's death or successor.
- *Veneficium*: compounding poisons. Your chemistry looks like this. Keep the
  laboratory inside a household, admit witnesses, and never work alone at night.
- Founding a cult, or a *collegium* the State has not licensed. Unlicensed
  associations are illegal (see Trajan's own reply to Pliny, *Ep.* 10.34, where
  he refuses even a fire brigade at Nicomedia for fear it becomes a faction).
  **Register your school as a licensed collegium of physicians or teachers.**


## 4a. The approval gate, as the simulator actually enforces it

Section 4 above is prose. This is the mechanic, and it is in the data: every
node in `data/tech_tree.json` carries a `gov` field from -3 to +3.

**A node with `gov` below zero cannot be built by money alone.**

| Rule | Effect |
|---|---|
| `gov < 0` | Costs 25% more per point: bribes, delay, relocating to a province, paying a compliant Roman citizen to front the enterprise |
| `gov < 0` | Adds 3 extra suspicion per point |
| `gov < 0` | **Cannot be attempted at all without a local patron** |
| `gov <= -2` | **Cannot be attempted at all without senatorial patronage** |

The nodes currently marked as opposed, and why:

| Node | `gov` | Why the State or the elite resists it |
|---|---|---|
| `academy_network` | **-2** | A large private association operating across several provinces is precisely what Roman government fears: a *factio*. Trajan refuses Pliny even a licensed fire brigade at Nicomedia for this reason (*Ep.* 10.34). Site the three houses under three different patrons so it does not look like one organisation. |
| `interchangeable_parts` | -1 | Visibly replaces free urban artisans with unskilled hands and gauges. This is the Vespasian precedent exactly (*Vesp.* 18). Put it in the provinces, staff it with freedmen, and sell it as arming the legions, never as saving wages. |
| `printing_press` | -1 | Cheap accurate copying breaks elite control of what is known and by whom. Print Homer, Virgil and the Twelve Tables first, visibly. |
| `corpus_dispersed` | -1 | The same objection, multiplied. Hundreds of copies of a technical corpus in private hands is what an anxious regime dislikes most. Give the first copies to the emperor's own foundations. |
| `scientific_method` | -1 | Contradicting Aristotle and Galen in public is a social act before it is an intellectual one, and their defenders hold the chairs and the guild. |
| `newtonian_mechanics` | -1 | Publicly overturns Aristotle on motion. Win it with predictions nobody can argue with, not with argument. |

Note what this list is: **the two nodes that the ablation study says are worth 40
and 47 years, `printing_press` and `corpus_dispersed`, are both politically
opposed.** The most valuable things you can do are among the things you will have
the most trouble being allowed to do. That is not a coincidence and it is the
reason the patronage ladder in section 3 comes before everything else.

Conversely, the highest `gov` scores (+3) sit on the optical and electric
telegraph, gunpowder, bulk steel, high pressure steam, the railway, crop
rotation, plague preparedness and the hot air balloon. Those are the things you
trade for the permission to do everything else.

## 5. The suspicion model

`suspicion` accrues when you do something that a Roman cannot explain by any
known art. It decays at roughly 10% per year if you behave normally.

Approximate deltas (**[C]**, tuned in the simulator):
| Act | Δ suspicion |
|---|---|
| A visibly better product with a plausible craft story (lens, mirror, soap) | +1 |
| Curing something reliably that others cannot | +4 |
| Fire, smoke, stench and sealed vessels in a private house | +6 |
| A demonstration that produces light, motion or sound with no visible cause | +12 |
| An explosion | +25 |
| Being right about a future event, publicly | +40 |

Mitigations: a powerful patron (multiplies incoming suspicion by 0.5), priestly
or medical office (0.7), conspicuous piety and public benefaction (-5/yr),
locating the dangerous work on a rural estate (0.6), and having a Roman citizen
of standing publicly own the enterprise (0.5).

At `suspicion > 60` you face denunciation: property seizure, exile, or death,
and the loss of everything not already copied and dispersed. **The simulator
treats this as a hard stop.** It is the most common way a run ends.

## 6. Citizenship and legal position

- Get **Roman citizenship** early. Routes: grant by the emperor or a governor
  for service (fastest for you), or, much slower, via military service or
  manumission. Citizenship gives you *provocatio*, the right of appeal, which
  is literally the difference between being executed by a governor and being
  sent to Rome. Cost: one great public service. Buy it with a bridge, a water
  supply, or a cure.
- Own nothing in your own name that can be confiscated. Use freedmen agents and
  a *societas*. Roman law has no corporation, but partnerships, *peculium* held
  by slaves and freedmen, and trusts via *fideicommissum* get you most of the way.
- **Wills are your succession mechanism.** Roman testamentary law is
  sophisticated and reliable, and an endowed foundation (*fundatio*, like
  Pliny's *alimenta* schemes or Trajan's own) is a real and legally durable
  vehicle. This is how your institute survives you. Endow it with land, not
  coin, because coin will be debased to nothing by 270 AD and land will not.

## 7. Slavery: the honest strategic problem

Roman labour is cheap because much of it is coerced. Three consequences:
1. **Labour-saving devices have a weak business case.** Your machines must
   compete against a man who costs 150 denarii once. Site your advantage in
   things slaves *cannot* do at any headcount: precision, chemistry, optics.
2. **The moral problem is not optional.** You will be offered slaves and you
   will need workers. The defensible strategy, and also the *effective* one, is
   to buy skilled slaves and manumit them into a paid, literate, loyal technical
   staff. Freedmen (*liberti*) were the engine of Roman commerce, retained
   obligation to their patron, and could hold property and run businesses. A
   manumitted, paid, trained artisan is worth several coerced ones, and Roman
   society is entirely comfortable with this arrangement.
3. The simulator models `freedman_loyalty` and gives manumitted staff a higher
   retention and knowledge-transmission rate than either slaves or hired hands.

## 8. Survival of knowledge: the real endgame

You will not see a transistor. Nobody alive when you arrive will. The programme
is a 150-250 year relay, and the Third Century Crisis sits in the middle of it.
Therefore:

1. **Write everything down, in Greek and Latin, in plain language, with
   numbers.** Not allegory. The alchemists' habit of deliberate obscurity
   destroyed centuries of work.
2. **Print it and disperse it.** Paper plus a screw press plus movable type is
   a low-tech, cheap technology that you can have inside ten years. Then push
   hundreds of copies of the core corpus into every library, temple archive and
   private collection from Britain to India. Redundancy defeats catastrophe.
   *This is the highest-value item in the entire tech tree and it is nearly
   free.* The Library of Alexandria's real lesson is not that books burn; it is
   that single copies burn.
3. **Endow institutions in more than one place, in more than one climate.**
   Alexandria, a western site (Massilia or Puteoli), and an eastern site
   (Ephesus or Antioch). Egypt's dryness preserves papyrus; the West preserves
   nothing.
4. **Teach method, not results.** A generation that has memorised your answers
   dies with them. A generation that can measure, calculate and experiment
   regenerates them.
5. **Mitigate the plagues.** Variolation, quarantine, water boiling, handwashing
   and basic sanitation are almost free and are the difference between your
   institute surviving 165 AD and not.
