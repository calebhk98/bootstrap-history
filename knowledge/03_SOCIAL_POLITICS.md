# Module 03: Standing, Patrons, and the Right to Exist

> There is a second file with this name: [`rome/03_SOCIAL_POLITICS.md`](../03_SOCIAL_POLITICS.md).
> That one describes the MODEL, meaning how the simulator computes approval, suspicion and
> protection. This one is the HOW-TO, meaning what you actually do about it, entry by entry,
> and it is what the tech tree's ten social nodes link to.

## Why this module is first among equals

The simulator has been run many thousands of times. The result that survives every parameter sweep, every ablation and every change of civilization is this:

**Success is zero per cent without the nodes in this module.** Not slower. Zero.

That is worth sitting with, because nothing in physics requires a patron. Iron does not smelt faster because a senator likes you. A lens does not focus better because you hold citizenship. The technical dependency graph and the real dependency graph are different graphs, and the second one is the one that kills you.

The reason is simple. Every technology in this guide has to be *built*, by *people*, in a *place*, over *years*, and each of those three things can be taken from you by someone who does not need a reason. In 100 AD you are, until proven otherwise, a foreigner of unknown origin with unexplained knowledge and unexplained money. The Roman state has a word for people like that and it is not "inventor".

So this module is about buying the right to keep working. Read it before you read anything about furnaces.

---

## The three things that can end you (there is a fourth, further down)

Understand the actual threat model before you spend a denarius defending against the wrong one.

**1. The magistrate.** A provincial governor holds *imperium* and, over a non-citizen, effectively unlimited coercive power. He does not need evidence, a charge that would satisfy us, or a trial. Pliny the Younger, governing Bithynia around 111 AD, writes to Trajan asking what to do about Christians and describes his procedure: he asks them three times, and if they persist he orders them executed, because "whatever it was they were admitting to, their stubbornness and unbending obstinacy certainly deserved to be punished" (Ep. 10.96). That is a conscientious, humane, well-read governor describing what he does to people who have committed no act. This is your baseline risk, not the worst case.

**2. The crowd.** Riots over grain, over games, over a rumour. A workshop with an unfamiliar smell, unfamiliar lights and unfamiliar noises, run by a man nobody's grandfather knew, is a natural first target when something goes wrong in a city. Fire is the specific danger: Rome burns regularly and arson accusations attach to strangers.

**3. Your own success.** This is the one people underestimate. Vespasian is said to have refused a labour-saving device for hauling columns, rewarding the engineer but declining to use it, saying he must be allowed to feed the common people (Suetonius, *Vespasian* 18). The story may be a moralising invention. Even so it was told and retold because it expressed something the Roman elite actually believed: that displacing the labour of the poor was a political act, and not obviously a good one. If your mill puts three hundred porters out of work, you have made three hundred enemies and one enemy who matters, the man whose clients they were.

Money does not solve any of these three on its own. Standing does. That is the distinction this module exists to teach.

---

## The rule that governs everything below

**Money protects you only when it has been converted into obligation.**

A chest of coin in your house is a reason to kill you. The same coin spent on a public fountain with an inscription naming the donor is a reason to protect you, because now a town council has a stake in your continued good health and a public record of your piety.

The simulator models this directly. Bare wealth adds nothing to your protection score. Wealth spent on benefaction, patronage, office and, yes, on bribes, adds to it, scaled by how bribable that civilization actually is. Rome scores 0.55 on that scale, which is high. This is not cynicism, it is the *cursus honorum* working as designed: office was routinely bought, and buying it was legitimate.

The converse rule matters just as much. **Speed does not make you a magician, and neither does money.** People habituate to new things astonishingly fast. The simulator applies a familiarity decay: the tenth strange device you show a town is roughly a tenth as alarming as the first. This matches how humans actually behave. The iPhone was witchcraft for about four months.

---

### identity_cover - The Alexandrian physician-philosopher (*medicus et philosophus Alexandrinus*)

**What it is / why you want it.** A coherent, checkable, boring explanation for who you are, where your knowledge comes from, and why you have money. Everything else in this module is built on it.

**Why you would never guess this.** The instinct is to hide. That is exactly wrong. A man with no history is far more alarming than a man with a slightly unusual one. What you want is not concealment but a *dull* story that survives casual checking and explains your anomalies in advance. Alexandria is the correct choice and the reason is specific: it is the one place in the Empire where a man might plausibly have read things nobody else has read, where Greek medicine and mathematics genuinely concentrate, where the Museum's reputation does the explaining for you, and which is far enough away that nobody in a Gallic or Italian town will know you were never there. You are not claiming to be special. You are claiming to have had access to a library, which is both mundane and true.

**Prerequisites.** None. This is the first thing you do, before you speak to anyone who matters.

**Roman-available inputs.** Books, which is to say papyrus rolls, bought in Alexandria or Rome. A house in a decent quarter, rented not bought at first. Clothes that are good but not showy, because the Roman elite reads over-dressing as the mark of a freedman on the make. A Greek freedman secretary, both because you need one and because having one is itself a credential. A visible, cheap, regular piety: sacrifice at the local temple on the ordinary days, attend the ordinary festivals. Nobody has to believe you are devout, they have to be unable to say you are not.

**Procedure.**
1. Spend the first months listening rather than talking. Not because a ritual demands it, but because you need to hear how educated men in *this* town actually speak, what they think of the emperor, and who the local powers are. This is optional and the simulator treats it as optional. It is simply cheap and it works.
2. Establish the medical persona before the mechanical one. Medicine is high-status, portable, explains travel, explains money, and explains a room full of equipment. Mechanics is the trade of a clever slave.
3. Practise real medicine, honestly and mostly conservatively. Roman medicine is not stupid; it is Galenic, systematic and often effective. Your advantage is germ theory, hand-washing, wound irrigation, and knowing when to do nothing. That last one alone will make your reputation.
4. Never claim revelation, prophecy, or a divine source. See the danger note below. Claim a teacher, a library, a school. Sources are checkable in principle and nobody will check.
5. Be visibly, tediously law-abiding in every matter that does not concern your work.

**How you know it worked.** Within a year you are invited to dinner by people who did not invite you before, and someone asks your opinion in front of others. In Roman terms that is the whole of social advancement, and it is observable.

**Failure modes.** Claiming too much. A man who is expert in medicine, mathematics, metallurgy, chemistry and navigation is not a scholar, he is a liar or a magician, and the second is a capital matter. Reveal breadth over decades, and attribute it to your school. Also: money that arrives faster than your visible activity explains. Slow the money down, or buy something that visibly makes it.

**Cost & labour.** Founder hours 500, mostly spent in company rather than at a bench (DERIVED from the node). Capital 1,500 den, upkeep 200 den/yr (ESTIMATED, basis: a modest urban household with one secretary, against attested Egyptian rents and the roughly 1,000-den annual subsistence of a poor family). Calendar 0.5 years.

**Danger.** Social, and it is the largest social danger in the game. *Magia* is a capital charge, and it is not a dead letter: Apuleius was prosecuted for it around 158 AD and had to write a whole defence, the *Apologia*, which survives. What convicts you is not doing strange things, it is doing strange things *inexplicably*. Every device you show must come with a dull mechanical explanation, given before anyone asks. The explanation does not have to be correct. It has to be boring.

**Confidence: HIGH.** The mechanism (patronage, persona, checkable-but-unchecked credentials) is exhaustively attested in Pliny's letters, Martial, Juvenal and the epigraphic record. The denarius figures are estimates.

---

### patron_local - A town patron (*patronus municipii*)

**What it is / why you want it.** One well-placed man in your town who is publicly known to be your protector. This is the single cheapest defensive purchase available to you, and it roughly halves incoming suspicion.

**Why you would never guess this.** The gift that works is not the expensive one. It is the one that solves a problem the patron has and cannot buy a solution to. Almost every literate Roman over forty-five is presbyopic and cannot read his own correspondence without a slave reading it aloud, which is both an inconvenience and a small daily humiliation. A pair of ground reading lenses costs you very little and gives him back something he thought he had lost forever. Nobody else in the Empire can supply it at any price. That asymmetry, cheap to you and unbuyable to him, is what buys a patron, and the same logic applies to a cataract couching, a cure for a wife's fever, or a working set of accounts for an estate he cannot make sense of.

**Prerequisites.** `identity_cover`. Approaching a patron before you have a persona means the persona gets built by other people, out of gossip.

**Roman-available inputs.** Glass, which Rome makes very well indeed, ground or moulded into a plano-convex lens. Rock crystal is the higher-status alternative and Nero is said to have used an emerald, so the *idea* of looking through a stone is not itself strange.

**Procedure.**
1. Identify the man, not the office. You want someone with local weight and imperial connections, ideally an equestrian or a decurion with ambition beyond the town.
2. Find his problem. Attend his morning *salutatio* like everyone else and listen.
3. Give the gift without a request attached. Asking for something in the same conversation converts a gift into a transaction and destroys its value.
4. Let him introduce you. A patron who has decided you are his discovery will do more work for you than one who has been asked for help.

**How you know it worked.** He introduces you to someone unprompted. In Roman practice that is the definitive signal, because his own standing is now attached to yours.

**Failure modes.** Choosing a patron in a faction that loses. Spread across two if the town has two, though this is delicate. Also: becoming a client so completely that your time is consumed by his *salutatio*, which is a real cost that the simulator charges in founder hours.

**Cost & labour.** Founder hours 400. Capital 1,200 den, upkeep 200 den/yr (ESTIMATED, basis: gifts and reciprocal obligations at the low end of what Pliny's letters treat as ordinary). Calendar 0.5 years.

**Danger.** Low, and this is the point of it. It is the cheapest risk reduction on the board.

**Confidence: HIGH** on the institution, **MEDIUM** on the lens as the specific lever. That reading stones and lens grinding were technically within Roman reach is well supported by Roman glass quality and by the Nimrud lens; that no one had made the connection is the reason it works as a gift.

---

### citizenship - Roman citizenship by grant (*civitas Romana*)

**What it is / why you want it.** Legal personhood. Specifically *provocatio*, the right of appeal, plus exemption from the more degrading forms of punishment.

**Why you would never guess this.** This is not about status, it is about physics: it changes who is allowed to kill you and how fast. Without it a governor's decision is final and immediate. With it, the case has to travel to Rome, and travel takes months, and months are enough for patrons to act. Acts 22 records Paul stopping a flogging mid-preparation by stating he was a citizen, and the officer's reaction is telling: he had bought his own citizenship at great cost and was alarmed to have nearly flogged a man who held it by birth. Whatever one makes of the source, it accurately reflects both the procedure and the price.

**Prerequisites.** `patron_local`. You do not apply for citizenship, someone applies on your behalf.

**Roman-available inputs.** Money, and a benefaction that gives the grant a public justification.

**Procedure.**
1. Fund something visible and useful in the town: a fountain, a stretch of road, a portico, grain in a bad year.
2. Have your patron propose the grant on the strength of it. The proposal must be about the town's benefit, never about your convenience.
3. Take the *tria nomina*, adopting the *praenomen* and *nomen* of your patron or of the emperor, as freedmen and grantees did. Your name is now a permanent public statement of who is responsible for you.

**How you know it worked.** You are in the album of the town. In practice: your name appears on the inscription.

**Failure modes.** Buying it too visibly and too early, which invites the question of where a foreign physician got 6,000 denarii. Make the money legible first.

**Cost & labour.** Founder hours 250. Capital 6,000 den (ESTIMATED, basis: attested prices for grants and offices vary enormously by period and province; this sits at the high end of a small-town benefaction). Calendar 3 years, and this is mostly waiting on other people, which cannot be bought down.

**Danger.** Low. Citizenship is the most respectable thing you will ever buy.

**Confidence: HIGH** on the legal effect, **LOW** on the price.

---

### freedman_staff - Buy, teach, and free a technical staff

**What it is / why you want it.** A permanent body of skilled people who can read your notes, run your processes and teach the next intake. This is the node that converts you from a man who makes things into an institution that makes things.

**Why you would never guess this.** The manumission is not charity and it is not squeamishness, though the squeamishness is warranted. It is the load-bearing engineering decision, for a reason specific to Roman law. A freed slave becomes his patron's *libertus*: he owes continuing legal obligations (*operae*), he stays in the household's orbit, and, crucially, **he can own property, make contracts, and be paid**. Roman commerce ran substantially on freedmen for exactly this reason. So manumission does not lose you the man, it upgrades him into someone who can hold a workshop lease, sign for a delivery, take an apprentice and receive a wage that makes him stay.

And the technical argument is stronger still. Coerced labour does what it is told and stops. It has no reason to notice that the crucible cracked differently this time, and every reason not to mention it. Precision work, chemistry and instrument-making are *reporting* problems before they are skill problems: the entire value is in the operator who says "that was not like the last one". A man who is paid, named, and expects to be here in ten years reports. A man who is owned does not.

**A note you should not skip.** The simulator lets you buy slaves and it does not stop you, because a model that refuses to represent the thing cannot show you what it costs. It is in the model because it was the ordinary condition of Roman production and because pretending otherwise would make every cost in this guide a lie. Buying a human being is a grave wrong, and it remains one when it is legal, ordinary, and useful to you. The manumission path is in the tree because it is both the decent route and, on the model's own numbers, the productive one. Those two things agreeing here is a genuine fact about skilled work, and you should not expect them to agree everywhere.

**Prerequisites.** `workshop_first`.

**Roman-available inputs.** The slave market, which in 100 AD is large, legal and unremarkable. Prices for skilled and literate men run far above field hands.

**Procedure.**
1. Buy for literacy and disposition, not for existing craft skill. You can teach the craft. You cannot teach a man to be interested.
2. Teach in Greek and write in Greek. It is the language of technical work in the East and of medicine everywhere.
3. Set the manumission term in advance and in public, five to seven years, and keep it exactly. The keeping is the whole mechanism: the second intake is buying a promise they have watched being kept.
4. Pay wages after manumission at or above the market rate for the trade.
5. Require every man to teach two others. This is what makes it compound.

**How you know it worked.** A process runs correctly for a month without you in the room, and someone brings you an anomaly you had not predicted.

**Failure modes.** Manumitting too fast, which leaves you with the training cost and no return, and manumitting too slowly, which the household notices immediately. Also: teaching a single irreplaceable specialist. Every process needs two people who can run it, because one of them will die.

**Cost & labour.** Founder hours 900. Capital 2,000 den, upkeep 1,400 den/yr (DERIVED from the node; the upkeep is the wage bill and it is the largest recurring cost you take on this early). Calendar 2 years.

**Danger.** Social and moderate. A household of freedmen doing unexplained skilled work reads as a *collegium*, which is the next entry's problem.

**Confidence: HIGH.** The legal position of freedmen and their commercial prominence are among the best-attested facts of the early Empire.

---

### collegium_licensed - A licensed association (*collegium licitum*)

**What it is / why you want it.** Legal permission for a group of people to associate for a stated purpose. Without it, your school is a conspiracy.

**Why you would never guess this.** Modern intuition says a school is obviously fine and a political club is obviously suspicious. Rome's intuition is that *any* standing association of non-elite men is suspicious, and the purpose barely matters. The evidence is precise and it is wonderful: Pliny asks Trajan for permission to form a fire brigade of 150 men at Nicomedia, a city that has just burned down. Trajan refuses (Ep. 10.33-34). His reasoning is that whatever name such societies are given, and for whatever purpose, men who gather together will become a political association. A fire brigade, in a city on fire, is too dangerous. Now consider how a workshop of literate freedmen doing things nobody understands looks by comparison.

**Prerequisites.** `citizenship`, `workshop_first`.

**Roman-available inputs.** A petition, a patron to carry it, and fees.

**Procedure.**
1. Choose a purpose that is legible and unthreatening. A burial society is the classic vehicle, because burial clubs were the one broadly tolerated form and because everyone dies. A cult association attached to a respectable god also works, ideally a healing god, which fits your persona: Asclepius is close to ideal.
2. Register members, dues and meeting days. Keep the records well, and expect them to be read.
3. Meet on the stated days, for the stated purpose, and actually do the stated thing. The burial fund must genuinely bury people.
4. Let the technical work be what the members happen to do the rest of the time.

**How you know it worked.** You have a document, and the magistrate has a copy.

**Failure modes.** Growing past the licensed membership, or admitting men of a different status class, which changes what the association looks like. Also: meeting more often than you said you would. That single detail is what informers report.

**Cost & labour.** Founder hours 350. Capital 2,500 den, upkeep 400 den/yr (ESTIMATED, basis: attested collegium dues and entry fees, scaled to a small association). Calendar 1 year.

**Danger.** Moderate before the licence, low after. An unlicensed association is the specific thing the state is watching for.

**Confidence: HIGH.** Pliny *Ep.* 10.33-34 and 10.92-93 are explicit, and the epigraphy of burial collegia is abundant.

---

### school_founded - The school (*Museum*)

**What it is / why you want it.** The pivot of the entire game. It converts your hours into other people's hours, permanently.

**Why you would never guess this.** Everyone accepts in principle that teaching multiplies effort. What the simulator shows, and what is genuinely surprising, is the *magnitude and the shape* of the cost of delay. Founding the school ten years late does not cost ten years. It costs ten years compounded through every downstream node, because from the founding date onward your scholar count grows and every technology afterwards is worked by more hands. In the sweeps, the founding date is the highest-leverage single decision in the run. It beats every technology choice, including the ones that look strategic. Move it earlier at almost any price.

And a warning against the obvious optimisation: **not founding a school is a legal option and the simulator will let you take it.** You can run the whole game as one man in a workshop. You will get perhaps a fifth of the way. Every run that reaches the transistor founds a school, and every run that founds it late finishes late.

**Prerequisites.** `collegium_licensed`, `arithmetic_positional`, `freedman_staff`.

**Roman-available inputs.** A building with a courtyard, teaching space and workshop space. Papyrus in quantity, which is a real recurring cost. Salaries.

**Procedure.**
1. Teach positional arithmetic first, before anything else. Roman numerals are adequate for recording quantities and are hopeless for calculating with them. This one change makes every later technical subject teachable, and it is the reason the arithmetic node is a prerequisite rather than a nicety.
2. Teach measurement second, and teach it as a discipline: repeat the measurement, record the disagreement, distrust the single number. This is the actual content of the scientific method and it is more valuable than any specific result you could hand them.
3. Take students from every class that will send them. Freedmen's sons will work harder than senators' sons and the senators' sons bring protection. You need both.
4. Have students write. A school that does not produce documents does not survive its founder.
5. Charge fees to those who can pay, teach the rest free, and make sure everyone knows you do.

**How you know it worked.** A student produces a correct result you had not told them, and a second student is able to check it.

**Failure modes.** Teaching results instead of methods, which produces men who can repeat what you said and cannot extend it. Also: keeping the interesting work for yourself. The founder who will not delegate is the binding constraint on his own project, and the model charges him for it in founder hours he does not have.

**Cost & labour.** Founder hours 2,000, the largest single call on your time in the early game. Capital 8,000 den, upkeep 2,500 den/yr, revenue 800 den/yr (DERIVED from the node). Calendar 4 years, and this is a genuine floor: it is the time to teach the first cohort well enough that they can teach. Money cannot buy it down, and the simulator will not let you try.

**Danger.** Social, and this node carries the `status_threatening` trait for a reason. A school that teaches freedmen's sons to calculate is teaching the wrong people a skill that was a marker of their betters. Expect hostility from grammarians and rhetors, who are your direct competitors for students and status, long before you get any from the state.

**Confidence: HIGH** on the mechanism, **MEDIUM** on the four-year floor, which is an estimate from apprenticeship durations rather than a measurement.

---

### endowment_land - Endow in land, not coin (*fundatio*)

**What it is / why you want it.** A permanent income for the institution, held in a form that survives the third century.

**Why you would never guess this.** This is the node where knowing the future is worth the most, and the knowledge is not technical. Between roughly 200 and 270 AD the denarius is progressively debased until the silver content approaches nothing, and prices in the Empire's east rise by orders of magnitude. A cash endowment made in 120 AD is worth approximately nothing by 270 AD. Land is not. Land produces grain, and grain is grain regardless of what the coin is doing. Rome already had the legal vehicle: Pliny endowed his home town's *alimenta* with land rather than money precisely so the income could not be dissipated, and Trajan's imperial *alimenta* scheme worked through mortgages on land. You are not inventing an instrument, you are choosing the right existing one for a reason nobody else has.

**Prerequisites.** `school_founded`. There must be an institution to endow.

**Roman-available inputs.** Agricultural estates, ideally several small and scattered rather than one large. Scattering costs you efficiency and buys you survival: one estate is one bad governor, one raid, one bad decade away from nothing.

**Procedure.**
1. Buy productive land with tenants already on it. You want income, not a project.
2. Vest it in the collegium, not in yourself, with the school as beneficiary in perpetuity.
3. Name the emperor or a major god in the foundation. Interfering with it should require offending someone more dangerous than you.
4. Split across at least three widely separated properties.
5. Write the constitution: how the head is chosen, what the income may be spent on, who may be admitted. Institutions die of unresolved succession far more often than of poverty.

**How you know it worked.** The school runs for a year on estate income alone, with no contribution from you.

**Failure modes.** Buying land you have to manage. Also: an endowment large enough to be worth stealing, held by an institution too weak to defend it. Grow the protection before the endowment.

**Cost & labour.** Founder hours 500. Capital 8,000 den, revenue 4,500 den/yr (DERIVED; the implied return of over 50 per cent is not a land yield, it is the node's accounting of an estate purchased at a fraction of its productive value plus the school's own fees, and it should be read as optimistic). Calendar 2 years.

**Danger.** Low, and falling. Landowning is the most respectable condition in Roman life and it converts you from a clever foreigner into a member of the propertied class.

**Confidence: HIGH** on debasement and on the *fundatio* as a vehicle, **LOW** on the revenue figure, which I would not defend.

---

### patron_senatorial - Senatorial patronage

**What it is / why you want it.** Protection that reaches above the province. A governor can end you; a governor who knows a senator is watching will not.

**Why you would never guess this.** You cannot buy this with money, because senators have money. You buy it with one of exactly three things: a cure, a profit, or a public benefaction made in their name. The third is the reliable one and the least obvious. A Roman senator's actual scarce resource is *visible* generosity, because his standing depends on it and his cash does not stretch as far as his ambition. If you fund a portico and have the inscription name him, you have given him something he wanted and could not afford, and it costs you a building. Pliny's letters are, read from one angle, a continuous record of a man managing exactly this budget.

**Prerequisites.** `school_founded`. You need something worth patronising.

**Procedure.**
1. Identify a senator with a provincial connection to your town, which most have.
2. Approach through his freedmen and his procurator, never directly. Directness is the mark of someone who does not understand the system, and it marks you.
3. Offer the benefaction in his name, unprompted.
4. Cure someone in his household if the chance comes. It will: households are large and Roman medicine has a low floor.
5. Ask for nothing for two years.

**How you know it worked.** A letter from him arrives that you did not solicit.

**Failure modes.** Attaching to a senator on the losing side of a succession. Under a stable emperor this is manageable; in a disputed one it is fatal. Hold two patrons in different factions once you can afford it.

**Cost & labour.** Founder hours 600. Capital 12,000 den, upkeep 1,000 den/yr. Calendar 2 years.

**Danger.** Low directly, moderate indirectly, because you have now joined a faction whether you meant to or not.

**Confidence: MEDIUM.** The mechanism is well attested; the price and timing are estimates.

---

### patron_imperial - Imperial patronage

**What it is / why you want it.** The state's resources, and effective immunity from everything below the emperor. It also unlocks mining concessions, which is the point.

**Why you would never guess this.** Two things here.

First: **you do not approach the emperor.** You approach the *a rationibus*, the finance secretary, or the Praetorian Prefect. These are the men who decide what reaches him, and both offices were often held by freedmen and equestrians who are far more reachable than any senator. The emperor is the last step, not the first.

Second, and this is the genuinely non-obvious part: **the demonstration that buys imperial patronage is the optical telegraph, not a weapon.** The instinct is to offer gunpowder. That is a mistake on its own terms, because you are then a man who makes weapons, and such men are watched, used and discarded. The Empire's real, permanent, structural problem is that a message from Rome to the Rhine frontier takes weeks, which means every frontier crisis is managed by a man who cannot be consulted. Give the emperor semaphore stations from Rome to the Rhine and you have not given him a battle, you have given him his empire back as a thing he can actually govern. That is worth more than any weapon and it makes you infrastructure rather than an armourer.

**Prerequisites.** `patron_senatorial`, `semaphore_telegraph`. The telegraph is the demonstration; without it you are one more petitioner.

**Procedure.**
1. Build a working line over a real distance first, at your own cost, between two towns that care about the result. A demonstration over a stadium's length proves nothing.
2. Document the transmission times against a courier's times over the same route. This is the whole argument and it is a table of numbers.
3. Route the proposal through the *a rationibus* as a matter of expense saved.
4. Offer it as a gift to the state, operated by the state. If you retain control of it you are a threat.
5. Accept honours, decline office. Office puts you in the *cursus honorum*, which consumes years and creates rivals.

**How you know it worked.** A rescript with your name in it, and a mining concession.

**Failure modes.** Being given a magistracy. Politely, expensively decline. Also: an emperor dying. They do, often, and abruptly. Diversify downward into senators and towns before you need to.

**Cost & labour.** Founder hours 900. Capital 25,000 den, revenue 20,000 den/yr (DERIVED from the node: the concessions, not the patronage itself). Calendar 3 years.

**Danger.** Low while your emperor lives. High during a succession, and there will be several.

**Confidence: MEDIUM.** That optical telegraphy was technically available to Rome is solid; Polybius describes a working torch-signalling code centuries earlier. That the imperial administration would have adopted it is my judgement, not a fact, and its failure to adopt the several signalling schemes it already knew of is the obvious objection to it.

---

### academy_network - Three separated academies

**What it is / why you want it.** Redundancy. Three institutions, far apart, holding the same corpus, so that the loss of one is a setback rather than an ending.

**Why you would never guess this.** This is the second node where knowing the future pays, and it pays more than any technology. The Third Century Crisis is coming: roughly fifty years of civil war, plague, invasion and currency collapse, in which cities are sacked and institutions vanish. A single academy, however well endowed, is a coin flip. Three, widely separated, are not. The site choice matters too: Alexandria is dry, and dryness is why we have papyri from Egypt and almost none from Italy. Put the archive copy where the climate preserves it.

This is also where the guide's own honesty is tested. Elsewhere I have argued that historical delays caused by *nobody knowing the answer* are not costs you pay, because you carry the answers. That argument does not apply here. The Crisis does not delete knowledge you personally hold, it deletes the buildings, the endowments, the students and the copies. Redundancy is a real cost against a real risk, and it is not optional.

**Prerequisites.** `endowment_land`, `corpus_dispersed`.

**Procedure.**
1. Alexandria first, for the climate and the existing scholarly community.
2. A western site: Massilia or Lugdunum. Far from the Danube frontier, on trade routes, in a region that stays comparatively intact.
3. An eastern site: Antioch or Pergamon. Wealthy, literate, and it will suffer, which is the argument for the other two.
4. Every text exists in three copies in three places, and a copy is made before the original is consulted.
5. Separate endowments and separate governance. A shared purse is a shared failure.
6. Exchange students between sites on a fixed cycle. People carry tacit knowledge that documents do not.

**How you know it worked.** A site loses its head and continues operating. Test this deliberately while you can afford to.

**Failure modes.** Three academies that are really one, sharing money, leadership and archives. That is one academy in three buildings and it will die once.

**Cost & labour.** Founder hours 2,500. Capital 45,000 den, upkeep 9,000 den/yr. Calendar 3 years to establish, and the diffusion floor is set by how long it takes people and texts to actually move, not by construction.

**Danger.** Moderate. Three institutions are three times the visibility, and a network spanning provinces is exactly the shape of thing the state dislikes. The licences must be genuinely separate.

**Confidence: HIGH** on the Crisis and on Egyptian preservation, **MEDIUM** on the specific sites.

---

## The fourth thing that can end you, and it is the one you will not see coming

Near the top of this module I listed three threats: the magistrate, the crowd,
and your own success. That list was incomplete, and a playtester found the gap
by being killed by something the guide never mentioned.

**Eminence is a hazard in its own right, and none of your defences touch it.**

Everything else in this module is a shield. Patrons, citizenship, a licensed
collegium, a reputation for piety, and money spent on the right people all
reduce the chance that an accusation lands. They work. Push them far enough and
almost nothing can be made to stick.

That is precisely the problem. In an autocracy the danger is not only that
someone accuses you. It is that you become large enough to be worth removing,
and the people best placed to remove you are the ones protecting you.

Sejanus was the most protected man in Rome, Praetorian Prefect and the emperor's
own instrument, until the morning a letter was read out in the Senate and he was
dead by evening. Seneca was Nero's tutor and one of the richest men in the
empire; he was ordered to open his veins. Thrasea Paetus was not accused of
plotting anything. He was admired, he was conspicuous, and he was too obviously
his own man. None of these were brought down by a mob or by a charge of sorcery.
They were brought down by being too eminent in a system with one man at the top.

**How the model treats it.** Prominence accumulates in a pool of its own,
separately from ordinary suspicion, and it rises with your reputation and your
visible wealth. Bribery does not reduce it. You can buy a magistrate, an accuser
and a jury; you cannot buy an emperor's judgement that you have grown too large,
and the attempt is itself evidence for the case. Holding imperial patronage
makes it worse rather than better, because the closer you stand to the throne
the more exposed you are to its turnover.

Usually it costs you a bad year rather than your life. Roughly:

- a confiscation, and you withdraw from public life for a while
- a patron destroyed in somebody else's quarrel, taking his protection with him
- and, less often, the end of the run

**What actually reduces it.** One thing: dispersal. A network of academies in
separate provinces is materially harder to destroy than one great man, and the
model gives it about a third off. This is the same argument as the redundancy
argument for surviving the Third Century Crisis, arrived at from a different
direction, and it is the strongest reason to build the network before you think
you need it.

**What does not reduce it.** More money. More patrons. A better reputation.
Those are the defences against everything else, and against this one they are
the cause.

The honest summary is that the game will let you become powerful enough that
nothing can touch you, and then kill you for exactly that. Both halves are
historically fair, and a player who has read only the first three threats will
feel ambushed by the fourth. That was a real complaint from a real tester, and
this section exists because of it.

## What this module does not let you do

The simulator will let you try anything in here badly, and will let you skip any of it. That is deliberate: a model that only permits the correct play cannot teach you anything about the cost of the incorrect one. So you may run without a school, hoard coin instead of spending it, approach the emperor directly, endow in silver, or announce a technology before you have a patron. None of these are blocked.

They simply lose. Consistently, across sweeps, and for reasons the run log will show you node by node.

The one thing money genuinely cannot buy anywhere in this module is calendar time on the diffusion floors: four years to teach a first cohort, three years for a network to become a network. Those are the times it takes for people to learn things and to move, and no amount of denarii changes them. Everything else here is for sale, and the whole argument of this module is that you should buy it early.

---

## Sources and confidence

| Claim | Source | Confidence |
|---|---|---|
| Governor's coercive power over non-citizens | Pliny *Ep.* 10.96 | HIGH |
| Citizenship halts summary punishment | Acts 22:25-29 | HIGH on the procedure it depicts |
| Associations refused even for firefighting | Pliny *Ep.* 10.33-34 | HIGH |
| *Magia* prosecuted as a capital matter | Apuleius, *Apologia* | HIGH |
| Labour-saving device refused for political reasons | Suetonius, *Vespasian* 18 | MEDIUM, the anecdote may be moralising |
| Land endowment as the durable vehicle | Pliny's *alimenta*; Trajan's scheme | HIGH |
| Third-century debasement to near-zero silver | Numismatic record | HIGH |
| Freedmen could own property and trade | Legal and epigraphic record | HIGH |
| Optical signalling known to antiquity | Polybius X.43-47 | HIGH on the method, LOW on adoption |
| All denarius figures in this module | My estimates from the node data | LOW |

## Where to go next

- The nodes themselves: [`tech_tree.json`](../data/tech_tree.json), ids `identity_cover` through `academy_network`.
- How the reaction is computed, including why money protects rather than endangers: [`00_NONOBVIOUS_TRICKS.md`](00_NONOBVIOUS_TRICKS.md).
- What a different society would do with these same nodes: [`../data/civilizations/_SCHEMA.md`](../data/civilizations/_SCHEMA.md). The Norse file inverts the sign on labour-saving technology, because labour there is scarce rather than cheap, and the whole of the Vespasian problem simply disappears.
- Money-making, which is what pays for all of the above: [`96_finance.md`](96_finance.md).
