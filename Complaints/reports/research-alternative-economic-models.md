# Alternative economic models, and a proposed input-output plus shadow-price architecture

Research report for the owner. It builds on, and does not repeat, `Complaints/reports/research-reference-economy-models.md`
(Capitalism Lab, Eurace@Unibi, Econ-ARK HARK, Caiani et al. 2016), `Complaints/reports/research-agent-based-economy-design.md`
(Lengnick, Caiani, Wiese, Peters, Lavoie) and `docs/architecture/ECONOMY_MODEL_SURVEY.md` (input-output, CGE, agent-based,
games). No code was changed.

## Sourcing key

- OPENED: I fetched the page in this session and read what it returned. The URL is given.
- SNIPPET ONLY: seen only in a web search result summary. Treat as unverified.
- NO SOURCE FOUND: I looked and found nothing for the name; I do not guess what it is.
- "Reading" marks my inference, not a claim by the source.
- Repo claims were measured on branch `research-alternative-economic-models` (from `section5-bugs-and-eurace-review`) with
  the command shown. The Eurace clone is the scratchpad one named in the task.
- GitHub's API (`gh`) was refused in this session, so I have repository dates only where a page showed them. Most
  repository pages I opened did not show a release or commit date; "maintained" below is a reading from the page
  (open issues, commit counts, a recent copyright year), never a confirmed date.
- No figure below is recalled from memory. Names of models that I could not open are listed at the end.
- FOLLOW-UP PASS: a second session opened the owner-supplied links. Items marked OPENED (follow-up) were fetched in that
  session. A PDF that the fetch tool could not read was downloaded and converted to text with `pdftotext`; those are marked
  OPENED (PDF). "Not shown" means the page showed no such fact. The third-party links were checked for being what they
  were said to be; section "Follow-up pass" below gives the verdict for each.

---

## Per-model notes

Each note: what it is, language, licence, maintained, then the mechanism tied to a problem here or "nothing applicable".

### BeforeIT.jl (OPENED, https://github.com/bancaditalia/BeforeIT.jl)
Behavioural agent-based macro forecasting package from the Bank of Italy, built on the model of Poledna et al. Julia,
Apache-2.0. Appears maintained (many commits; releases list empty, no dates shown). Built from `parameters` and
`initial_conditions`, run for a number of quarters, with an Austria and an Italy parametrisation and counterfactual scenarios.
The page does not describe a shock mechanism or the model's rules (the rules are read in the follow-up section below from the
IIASA working paper). Mechanism: the initial conditions come from national accounts and input-output tables (OPENED (PDF),
https://pure.iiasa.ac.at/id/eprint/16268/1/WP-20-001.pdf, appendix C), so the opening is calibrated to a data stationary state. This is the same idea Caiani et al. give for
Complaint 473 and `opening_runs`, with nothing new. Nothing applicable beyond that: its sectors are modern national-accounts
categories (Reading: they cannot be reused for a tenth-century opening without authoring the data, which is the job
`data/production/` already does).

### K+S, Keynes plus Schumpeter (Dosi, Fagiolo, Roventini 2010) (SNIPPET ONLY, https://econpapers.repec.org/RePEc:eee:dyncon:v:34:y:2010:i:9:p:1748-1767)
Agent-based model joining Keynesian demand with Schumpeterian technology-driven growth; the abstract finds complementarities
between demand drivers and technological change. Language and licence: no source found (the earlier report also could
not open the paper, `research-agent-based-economy-design.md` section 1.7). A COMSES catalogue entry exists
(https://catalog.comses.net/publications/1770, SNIPPET ONLY). Mechanism that could matter: firm research and development
and imitation draws that move a capital-goods producer's productivity, and the demand-technology feedback. Tie: the
tech-adoption side of the founder's bootstrapping, not Complaint 473 (the opening). No complaint is open for it that I could
tie it to; nothing applicable to the spin-up.

### JMAB (Caiani, Godin) (OPENED, https://github.com/S120/jmab)
Java framework for stock-flow consistent agent-based macro models, configured through a Spring beans file. MIT-style text with
copyright 2016; Java 6 or later. The page shows no commit date; the toolkit page (follow-up section) dates its papers to 2016 through 2018, so it looks
unmaintained. The README names no agents or markets. The benchmark model it runs is Caiani et al. 2016, which the earlier
report already read (stationary state solved before the run, section 4 of that report). Nothing new; as a library, nothing
applicable (Java, and the repo has its own engine).

### CATS and BAM (Delli Gatti, Gallegati and co-authors) (SNIPPET ONLY, https://exploring-economics.org/pl/study/books/macroeconomics-from-the-bottom-up, https://www.jasss.org/14/4/reviews/8.html)
CATS means Complex AdapTive Systems; BAM is Bottom-up Adaptive Macroeconomics, the book's basic model with a credit market
where firms borrow when their resources fall short. Code and licence: no source found. The earlier report records the
"bankruptcy avalanche when leverage is high" finding as a snippet. Mechanism: a financial accelerator with a credit network
(Reading: relevant to Complaint 641, lenders ask nothing for default, as an example of leverage-dependent lending, which
Caiani et al. already supply and the earlier report already opened). Nothing new.

### Mark-0 and Mark-I (Gualdi, Tarzia, Zamponi, Bouchaud) (OPENED abstract, https://arxiv.org/abs/1307.5319)
Paper studies the phase diagram of simple macro agent-based models, starting from Delli Gatti's "Mark I". Finds a
transition between a low-unemployment and a high-unemployment state, generically driven by an asymmetry between firms'
hiring and firing rates; a bankruptcy threshold adds endogenous crises. The abstract does not mention "Mark-0"; I could not
tell whether it means this paper's model or another (the Peters et al. paper, https://arxiv.org/abs/2205.00752, was opened
and does not mention Mark-0 either: it calls its model unnamed; the earlier report cites it as "Mak(h)ro 0").
Mechanism that could matter: hiring versus firing asymmetry as the source of a bad state, tied to Complaint 473's
unemployment and unsold-hours behaviour in the spin-up (the earlier design report item (d), hours unhired). The method
(map the phase diagram of the parameters, then place the opening on the good side) is a way to show the opening is not a
point on a cycle, not an engine feature. No code or licence found.

### Lagom generiC (Mandel, Jaeger, Fuerst and co-authors) (SNIPPET ONLY; the two owner links yielded only a citation, see follow-up; https://globalclimateforum.org/2010/03/17/release-of-lagom-generic-2-0-an-agent-based-model-of-growing-economies/)
Prototype agent-based model of disaggregated growing economies with capital accumulation, building on Gintis' work on the
dynamics of general equilibrium; a three-sector German application is mentioned. Release 2.0 was in 2010; nothing newer
turned up, so likely unmaintained. Licence and language: no source found. Mechanism: agents that adjust prices
themselves with a general-equilibrium structure underneath (the Gintis line the earlier survey already covers in
`ECONOMY_MODEL_SURVEY.md` section 3). Nothing new.

### abcEconomics, ABCE (OPENED, https://abce.readthedocs.io/en/master/)
Python platform for agent-based trade and production models. Goods are physical objects: a transfer moves the good and the
giver no longer has it. Firm and Household archetypes, parallel execution, accounting in a separate package (abcFinance).
Licence: not stated on the page. Maintained: no. The GitHub repository was archived by its owner on 23 January 2024 and is
read-only (OPENED (follow-up), https://github.com/AB-CE/abce). Mechanism: conservation by construction (a good cannot be created by a transfer).
Reading: this repo already has that through its ledger and settlement; nothing applicable. It states nothing on price
formation.

### sfctools (SNIPPET ONLY, https://pypi.org/project/sfctools; the PyPI page itself would not load)
Python toolbox for stock-flow consistent agent-based macro models from the German Aerospace Center (DLR): agents, a world
registry, balance sheets that enforce stock-flow consistency, a graphical interface. MIT licence, published in the Journal of
Open Source Software 2023 per the search summary. Appears maintained (releases through a late version). Mechanism: a
balance-sheet class that refuses unbalanced bookings. Tie: the repo's existing money and settlement checks (see the
one-owner-per-fact walls); a stock-flow consistency check at every transaction is a test idea, not a new mechanism.
Nothing applicable to a named complaint.

### AgentPy (OPENED, https://agentpy.readthedocs.io/en/latest/)
Python library for building and analysing agent-based models. Licence not named on the page. Latest changelog entry is
from December 2021, so likely unmaintained. A generic framework: nothing applicable (this repo has its own engine).

### Mesa (OPENED, https://github.com/projectmesa/mesa)
Python library for agent-based models, Apache-2.0, actively maintained by the page's signs (Mesa 3 stable, Mesa 4 in
pre-release, open issues and pull requests). A framework with visualisation; nothing applicable: the repo's engine is
already past the stage where a framework helps, and `sim/` forbids new loose scripts. Its experiment and batch tooling
could inform how the repo runs ensembles (CLAUDE.md 4.2) but I did not open that documentation.

### Agents.jl (OPENED, https://github.com/JuliaDynamics/Agents.jl)
Pure Julia agent-based framework, MIT, apparently maintained. Supports discrete-time and event-queue continuous-time
simulation, and spaces built from OpenStreetMap data. Julia is a language this repo does not use; nothing applicable.

### ACCEPTS (NO SOURCE FOUND)
Two searches returned nothing named ACCEPTS. Ambiguous; I do not guess. The closest unrelated hit was SABCEMM
(https://arxiv.org/abs/1801.01811, SNIPPET ONLY), a financial market simulator, which I do not claim is the intended one.

### ARIO and BoARIO (OPENED, https://spjuhel.github.io/BoARIO/boario-math.html and https://github.com/spjuhel/BoARIO/)
ARIO is the Adaptive Regional Input-Output model; BoARIO is its Python implementation, GPL-3.0, developed in a PhD
project in free time, with open issues and a build badge (so informal but alive). The model starts from a multi-regional
input-output table in equilibrium, each industry holding input stock for a set number of days, and applies shocks: a direct
cut in capacity, or loss of productive capital that must be rebuilt. When demand exceeds production, orders are rationed
proportionally; inventories buffer unfilled orders; capacity can rise above base when unmet demand is positive ("overproduction");
destroyed capital adds rebuilding demand. The page states that prices and the demand-side macro feedback are not
covered there (a separate monetary-factors page exists, not opened), and says nothing on stock-flow consistency.
Mechanisms that could matter: (a) the proportional rationing plus input stock buffer as a way a missing input cuts a
recipe's run by the share it is short, not to zero; this ties to CLAUDE.md section 5 ("a shortage of one input must not
silently stop everything"), and to the unmet-orders handling that the repo already has in settlement (I did not measure
it); (b) rebuilding demand after a loss, which is a shock test for the repo's investment rule
(`producers_close._investment`). It cannot serve as a price owner: it fixes final demand and does not model prices on the
page I read. Not usable for our opening (modern multi-regional tables), usable as a pattern for shock tests.

### ColonD (NO SOURCE FOUND)
One search returned nothing named ColonD. Ambiguous; I do not guess.

### GAMA Platform (OPENED, https://github.com/gama-platform/gama)
Open-source modelling and simulation environment for spatially explicit agent-based simulation, GPL-3.0, modelling language
GAML, Java and Eclipse based, extensions for shapefile and OSM data, apparently actively developed. A GIS-first framework.
Nothing applicable: the repo's map (`sim/geography/`) is its own and the engine is Python; GAMA offers a visualiser at most.

### CGE models: GTAP, MPSGE, Envisage, GEMPACK (SNIPPET ONLY for all; the web summary is https://en.wikipedia.org/wiki/GTAP, https://gtap.agecon.purdue.edu/models/envisage.aspx, https://gams.com/53/docs/UG_MPSGE_Intro.html)
GTAP is a multiregion, multisector CGE model and database coordinated at Purdue; the standard model is implemented in
GEMPACK (Monash) and also in GAMS; Envisage is a recursive-dynamic CGE model first built at the World Bank for climate
questions; MPSGE is a GAMS subsystem for general equilibrium on nested constant-elasticity production and utility functions,
reducing to mixed complementarity problems, with a JuMP-based port MPSGE.jl under development. Licences: no source
found. Mechanism: the base year is calibrated to be an exact equilibrium and then shocked, with a closure choice;
prices come from zero excess demand with a numeraire. `ECONOMY_MODEL_SURVEY.md` section 2 already covers CGE and rates
it as fitting poorly (a calibrated base year does not exist for an opening that is itself a model output). Nothing new.

### HABITAT and IIASA models, MESSAGEix (MESSAGEix OPENED, https://github.com/iiasa/message_ix; HABITAT NO SOURCE FOUND)
MESSAGEix is a linear programming model framework for strategic energy planning and integrated assessment, a GAMS core with a
Python package and an R interface, Apache-2.0, maintained by the page's signs (copyright through 2026, many commits), and it
can link to the MACRO general equilibrium model to feed prices back to demand. The page does not mention dual prices.
HABITAT: searching returned nothing under that name (only the MESSAGEix-GLOBIOM combination); ambiguous, not guessed.
Mechanism: a cost-minimising dispatch over a technology list with vintages and capacity, solved as an LP, and a
price-demand iteration with a macro model. Tie: only as the cost-minimising choice of technique, which the repo's
`opening_runs.choose_recipes` already does with a ranking (see below). Nothing else applicable.

### 1:1 synthetic firm networks, Poledna and CSH Vienna
The Poledna forecasting model is now OPENED (follow-up section below). Earlier summary (SNIPPET ONLY, https://irihs.ihs.ac.at/id/eprint/6453/):
an agent-based model of a small open economy at 1:1 scale with sectors, input-output and financial links, calibrated from
national accounts, input-output tables and business demography; it claims forecasting competitive with VAR and DSGE. A
related CSH Vienna line builds a firm-level production network of a whole country from VAT data
(https://link.springer.com/10.1038/s41598-022-11522-z); the follow-up pass confirmed this is Diem, Borsos, Reisch, Kertesz and
Thurner (Scientific Reports 2022), and Poledna is not an author. Both depend on modern administrative micro data, which
does not exist for a tenth-century opening. Mechanism: one agent per real firm, which this repo cannot calibrate. Nothing
applicable to the opening; the idea of reporting indirect losses by tracing a firm's removal through the network is a
possible check for the bankruptcy-cascade question the proposal raises.

### PyPSA (OPENED, https://github.com/PyPSA/PyPSA)
Python framework for optimising and simulating power and energy systems, MIT code licence, solvers HiGHS (default), GLPK,
CBC, Gurobi, Xpress; many commits, appears maintained. The pages I opened did not describe how marginal prices are
exposed (the repository page names `marginal_cost` and `n.statistics()`; the documentation front page did not mention
marginal prices). I therefore cannot cite that PyPSA returns nodal shadow prices; Reading: it is a standard property of
network LPs, but not verified here. Mechanism that fits: a network of buses and links with capacities, balance at each node,
solved as a linear programme. Tie: the proposal's step two. It is built for electricity (a single homogeneous commodity per
carrier), not for hundreds of goods with recipe vectors, so it would be a misfit as a dependency; the equivalent
for our case is a small linear programme written in whatever solver the repo accepts as a dependency (the repo's
`requirements.txt` lists numpy only, measured with `grep -n -i 'scipy\|numpy' requirements.txt`).

### Calliope (OPENED, https://github.com/calliope-project/calliope)
Python multi-scale energy systems modelling framework (Pyomo based, YAML and CSV model definitions), Apache-2.0, appears
active. Spatial and temporal resolution, many runs from one base model. Mechanism: data-defined technologies and
locations kept apart from the framework code. That is already this repo's approach (data in `data/`, engine without content
ids, CLAUDE.md 4.7). Nothing applicable.

### SpineOpt (OPENED, https://github.com/spine-tools/SpineOpt.jl)
Julia framework for multi-energy systems; GPL-3.0 and LGPL-3.0 are listed and the README states LGPL-3.0 or later; EU
funded project through 2026 per the page; appears maintained. Energy-only; nothing applicable.

### JuMP (OPENED, https://jump.dev/JuMP.jl/stable/manual/solutions/)
Julia modelling language for mathematical optimisation. Its manual states how dual values are read (`dual`,
`shadow_price`, `reduced_cost`) and notes that duals are available only if the solver returns them. Licence not stated on
the page I opened. Julia, so not a dependency candidate; useful as the statement of what a dual is.

---

## Follow-up pass: the owner-supplied links

The owner's links came from a third party. Each was opened and checked against what it was said to be. Verdicts:
OK means it is what was claimed; WRONG means it is a different work; BROKEN means it did not load for me (which does not
show the page is gone).

### Verdicts on the doubtful items

- **Pichler and Farmer, "Simultaneous supply and demand constraints in input-output networks".** The IDEAS link
  (https://ideas.repec.org/p/arx/papers/2104.07260.html) is WRONG for that claim. It is the entry for "Quantifying firm-level
  economic systemic risk from nation-wide supply networks" by Diem, Borsos, Reisch, Kertesz and Thurner (OPENED (follow-up);
  it shows a 2021 arXiv preprint). The correct Pichler and Farmer reference is arXiv 2101.07818, "Simultaneous supply and
  demand constraints in input-output networks: The case of Covid-19 in Germany, Italy, and Spain", Anton Pichler and J. Doyne
  Farmer, econ.GN, first submitted 19 January 2021, revised 5 May 2021 (OPENED (follow-up), https://arxiv.org/abs/2101.07818).
  The abstract page lists no journal; a search summary gives Economic Systems Research 2022, volume 34, pages 273 to 293
  (SNIPPET ONLY).
- **Diem et al. 2022 and arXiv 2104.07260.** The id 2104.07260 is correct for Diem et al., but the title the note gave
  ("Firm-level production networks") is WRONG. The arXiv HTML page (https://arxiv.org/html/2104.07260v1, OPENED
  (follow-up), first 100000 of 177121 characters read) is "Quantifying firm-level economic systemic risk from nation-wide
  supply networks". The journal version, Scientific Reports 2022, volume 12, article 7719 (SNIPPET ONLY, search summary
  pointing to https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9092945/), carries the same title. So the IDEAS entry and the
  Diem et al. paper are one work; there is no second paper behind the shared id.
- **Bacilieri et al.** The PDF link (https://oms-inet.files.svdcdn.com/production/files/Firm-level-production-networks-what-do-we-really-know.pdf)
  is OK: "Firm-level production networks: what do we (really) know?", Andrea Bacilieri, Andras Borsos, Pablo
  Astudillo-Estevez and Francois Lafond, INET Oxford Working Paper No. 2023-08, May 2023 (OPENED (PDF), first page). It is the
  paper whose title the note attached to Diem et al. Abstract: it benchmarks two administrative datasets without a reporting
  threshold (Ecuador, Hungary) against a commercial dataset and finds the threshold-free ones alike in their network
  properties.
- **arXiv 2607.09745.** Exists: SupplyNetPy, "An Open-Source Python Library for High-Fidelity Modeling and Simulation of
  Arbitrary Supply Chain and Inventory Networks", Tushar Lone and Neha Karanjkar, IIT Goa (OPENED (follow-up),
  https://arxiv.org/html/2607.09745v1).
- **arXiv 2607.23313.** Exists but is NOT "OpenCGE / OG-Core": it is "Agentic AI orchestration of heterogeneous economic
  models for rapid, multi-scenario analysis of energy crises", Golden, Indelicato, Varshney, Messina and Thornsbury (OPENED
  (follow-up), https://arxiv.org/html/2607.23313v1). It lists OpenCGE (OG-Core / OG-USA, Python, overlapping-generations CGE)
  and MPSGE.jl among many wrapped models; it is a language-model workflow around other models, not a CGE source. The paper
  names no licence for OG-Core.
- **ACCEPTS, ColonD, HABITAT.** I was given the owner's links but not the owner's note text, so I cannot tell which link
  replaced which name. No link I opened is called ACCEPTS, ColonD or HABITAT, and a further search for ACCEPTS (SNIPPET
  ONLY) again found no model of that name. The three names stay unidentified. Any substitute is listed on its own below;
  none is recorded as an identification.
- **Gill, Lalith, Poledna, Ichimura 2021.** Page found: the dblp record
  https://dblp1.uni-trier.de/rec/journals/tpds/GillLPHFI21.html and the IIASA record https://pure.iiasa.ac.at/17104 (the
  IIASA page was BROKEN to me, bot protection; both are SNIPPET ONLY via a search summary). The summary gives the title
  "High-Performance Computing Implementations of Agent-Based Economic Models for Realizing 1:1 Scale Simulations of Large
  Economies", IEEE Transactions on Parallel and Distributed Systems, volume 32, number 8, pages 2101 to 2114, 2021, DOI
  10.1109/TPDS.2021.3060462, authors Amit Gill, Madegedara Lalith, Sebastian Poledna, Muneo Hori, Kohei Fujita and Tsuyoshi
  Ichimura (the note lists four authors; the summary lists six). I did not read the paper. Its subject is parallel
  computing speed, so nothing applicable.

### Link-by-link status

| Link | Verdict | What it is |
|---|---|---|
| github.com/spjuhel/BoARIO | OK | Python ARIO implementation, GPL-3.0 |
| spjuhel.github.io/BoARIO/ | OK | Its documentation; front page does not mention rationing or prices; JOSS paper cited |
| arxiv.org/html/2607.09745v1 | OK | SupplyNetPy (above) |
| arxiv.org/html/2104.07260v1 | OK, title in note wrong | Diem et al. |
| ideas.repec.org .../2104.07260 | WRONG for Pichler and Farmer | Diem et al. |
| oms-inet ... Firm-level-production-networks PDF | OK | Bacilieri et al. 2023 |
| github.com/iiasa/message_ix | OK | MESSAGEix |
| github.com/s120/jmab, S120/benchmark | OK | JMAB and its Benchmark model |
| Sylvain-Barde/begrs_sfc | OK, different thing | Replication files for estimating the Benchmark model's parameters (BEGRS) |
| sites.google.com/.../java-macro-ab-simulation-toolkit | OK | JMAB toolkit page |
| github.com/phelps-sg/jabm | OK | JABM, the Java framework JMAB runs on |
| arxiv.org/abs/1307.5319 | OK | "Tipping points in macroeconomic Agent-Based models" |
| github.com/KarlNaumann/Mark0 | OK | Mark-0 interface |
| github.com/bancaditalia/BeforeIT.jl | OK | BeforeIT.jl |
| researchgate ... 389167105 | BROKEN (403) | Title confirmed instead through arXiv 2502.13267, which I opened |
| pure.iiasa.ac.at/id/eprint/16268/1/WP-20-001.pdf | OK (PDF) | Working paper version of Poledna et al. |
| ideas.repec.org .../v151y2023ics0014292122001891.html | OK | Journal version, European Economic Review 151 (2023) |
| wifo.ac.at ... abm_slides.pdf | OK (PDF) | Slides by Poledna and Kaniovski, WIFO, 5 February 2026 |
| gitlab.com/dlr-ve/esy/sfctools/framework | OK | sfctools |
| sfc-models.net/tag/python/ | OK, only a blog | Network site; posts on sfctools, Romanchuk and Takara Python SFC code |
| github.com/AB-CE/abce, github.com/AB-CE | OK | abcEconomics, archived |
| abce.readthedocs.io ... 0.9.3b2/pdf | OK (PDF) | Manual; front page says release 0.9.3b0, 5 July 2019 |
| github.com/marcov64/Lsd | OK | LSD |
| researchgate ... 227359745 (K+S) | BROKEN (403) | Not read |
| ews.santannapisa.it | OK | Sant'Anna models page |
| pypi.org/project/bamengine/ | OK | BAM engine, Python |
| jasss.org/24/1/3.html | OK, different thing | An extortion model built on BAM (BAMERS), not CATS or BAM itself |
| docs.pypsa.org/latest/examples/example-2/ | OK | PyPSA three-zone example |
| github.com/spine-tools/SpineOpt.jl | OK | SpineOpt |
| julia-mpsge.github.io/MPSGE.jl/ | OK (redirects) | MPSGE.jl docs, read through the `/dev/` page |
| financeministersforclimate.org ... CFCMA HP4 PDF | BROKEN (403, 503) | Not read |
| github.com/gama-platform/gama, gama-platform-plugins | OK | GAMA and its plugin organisation |
| github.com/salesforce/ai-economist | OK | AI Economist (Foundation), archived |
| coegss.eu .../D3.4.pdf | OK, but only cites Lagom | CoeGSS deliverable D3.4 |
| research.tudelft.nl .../Navigating_complexity... | BROKEN (403) | Not read |

### Per-item notes (new or changed)

Each: what it is, language, licence, maintained, mechanism tied to a problem, or "nothing applicable".

**BoARIO** (OPENED (follow-up), https://github.com/spjuhel/BoARIO and https://spjuhel.github.io/BoARIO/). Python, GPL-3.0;
the repository page shows seventeen open issues but no commit or release date, and the documentation footer says "Last
updated on Oct 29, 2026" (a page build date). The front page does not mention rationing or prices. The mechanisms in the
main section above stay as read earlier from the maths page. No change.

**Pichler and Farmer** (OPENED (follow-up), https://arxiv.org/abs/2101.07818). Paper; no code on the abstract page. The abstract
says the impact of a supply and demand shock depends heavily on the rationing rule applied when an industry cannot meet
incoming demand, and that input bottlenecks drive losses. Tie: CLAUDE.md section 5 (a shortage of one input must not
silently stop everything). The page does not list the rules; I did not open the paper body. Supports recommendation 5, as a
reason the rule must be chosen on purpose and tested.

**Diem et al.** (OPENED (follow-up), https://arxiv.org/html/2104.07260v1, partly read). Paper built on Hungarian value-added-tax
data. Its production function treats essential inputs as strictly complementary and non-essential inputs as substitutable,
and propagates a firm's failure down to customers (lost supply) and up to suppliers (lost demand). It argues aggregate
input-output data cannot show this risk. Tie: the bankruptcy-cascade check in the Poledna section below; for the Norse
collapse it points at the failure path (a producer that cannot pay removes demand from its suppliers), not at the opening's
sizing. Needs administrative data; nothing applicable as a method to import.

**Bacilieri et al.** Paper about data quality of firm-level networks. Nothing applicable.

**SupplyNetPy** (OPENED (follow-up), https://arxiv.org/html/2607.09745v1). Python on SimPy, MIT per the paper, installable
with pip; maintenance not shown. Discrete-event supply-chain simulator. A node that cannot fill an order loses or backorders
the demand, or with a `consume_available` setting uses whatever stock exists; the paper describes no explicit rationing.
Nothing applicable (inventory policy, not an economy).

**MESSAGEix** (OPENED (follow-up), https://github.com/iiasa/message_ix). Confirmed as before: GAMS core with Python and R
interfaces, Apache-2.0, many commits, no dates shown; dual prices are not mentioned on the page. Nothing new.

**JMAB family** (OPENED (follow-up)). JMAB (https://github.com/s120/jmab): Java 6 or later, MIT-style notice, copyright 2016
Caiani and Godin, no dates shown. Benchmark (https://github.com/S120/benchmark): the Benchmark model of Caiani et al. 2016 on
JMAB, same notice. begrs_sfc (https://github.com/Sylvain-Barde/begrs_sfc): MIT, Python scripts plus a Java archive,
replication files for estimating that model's parameters; its README warns the original runs needed GPU and multi-CPU
high-performance nodes. JABM (https://github.com/phelps-sg/jabm): Java framework, copyright 2015 Steve Phelps, no licence in
the captured text. The Caiani toolkit page (https://sites.google.com/view/alessandro-caiani/java-macro-ab-simulation-toolkit)
says JMAB runs on JABM and lists model packages (Benchmark, Inequality and innovation, Interbank) with papers from 2016 to
2018. Nothing applicable beyond what the earlier report took from Caiani et al.; unmaintained by all signs.

**Mark-0** (OPENED (follow-up), https://github.com/KarlNaumann/Mark0). The name exists as code: a repository by Karl
Naumann-Woleske, MIT, the model in C++ with a Python interface; the page credits Gualdi et al. (2015, 2017), Bouchaud et al.
(2018) and Sharma et al. (2020), and shows one commit with no date. This closes the earlier "no source named it". The paper
https://arxiv.org/abs/1307.5319 is "Tipping points in macroeconomic Agent-Based models", Gualdi, Tarzia, Zamponi and
Bouchaud, Journal of Economic Dynamics and Control 50 (2015), pages 29 to 61; it is the Mark I paper, and the abstract does not
use "Mark-0". Mechanism as in the main section: the good-to-bad transition set by the asymmetry between hiring and firing
speed. Reading: relevant to the household help hiring that flipped all-or-nothing, and to the never-settling opening of
Complaint 473. I did not read the model rules.

**Poledna model, BeforeIT.jl and the working paper.** BeforeIT.jl (https://github.com/bancaditalia/BeforeIT.jl, OPENED
(follow-up)): Julia, Apache-2.0, seven open issues, no dates shown. Its software paper, "BeforeIT.jl: High-Performance
Agent-Based Macroeconomics Made Easy", Meligrana et al., arXiv 2502.13267 (OPENED (follow-up),
https://arxiv.org/abs/2502.13267), says the base model runs much faster than the original MATLAB code. The journal paper is
"Economic forecasting with an agent-based model", Poledna, Miess, Hommes and Rabitsch, European Economic Review 151 (2023)
(OPENED (follow-up), https://ideas.repec.org/a/eee/eecrev/v151y2023ics0014292122001891.html). The working paper
https://pure.iiasa.ac.at/id/eprint/16268/1/WP-20-001.pdf is the earlier version, Poledna, Miess and Hommes, IIASA WP-20-001,
17 January 2020 (OPENED (PDF)); I read parts of its appendix A with `pdftotext`. Mechanisms:
(a) Production is the minimum of desired output, intermediate inputs, labour and capital (equation 12); the text says that
when one limits, "the firm has to scale down activity", so a short input cuts output to what that input supports and not to
zero. This is the proportional pattern recommendation 5 asks to test.
(b) Employment: desired employees are desired output over labour productivity, rounded to a whole person, so an additional
need below a half-time position leaves the workforce unchanged and above it hires one person; vacancies are then filled by
search and matching, so a firm can fill some of them and not others. That is a threshold on the demand side with partial fill
on the supply side; I did not read the matching rules (appendix A.2.1), so I cannot say whether it avoids an all-or-nothing flip.
(c) Unsold output goes to an inventory of finished goods, the firm's demand-expectation error.
(d) Appendix C gives the initial conditions for the Austrian economy from national accounts, so the opening is data, not a
solved state.
Nothing here is a fix for the Norse collapse, whose cause was producers sized without a margin check; the sections I read
show no such check. Slides by Poledna and Kaniovski (OPENED (PDF),
https://www.wifo.ac.at/wp-content/uploads/upload-3765/abm_slides.pdf, 5 February 2026): overview of the same model and the
Dawid and Delli Gatti comparison of behavioural rules; nothing beyond the paper.

**sfctools** (OPENED (follow-up), https://gitlab.com/dlr-ve/esy/sfctools/framework). MIT, 499 commits, 5 tags, 2 releases,
project created 25 February 2022; language, last commit and archive status not shown. The blog
https://sfc-models.net/tag/python/ (OPENED (follow-up)) has a July 2023 post introducing it as a Python toolbox for
stock-flow consistent agent-based modelling with a graphical interface, from the German Aerospace Center, with a JOSS paper.
The pages do not describe the balance-sheet checks. Earlier reading stands: a test idea, nothing applicable to a named complaint.

**abcEconomics** (OPENED (follow-up), https://github.com/AB-CE/abce, https://github.com/AB-CE and the manual
https://abce.readthedocs.io/_/downloads/en/0.9.3b2/pdf/). Python, archived 23 January 2024; licence not stated on the
repository page. The manual front page reads "Release 0.9.3b0", Davoud Taghawi-Nejad, 5 July 2019 (the URL says 0.9.3b2; a
mismatch I did not resolve). Its trade text says a buyer with insufficient funds gets a partial accept of an offer. Nothing
applicable.

**K+S and LSD** (OPENED (follow-up), https://github.com/marcov64/Lsd and https://www.ews.santannapisa.it/). LSD: a modelling
environment for difference-equation models, C++ based with Tcl/Tk, GPL; README header "LSD 8.1 - July 2023"; no commit date
shown. The Sant'Anna page hosts K+S and variants (basic, finance, energy, labour, multi-industry) with code links to a
SantAnnaKS/LSD repository, but states the models are the authors' property and may not be copied or distributed without
written agreement: licence NOT open. The ResearchGate K+S link was BROKEN to me. Mechanism and tie as in the main K+S
section; nothing applicable to the opening.

**CATS and BAM** (OPENED (follow-up), https://pypi.org/project/bamengine/). `bamengine` 0.10.2, released 9 July 2026, Python
3.11 or later, MIT, one maintainer, "4 - Beta", numpy-array state; baseline BAM (labour, credit, goods markets) plus
extensions. The page does not describe rationing or hiring rules. The JASSS link (https://www.jasss.org/24/1/3.html) is NOT
CATS or BAM but "On the Macroeconomic Effect of Extortion: An Agent-Based Approach" (Platas-Lopez, Guerra-Hernandez,
Grimaldo, 2021), which extends BAM and has an ODD description of baseline BAM in its appendix (I did not read the last
4,789 characters of the page, nor the ODD). A numpy implementation is the most stack-compatible code surveyed and a
possible cross-check for a hire-and-fire rule; no code was run.

**PyPSA marginal prices** (OPENED (follow-up), https://docs.pypsa.org/latest/examples/example-2/). Resolves the earlier gap:
after `n.optimize()` the example reads `n.buses_t.marginal_price` per zone and shows the `Bus-nodal_balance` constraint; it
also notes shadow prices for other constraints (generator limits, line capacities) were not assigned to the network. So
PyPSA returns nodal marginal prices for a balance constraint, now verified. Conclusion unchanged (single homogeneous
commodity; recommendation 3 rejects duals as opening prices).

**SpineOpt** (OPENED (follow-up), https://github.com/spine-tools/SpineOpt.jl). Julia; the README says LGPL-3.0 or later (the
page also lists GPL-3.0); a v1.0.0 release is mentioned, no dates shown. Energy-only; nothing applicable.

**CGE** (OPENED (follow-up), https://github.com/julia-mpsge/MPSGE.jl and https://julia-mpsge.github.io/MPSGE.jl/dev/). Julia
implementation of MPSGE, described as a high-level language for CGE models whose original was a FORTRAN subsystem of GAMS;
repository MIT, but the PATH solver is closed source and limited to 300 variables and 2,000 nonzeros without its own licence;
the README says a 1.0.0 release is in preparation. The CFCMA report PDF was BROKEN to me and is not read. The arXiv
2607.23313 paper is not a CGE source (above). Nothing new beyond `ECONOMY_MODEL_SURVEY.md`.

**GAMA** (OPENED (follow-up), https://github.com/gama-platform/gama and https://github.com/gama-platform-plugins). Java, GPL-3.0,
described as the main repository for 2025 and later versions; the plugin organisation shows updates through 30 October 2026.
Nothing applicable.

**AI Economist, Foundation** (OPENED (follow-up), https://github.com/salesforce/ai-economist). Python 3.7 or later,
BSD-3-Clause, ARCHIVED by its owner on 6 November 2023 (read-only). Gym-style `reset` and `step`, components and scenarios,
a social planner agent, mobile worker agents with labour as an entity, for learning policy by reinforcement learning. Trade is
not described on the page. Nothing applicable to the named problems.

**Lagom generiC** (https://coegss.eu/wp-content/uploads/2018/11/D3.4.pdf, OPENED (PDF)). The deliverable is CoeGSS D3.4, dated
30 June 2018, about domain-specific languages and high-performance computing for synthetic information systems; Lagom
generiC appears only as a reference ("Lagom generiC: an agent-based model of growing economies", ECF Working Paper 1, 2009).
The TU Delft link was BROKEN (403). So no new information on the model; language and licence remain NO SOURCE FOUND.

### Substitutes

The note replaced ACCEPTS, ColonD and HABITAT with other models. Which links are the substitutes was not stated to me.
They are recorded above as entries in their own right and the three original names stay unidentified.

The owner later quoted the article the three names came from. It uses each name only as a label in a table or a
sentence, beside a description: "ColonD / Firm-Level Production Network ABMs" (firm-as-node models with physical inputs
and outputs, attributed to the Santa Fe Institute and the Complexity Science Hub Vienna); "ACCEPTS / ARIO" (an
input-output agent network for supply-chain shocks); "HABITAT / IIASA Models (MESSAGEix)". The article gives no link,
author or paper for the three names themselves. Reading (not a sourced claim): they look like labels the article's
author attached to the families it describes, not names of separate models, so the entries for the firm-level network
papers, BoARIO and MESSAGEix cover what the article meant and no further search is planned.

---

## Evaluation of the proposed architecture

The proposal has three parts: (1) a spatial input-output hypergraph of physical recipe vectors, location nodes with
endowments and transport edges; (2) before agents trade, a linear or convex feasibility and shadow-price pass whose
duals give each commodity's marginal value at each node as the starting economy; (3) dynamic shocks on top (a new recipe or
mine, a gold injection with stock-flow consistency and mass balance, a Cantillon effect along trade routes). It also
claims Eurace@Unibi hardcodes modern sectors.

### What the repo already has (measured)

| Proposal part | In the repo | Evidence |
|---|---|---|
| Recipe vectors | Yes. Each production method has inputs, outputs, labour hours by trade, heat, work, plant goods and life, yields | `data/production/_SCHEMA.md` (fields table); `data/production/*.json` |
| Joint production, rents, technique choice | Yes, in the solver | `sim/prices/solve_prices.py`; `docs/architecture/ECONOMY_MODEL_SURVEY.md` section 1 |
| Nodes with endowments | Yes. Tiles with soils, climate, deposits and a provisions layer | `sim/geography/` (resources_endowment.py, food_land.py and others) |
| Transport edges with distance and terrain | Yes. Freight cost from a carrier's feed, crew, capital and return leg, per tonne-km, by mode | `sim/geography/freight_cost.py`, `cargo_cost.py`, `carriage_reach.py` |
| A stationary input-output pass over final demand by tile | Yes. `opening_runs.choose_recipes` solves the runs that meet final demand (x equals matrix times x plus demand) and ranks recipes by cost, and `opening_stationary.solve` returns runs, hours by trade, wage bill and incomes | `sim/economy/opening_runs.py`, `sim/economy/opening_stationary.py` (module docstring); called from `sim/economy/opening.py` around lines 105 to 134 |
| Cost-price dual | Yes, as cost-of-making fixed point | `sim/economy/unit_cost.py` (named in the stationary module docstring), `sim/prices/` |
| Shocks that reallocate capital and bankrupt producers | Yes, as agent-economy rules: entry and exit on expected sales and loss years, investment | `Complaints/473` line about `LOSS_YEARS_BEFORE_EXIT`; `sim/economy/producers_close.py` |
| Money injection raising prices | Partly. A coin-metal money with mint and a price-level test existed ("more metal raises the price level"), now drowned by the unsettled economy | `Complaints/473` Finding, and the restored slow-only baseline validation naming 473 |

### What it lacks

1. **A global feasibility or shadow-price pass over the spatial network.** `opening_runs.choose_recipes` handles the
   recipe system by an input-output solve and ranking with ceilings, but trade between tiles is not solved jointly as a
   network problem: no transport-aware linear programme returns a marginal value of each good at each tile (the route
   prices are applied afterwards by carriers and merchants). I measured this by reading the module docstrings, not by
   running anything; `grep -rn "linprog\|scipy" sim --include=*.py` finds scipy only in the map layer build
   (`sim/geography/layer_build/sea_links.py`: ndimage and graph routines) and no linear-programme call; `requirements.txt` lists numpy only.
2. **A dependency for linear programmes.** None. Adding one is an owner decision.
3. **Spatial Cantillon spreading as an explicit check.** There is a price-level test, but no test that a gold
   injection at one tile raises prices there before it raises them elsewhere.

### Where the proposal conflicts with CLAUDE.md or the 507 decision

- **507 (one price owner).** `Complaints/507` and `docs/architecture/ONE_PRICE_OWNER_PLAN.md` decide that the agent economy
  owns prices and traded volumes and the solver is a cost-of-making calculator, "used for entry decisions, quotes and the
  opening's seed prices". Part (2) of the proposal makes a solver's duals the starting economy. Whether that conflicts depends
  on one word: the plan already allows the calculator to seed the opening, but the plan's stage 2 seeds with the
  *cost of making at the economy's own wages*, which is a cost-price dual of a system without a demand side. A shadow price
  from a feasibility pass with scarce endowments and fixed final demand is a *scarcity* price, which includes a demand-side
  rent. That is exactly the "demand" job the plan removes from the solver (the plan's section 1, jobs 2 and 3: demand and rent).
  So a shadow-price pass as the source of opening prices re-creates the second price owner; it is the very seam
  507 closes. As a seed that the agent economy then overwrites in the first trading round, it is tolerable only if
  nothing reads it afterwards.
- **"Calculated, not looked up" (CLAUDE.md 4.5).** Shadow prices are calculated, from physical vectors, endowments and a
  stated final demand, so they pass the letter of 4.5. Two cautions. The final demand that feeds them must itself be a
  derived basket (the repo's `opening_basket`) or the dual inherits a looked-up input. And the marginal value of a good that
  is in surplus is zero, which CLAUDE.md section 5 forbids as an in-band "none"; the pass would return a price of "no
  scarcity" that a caller must read as `None`, not free.
- **4.1 and 4.2.** A solved optimum is a planner's equilibrium. Using it as the opening's starting price biases the baseline
  toward a market-clearing outcome, which is the cobweb problem of Complaint 473 in reverse (the opening would be too settled
  to show the real instability the agent economy produces). Section 4.2 says the real trajectory should be a plausible
  draw from an ensemble, and a deterministic dual always lies in one point.
- **4.7.** No conflict: recipes and tiles are data.
- **Dependency and size rules.** Julia (JuMP, BeforeIT.jl, MPSGE.jl) and the energy frameworks (PyPSA, Calliope, SpineOpt)
  are outside the project's Python-with-numpy stack; none of them represents hundreds of goods with joint production
  and per-tile endowments.

### The Eurace claim, checked against the clone

Clone: `/tmp/claude-0/-home-user-bootstrap-history/5d7f8e03-7271-5935-85ab-84cd283dc951/scratchpad/eurace`.
Commands run there:

- `grep -rn -i -E 'sector|industr|good_type|goods_type|homogeneous|single (type|good)' --include=*.xml --include=*.md --include=*.c --include=*.h .`
  (excluding unit tests and the public-sector role names) returned no list of sectors or goods.
- The model definition files list agent types (consumption goods firms, an investment goods firm, banks, central bank,
  government, a clearing house, malls, households) and the variable list for malls describes one offered good per firm
  with price and quality (`Cons_Goods/model.xml` line 154). The earlier report, section 2, lists the same agent types.

Reading: Eurace does not hardcode modern sectors; it has no sectors. It has one consumption good, differentiated by firm
through price and quality, and one capital good in vintages that differ in productivity. That is an economy too thin to have
a recipe graph at all, which is why this repo ported the rules (market protocols, rationing, wage and price rules) and not the
goods. The claim as stated is not supported by the clone. The thin good space is a limitation for the founder scenario, not a
set of modern sectors baked in.

### Could a feasibility pass serve as a check, not a price source

Yes, and this is the version I would recommend. Use the linear programme only to answer feasibility questions and discard
its duals as prices:

1. **Run-pays test.** For the opening's chosen runs and producers, check that at the economy's own seed prices and wages every
   chosen recipe covers its input cost, plant wear and wages, and that the sum of runs does not exceed a site ceiling. The
   opening already computes `StationaryFlows.profit` and `sales_value` against `wage_bill` and `input_cost`; a per-recipe
   (not just in total) negative-margin report would catch the case where an opening sizes producers whose runs cannot
   pay. The Norse spin-up collapse this week is the motivating case (I have not reproduced it; I read only the commit log
   and `Complaints/473`; `python3 sim/simulator.py spin-up-trace --civ norse_900ad --years 7` is the measure that
   exists). A repo-native version needs no new solver: it is a loop over `opening_stationary.solve` output.
2. **Mass-balance and endowment feasibility.** Check that the final demand is producible from tile endowments and the
   freight network (a feasibility linear programme with zero objective). A phase-one infeasibility certificate names which good
   or tile binds. This is the part that needs a solver dependency.
3. **Shock regression tests.** After a shock (a mine opens, gold arrives), check mass balance and stock-flow consistency
   as invariants of the agent economy. This is the useful part of sfctools and BoARIO's pattern, as a test.

A check that returns pass or fail with a `cause` fits CLAUDE.md section 6's "a refusal's `cause`" and does not create a
second price owner.

---

## Recommendation (one line each, for possible later complaints)

1. **Opening run-pays check.** Add a per-recipe report, in the opening validation, of producers whose planned runs cannot
   pay input cost, plant wear and wages at the seed prices; the check, not a solver, is the fix for sizing producers that
   cannot pay (reads `opening_stationary.solve`; no new dependency; link Complaint 473).
2. **Feasibility check as a test, not a price source.** If the owner accepts a linear-programme dependency, use it to prove
   a stated final demand is producible over the tile network and to name the binding good or tile; discard its duals.
3. **Reject shadow prices as opening prices.** Record in `ONE_PRICE_OWNER_PLAN.md` that a scarcity dual is a second price
   owner (507) and biases the baseline toward equilibrium (4.2); keep the cost-of-making calculator as the only seed.
4. **Spatial Cantillon test.** Add a slow-tier relationship test that a gold injection at one tile raises local prices
   before distant ones, along route cost, once the spin-up settles (blocked by Complaint 473).
5. **Proportional rationing with input buffers.** Check, against BoARIO's rule, that an input shortage cuts a recipe's runs
   by the share it is short and not to zero (CLAUDE.md section 5); a rule test on the settlement function. Follow-up: two
   further sources agree on the pattern (output is the minimum over inputs and a short one scales activity down, Poledna
   et al. working paper equation 12; the rationing rule is a main driver of losses, Pichler and Farmer abstract), so the
   rule must be chosen on purpose and tested.
6. **Phase-diagram method for the opening.** Use the Gualdi et al. approach (map the economy's behaviour over the hiring
   and firing asymmetry parameters) to show where the opening sits relative to the good-to-bad transition; this is
   analysis for Complaint 473, not an engine feature. Follow-up: a Mark-0 code base exists (C++ with a Python interface,
   MIT, https://github.com/KarlNaumann/Mark0), usable as a reference to compare against, not as a dependency.
7. **Drop the Eurace claim.** The clone has no sectors; no complaint, but the thin good space deserves a note in
   `NOTICE.md` or the economy architecture docs.

Follow-up change: no recommendation was added or dropped; items 5 and 6 gained sources as marked. The new material gave no
mechanism for the Norse collapse beyond item 1, nor for the all-or-nothing household help hiring (the Poledna working
paper rounds labour demand to whole workers with partial vacancy filling, but its matching rules were not read).

Nothing else surveyed deserves a complaint: the Julia and energy frameworks (BeforeIT.jl, Agents.jl, JuMP, PyPSA,
Calliope, SpineOpt, MESSAGEix), the Python frameworks (AgentPy, Mesa, GAMA, abcEconomics) and the CGE family offer
nothing the repo lacks that fits its stack and its rules.

## Models I could not open or identify

- ACCEPTS: NO SOURCE FOUND (two searches in the first pass, one more in the follow-up).
- ColonD: NO SOURCE FOUND.
- HABITAT (IIASA): NO SOURCE FOUND.
- Substitutes for the three names were supplied by the owner but not mapped to them; they are not identifications.
- JMAB 2.0: no repository found; JMAB (version not shown) is the Java toolkit, opened.
- Links BROKEN to me (403 or 503, not read): the ResearchGate pages for the K+S paper and BeforeIT.jl, the IIASA record
  17104 (Gill et al. 2021), the finance-ministers CFCMA report, the TU Delft Lagom document.
- Not opened (snippet only): Gill et al. 2021 paper itself, GTAP, GEMPACK, Envisage, Lengnick-style CATS code, the
  Economic Systems Research and Scientific Reports journal versions.
- Opened but no usable model description on the page: Lagom generiC (only a citation), the Bacilieri et al. paper (data quality).
- The earlier report's HARK, Eurace and Caiani sources remain the only fully read ones for the agent-based design.
