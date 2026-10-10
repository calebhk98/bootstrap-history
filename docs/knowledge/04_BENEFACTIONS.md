# Module 04: Benefactions - What Wealth Is Spent On

## Why this module exists

Once the school, the patrons and the money exist, cash piles up faster than research can use it, and cash that sits idle only makes a fortune worth confiscating. Rich people and rich companies have always spent on the same handful of things: teaching, healing, water, harbours, shows, gods, artists, banks, grain for the poor, gifts to the state and voyages. Each is a lasting work with running costs, and each buys something the founder can use: literacy, health, name, protection, credit, reach.

Every entry here is an ordinary node in `data/branches/56_benefactions.json`. Nothing sells anything: the return is what the work does through the game's normal channels (listed in `data/branches/MECHANICS.md`). Building costs labour and materials at the usual rates. Running costs come every year the doors are open, worked out from the people and consumables the work needs (each node's `_internal` field shows the working), and the effect stops when the money does. Every work marked repeatable can be founded again, dearer each time, up to what the population can fill. All sizes are heuristics: run `why <id>` for the current cost, upkeep and figures.

Some works are paid once rather than kept up: paying off the state's debt, settling the claims of an interest group, a grant for disaster relief, and a charter for a colony. They have no running cost; what they do is done when they are finished, and the `pay` and `settle` commands do the same again later. Works repeated across the land (schools, clinics, lit streets) are rolled out with the `rollout` command until a chosen share of the people is reached. Gambling houses and lotteries are ordinary concerns that pay the state a share of their takings each year.

---

### ben_free_school_foundation - Free school foundation (*alimenta*)

**What it is / why you want it.** A school for pupils whose families cannot pay, kept by land income, with a midday meal. It adds to the flow of schooling, so literacy rises faster, and it earns the founder standing.

**Why you would never guess this.** Charity schools work as an endowment, not a gift: the land pays the teachers every year. The second one costs more than the first because it draws on the same few people fit to teach.

**Prerequisites.** `school_founded`, `endowment_land`.

**Cost & labour.** Teachers and scribes on the payroll, food and parchment each year. ESTIMATED.

### ben_public_library - Public library

**What it is / why you want it.** A reading room open to any reader, with librarians who lend and copy. Teaches by example, so it adds less schooling than a school does, and gives the founder the name of the man who gave a town its books.

**Why you would never guess this.** Books are only worth the readers who can use them; the library's ceiling is set by literacy, like a school's.

**Prerequisites.** `school_founded`, `printing_press`.

**Cost & labour.** Building, books, copyists. ESTIMATED.

### ben_research_foundation - Endowed research foundation

**What it is / why you want it.** Laboratories, an observatory, instrument makers and an annual silver prize, left to a standing body of scholars. It raises the number of trained scholars the household can keep and the founder's standing.

**Why you would never guess this.** A prize does not make discoveries; it pays for the time and instruments of the people who do.

**Prerequisites.** `fin_research_institute`, `fin_learned_society`.

**Cost & labour.** Instruments, glass, metal, fuel and the prize each year; the scholars are paid through the household's staff. ESTIMATED.

### ben_hospital_foundation - Endowed hospital

**What it is / why you want it.** Wards, physicians and nurses paid for from an endowment. It lowers the share of the household's people that a bad year of sickness carries off.

**Why you would never guess this.** A hospital that keeps records and separates the sick from the well helps far more than one that only shelters them; the prerequisite is the records, not the building.

**Prerequisites.** `med_hospital_institution`, `endowment_land`.

**Cost & labour.** Masons, carpenters, plumbers; then physicians, nurses, food and fuel each year. ESTIMATED.

### ben_civic_water_works - Aqueduct, baths and sewers for a town

**What it is / why you want it.** Clean water piped in, foul water piped out, baths to use it. It lowers losses to water-borne disease and gives the founder standing.

**Why you would never guess this.** The channel is the smaller cost. A supply that is not cleared and mended every year silts and leaks within a generation.

**Prerequisites.** `civ_aqueduct_roman`, `civ_sewer_roman`.

**Cost & labour.** Stone, lead, and gangs of labourers and masons; maintenance crews each year. ESTIMATED.

### ben_harbour_and_lighthouse - Harbour works and lighthouse

**What it is / why you want it.** A breakwater, quays and a fire on a tower. Ships that can shelter and find the mouth at night come, and buyers come with them: wider market reach, fewer losses at sea.

**Why you would never guess this.** The fire burns fuel every night, and moles silt. A harbour is a running cost, not a monument.

**Prerequisites.** `civ_harbour_dock`, `sea_pharos_lighthouse`.

**Cost & labour.** Stone in bulk, timber, iron; dredging, keepers and fuel each year. ESTIMATED.

### ben_telegraph_network - Telegraph lines to the provincial towns

**What it is / why you want it.** Wire and operators between the towns you trade with. Orders and prices travel at once, so one person can direct agents far away and the market reach widens.

**Why you would never guess this.** The wire is cheap next to the people who keep it working: linemen, operators, cells.

**Prerequisites.** `telegraph_electric`, `fin_telegraph_business`.

**Cost & labour.** Copper wire, poles, insulators; linemen and cells each year. ESTIMATED.

### ben_public_games - Public games and festivals

**What it is / why you want it.** Shows, races and feasting paid from one's own purse. The crowd remembers who paid: standing rises and the founder is a little safer with the people. He is also more visible to those above, who cannot buy the same love.

**Why you would never guess this.** The bill is mostly bread and wine for the crowd, and it comes again every time the games are held.

**Prerequisites.** `civ_amphitheatre`, `patron_local`.

**Cost & labour.** Performers, stagehands, and grain, wine and oil on a large scale each year. ESTIMATED.

### ben_temple_endowment - Temple and shrine endowment

**What it is / why you want it.** A temple with land, servants and daily offerings. What is given to the gods is hard to take back, and the priesthood speaks for its benefactor.

**Why you would never guess this.** The protection comes from the priests, not the stone: it lasts only while the servants are fed and the lamps lit.

**Prerequisites.** `endowment_land`, `citizenship`.

**Cost & labour.** Masons and bronze at the start; servants, oil and grain each year. ESTIMATED.

### ben_scholar_and_artist_patronage - Patronage of scholars, poets and artists

**What it is / why you want it.** A table and a stipend for men who write, paint, play and calculate. They carry the patron's name and give him people to call on.

**Why you would never guess this.** A circle that only flatters is worth less than one that can do useful work; the scholars in it count toward the staff the household can keep.

**Prerequisites.** `patron_senatorial`, `school_founded`, `prn_theatre_pantomime`.

**Cost & labour.** Commissions in silver, parchment and paper each year. ESTIMATED.

### ben_house_bank - House bank

**What it is / why you want it.** A banking house of one's own, with a strongroom and a reserve. Depositors' money becomes the founder's credit: he borrows more and more cheaply.

**Why you would never guess this.** A bank that lends to the powerful is only as safe as they are.

**Prerequisites.** `fin_deposit_bank`, `patron_local`.

**Cost & labour.** Strongroom, silver reserve, clerks and factors each year. ESTIMATED.

### ben_underwriting_syndicate - Underwriting syndicate

**What it is / why you want it.** A silver reserve and a clerkroom that write cover for ships, houses and lives. Spreading risk over many policies turns a disaster into a bill.

**Why you would never guess this.** The reserve does the work, and it is idle money by design.

**Prerequisites.** `fin_reinsurance`, `fin_fire_insurance`, `fin_life_insurance`.

**Cost & labour.** Silver reserve, clerks and underwriters each year. ESTIMATED.

### ben_grain_dole - Public granary and grain dole

**What it is / why you want it.** Granaries and a register of households, grain bought each harvest and handed out each month. A bad harvest hurts the town less, and the crowd owes its bread to a name.

**Why you would never guess this.** The dole never shrinks while the town grows. The cost is the grain, bought every year.

**Prerequisites.** `fin_annona`, `endowment_land`.

**Cost & labour.** Granaries and an opening stock of grain; grain and clerks each year. ESTIMATED.

### ben_state_subvention - Subsidy to the army and the treasury

**What it is / why you want it.** Silver paid every year toward the army, the fleet and the interest on the state's debt. A state that lives on the founder's money is slow to think ill of him. The protection counts as much as the society's habit of patronage does.

**Why you would never guess this.** It is protection rented by the year: when the payments stop the favour goes with them.

**Prerequisites.** `fin_public_debt`, `patron_senatorial`.

**Cost & labour.** Silver each year. ESTIMATED.

### ben_survey_and_trade_expedition - Sponsored survey and trade expedition

**What it is / why you want it.** A small fleet, a mapmaker and a factor sent to coasts and markets nobody in the household has seen. What comes back is charts and buyers: wider reach and a name for enterprise.

**Why you would never guess this.** Ships and crews are provisioned and repaired every season whether or not the last voyage paid.

**Prerequisites.** `exp_openocean_navigation`, `fin_survey_map`, `exp_trade_route_extend`.

**Cost & labour.** Hulls, iron, rope, provisions; crews and repairs each season. ESTIMATED.

### ben_public_museum - Public museum

**What it is / why you want it.** A building for a collection of texts, specimens and instruments, with curators, open to anyone. It teaches a little and earns the founder standing.

**Why you would never guess this.** A collection is read by few and only teaches as far as literacy reaches; as a safeguard for knowledge it would count only as one more copy in one town, which the game does not yet model.

**Prerequisites.** `fin_museum`, `school_founded`.

**Cost & labour.** Masons and carpenters to build; curators and scribes, fuel and paper each year. ESTIMATED.

### ben_free_press - Endowed free press

**What it is / why you want it.** A paper kept printing whether or not it sells. It gives a town something to read, carries prices to distant markets, and makes its founder known.

**Why you would never guess this.** The same press that widens your markets draws the eye of officials: a paper is both a help and a danger, and it raises the alarm and the notice your work causes while it runs.

**Prerequisites.** `prn_newspaper_institution`, `fin_newspaper_business`.

**Cost & labour.** Printers, correspondents and engravers on the payroll; paper and ink each year. ESTIMATED.

### ben_city_electric_lighting - Electric lighting for a city

**What it is / why you want it.** Lamps along a town's streets, kept by electricians. Lit streets are safer for your people after dark and earn a little respect.

**Why you would never guess this.** It draws power from the grid the whole time it is lit, so it needs generating capacity as well as lamps; and it has a running cost the bare street-lighting technique does not.

**Prerequisites.** `civ_street_lighting`, `hom_electric_lighting`.

**Cost & labour.** Electricians and labourers to build and keep; copper and glass each year. ESTIMATED.

### ben_fire_and_flood_brigades - Fire and flood brigades

**What it is / why you want it.** Paid crews with pumps, buckets and sandbags, drilled to turn out at a bell. They hold fire and flood damage to your own people and workshops to a part of what it would be.

**Why you would never guess this.** It protects what you own, not the town: a quarter without a brigade burns as before.

**Prerequisites.** `civ_aqueduct_roman`, `patron_local`.

**Cost & labour.** Labourers and carpenters on the payroll; rope and iron each year. ESTIMATED.

### ben_masons_school - School of the building trades

**What it is / why you want it.** A trade's own school: master masons teach drawing and setting out. Masons do more per hour and the household can keep a few more trained people.

**Why you would never guess this.** The gain is to one trade only; the effect of having built it stays when the doors close, while the extra trained staff go with the money.

**Prerequisites.** `school_founded`, `fin_guild`, `fin_apprenticeship`.

**Cost & labour.** Teachers and masters on the payroll; parchment and paper each year. ESTIMATED.

### ben_technical_school - Technical school for machinists

**What it is / why you want it.** A school with a shop floor and a classroom for drawing and arithmetic. Machinists do more per hour and the household can keep a few more trained people.

**Why you would never guess this.** Like the building trades school, it helps one trade; the machinist's hour is what the late-game works draw on.

**Prerequisites.** `school_founded`, `fin_apprenticeship`, `mfg_engine_lathe`.

**Cost & labour.** Instructors and machinists on the payroll; iron, coal and paper each year. ESTIMATED.

### ben_trading_post - Fortified trading post

**What it is / why you want it.** A walled depot on a far coast where ships refit, trade and take on stores. Goods travel further and fewer voyages are lost.

**Why you would never guess this.** It is a post, not a colony: it holds no land beyond its walls and no people but its own, and it has to be fed from home every year.

**Prerequisites.** `exp_colony_administration`, `fin_trading_post`.

**Cost & labour.** Masons, carpenters and labourers to build; factor, clerks, labourers and provisions each year. ESTIMATED.

### ben_state_debt_redemption - Redemption of the state's debt

**What it is / why you want it.** The founder pays the whole of what the state owes in one sum, or as much as the founder's money covers. A state that owes less pays less interest and can borrow more cheaply, and it is slow to forget who cleared its books.

**Why you would never guess this.** Paying more than the state owes does not clear anything further: the rest lies in the state's purse as a reserve for the state to spend as it likes. Walpole's sinking fund of the 1720s was raided for other uses until Pitt shielded it in 1786, so the honest cost of a repayment is that the state may borrow again as soon as it is free to.

**Prerequisites.** `fin_public_debt`.

**Cost & labour.** Clerks and bankers to find the holders and buy the bonds in; the sum itself, which is the state's debt on the day. ESTIMATED.

### ben_political_settlement - Settlement of an interest group's claims

**What it is / why you want it.** The founder pays what the state has undertaken to make good to the guilds, landholders or craftsmen who lost income to the founder's methods, so the state does not have to raise it from taxpayers. A body that is paid presses the state less and blames the founder less.

**Why you would never guess this.** It settles the claims of today only. When the founder's methods hurt a new body, a new claim stands, and the pay command meets it.

**Prerequisites.** `fin_government`, `fin_guild`.

**Cost & labour.** Envoys and clerks; the claims themselves. ESTIMATED.

### ben_disaster_relief_grant - Grant to the state for disaster relief

**What it is / why you want it.** A large sum paid to the state after a flood, a fire or a failed harvest, to feed the homeless, clear what is unsafe and rebuild. The state spends it through its own officials on its dole and public works.

**Why you would never guess this.** The grant eases the state's deficit; it does not feed anyone by itself. Grain handed out directly to the hungry is the work of the public granary, which the nation's people eat.

**Prerequisites.** `fin_annona`, `fin_public_debt`.

**Cost & labour.** Clerks; the sum itself. ESTIMATED.

### ben_settlement_charter - Charter and outfit for a settlement

**What it is / why you want it.** The right to found a settlement on a tile nobody holds that borders what the founder holds, or on a coast across the sea. Families go from home with ships, stores, tools and seed, and become a people of their own on that land.

**Why you would never guess this.** The colonists leave the home country's working age, and the outfit is paid at the society's wage. The Cape settlement of 1652 began as a refreshment station of a company's employees; Jamestown lost most of its colonists in its first winters. A colony lives or dies by whether its own hands can work enough land to feed it.

**Prerequisites.** `exp_colony_administration`.

**Cost & labour.** Lawyers and merchants for the charter; a year's work for each settler at the wage of the day. ESTIMATED.

### ben_district_clinics - District clinics

**What it is / why you want it.** A clinic in each district where mothers and children are weighed, vaccinated and treated early. The nation's burden of disease falls by the share of its people the clinics reach.

**Why you would never guess this.** One clinic does almost nothing for a nation. The burden falls in proportion to the share of the people within reach of an open clinic, which is why a rollout (many clinics until a chosen share is covered) is the work, not the first building.

**Prerequisites.** `md2_child_clinic`, `md2_maternal_clinic`.

**Cost & labour.** Masons and carpenters to build; a nurse, a physician and labourers on the payroll, soap and fuel each year. ESTIMATED.

### ben_village_schools - Schools in every parish

**What it is / why you want it.** A reading school in each parish for the children of ordinary families, paid for from an endowment of land. General literacy rises faster.

**Why you would never guess this.** It does nothing for the lettered few, who are taught elsewhere. Each school serves only its own parish, so the work is the rollout, not the single school.

**Prerequisites.** `school_founded`, `endowment_land`.

**Cost & labour.** Teachers on the payroll, parchment each year. ESTIMATED.

### ben_endowed_college - Endowed college for scholars

**What it is / why you want it.** Lodgings, a hall and a library for young men of the propertied classes, kept by the rents of an endowment of land. It raises the literacy of the lettered class, which the learned trades and the state's offices draw on.

**Why you would never guess this.** It does nothing for the reading of the common people; the schools in every parish do that.

**Prerequisites.** `school_founded`, `endowment_land`.

**Cost & labour.** Fellows and clerks on the payroll, parchment each year. ESTIMATED.
