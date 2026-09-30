# Module 04: Benefactions - What Wealth Is Spent On

## Why this module exists

Once the school, the patrons and the money exist, cash piles up faster than research can use it, and cash that sits idle only makes a fortune worth confiscating. Rich people and rich companies have always spent on the same handful of things: teaching, healing, water, harbours, shows, gods, artists, banks, grain for the poor, gifts to the state and voyages. Each is a lasting work with running costs, and each buys something the founder can use: literacy, health, name, protection, credit, reach.

Every entry here is an ordinary node in `data/branches/56_benefactions.json`. Nothing sells anything: the return is what the work does through the game's normal channels (listed in `data/branches/MECHANICS.md`). Building costs labour and materials at the usual rates. Running costs come every year the doors are open, worked out from the people and consumables the work needs (each node's `_internal` field shows the working), and the effect stops when the money does. Every work marked repeatable can be founded again, dearer each time, up to what the population can fill. All sizes are heuristics: run `why <id>` for the current cost, upkeep and figures.

Not yet covered: museums, newspapers and gambling houses as benefactions (the tree has them only as businesses with no effect on the household), colonies, and paying off a state's debt outright rather than subsidising it.

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
