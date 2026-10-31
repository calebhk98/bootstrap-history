# Labour-market models surveyed for the bootstrapping simulator

Research report, no code changed. It builds on `Complaints/reports/research-reference-economy-models.md`,
`research-agent-based-economy-design.md` and `research-alternative-economic-models.md` and does not repeat them.

## Sourcing key

- OPENED: fetched in this session; the URL is given. A fetch returns a summary produced by a small model, so "page does
  not say" means the summary did not show it.
- SNIPPET ONLY: seen only in a web search result summary; unverified.
- NO SOURCE FOUND: looked, found nothing.
- "Reading" marks my inference, not a claim by the source.
- Nothing here is recalled from memory. Repository dates were mostly not shown by the pages; "maintained" is a reading.
- The owner's list came from a third party. The verdict on each link is in the section for the model.

## 1. del Rio-Chanona and colleagues, occupational mobility network

- Link check: RIGHT, with a correction. The repository exists:
  https://github.com/RMariaDelRioChanona/CanadaLaborApplication (OPENED). It is a Canadian application (regions, demand
  scenarios) of the 2020 model, Python 3.12 with PyTorch per its README, 103 commits, no archive notice, one star. Licence is
  inconsistent on the page: the sidebar says CC-BY-4.0, the README says CC-BY-NC 4.0; read the LICENSE file before any reuse.
  The original paper code is a Zenodo record (OPENED, https://zenodo.org/record/4453162): Python 3.8 and Julia 1.0.4,
  CC BY 4.0, published December 2020, with the adjacency matrix and an agent model; an archive, not maintained.
- Paper: "Automation and occupational mobility: A data-driven network model", https://arxiv.org/abs/1906.04086 (OPENED,
  abstract); text at https://ar5iv.arxiv.org/html/1906.04086 (OPENED, first part only).
- Mechanism (OPENED, ar5iv): each unemployed worker sends one application a step. The chance it goes to occupation j is
  proportional to open vacancies in j times a fixed network weight from the worker's occupation to j. Matching is an urn: each
  vacancy hires one applicant drawn uniformly; vacancies without an applicant stay open. The network is built from observed
  worker transitions in a US survey panel, not from skill or task similarity. A self weight is calibrated so most workers stay
  in their occupation each year. Wages are not modelled; the authors say they neglect wage pressure.
- Compared with ours: our workforce forms by training (`sim/labour/market/training.py`, teacher cap in
  `sim/labour/market/DESIGN.md`) and the entrant logit (`entrants.py`); movement between trades follows the `taught_from`
  links in `data/world/trades.json` plus training years. Their graph is empirical and fixed; ours is structural (what a trade
  teaches). A fixed observed graph would hardcode an outcome under CLAUDE.md 4.1 and has no entry for a trade that has never
  existed. Their urn matching with applications weighted by vacancies is a micro-founded alternative to the matching function
  in `clearing.py`; the transferable idea is that applications follow vacancies in places the worker can plausibly go.
- Bearing: 619 (validation against a Beveridge curve and flow correlations is a relationship check, in the spirit of
  CLAUDE.md 4.2). 644: nothing applicable as a table, since an empirical graph cannot hold a new trade; a graph derived from
  `taught_from` could. Wage complaints: nothing applicable, wages are absent.

## 2. WorkSim (Kant, Ballot, Goudet)

- Link check: RIGHT as to the paper: JASSS 2020, volume 23, issue 4, https://www.jasss.org/23/4/4.html (OPENED, first part
  only; the rest was not read). The earlier calibrated version in Computational Economics is SNIPPET ONLY. Java and a "full
  specification" are NOT CONFIRMED: the opened part names no language or licence and says the detailed equations are in its
  appendices A to C. A search for downloadable code found none (SNIPPET ONLY, search listings). Treat as no public code, not
  maintained.
- Mechanism (OPENED): three kinds of human capital: general (useful in all jobs), occupational (one of three levels: employee,
  middle, manager) and firm or job specific (periods in the job, reset on a move). General and occupational capital rise with
  experience and training and decay after periods unemployed or inactive. Weekly periods; a job seeker receives a Poisson
  number of offers, mean depending on tightness, for its occupation level or higher, and takes the first whose utility beats a
  reservation utility. That utility falls with time unemployed (calibrated near a fifth per year) and after each rejection.
  Employers choose the contract type with best expected profit and hire the top candidate only if the score clears a hiring
  norm that falls each period until the job is filled. There is no aggregate matching function.
- Compared with ours: our ask falls by the unsold share, with Eurace's per-round cut compounded
  (`moved_scale` in `sim/labour/market/asks.py`), and floors at the plot return (`sim/economy/labour_ask_floor.py`). Their
  reservation utility also decays with unemployment, so the shape agrees; theirs has no household plot, hence no floor. The
  hiring norm that relaxes while a vacancy stays open mirrors our wage offer rising with unfilled vacancies (`vacancy_raise`
  in `clearing.py`). Their capital decay when idle has no counterpart in `sim/labour/learning_curve.py`.
- Bearing: 678: a relaxing hiring norm is a second way a scarce trade's vacancy resolves besides the wage rising (reading,
  untested). 473: nothing applicable. Their contract institutions are modern French law.

## 3. Labour-augmented K+S (Dosi, Pereira, Roventini, Virgillito and others)

- Link check: https://github.com/marcov64/Lsd (OPENED) is LSD, the modelling environment (C++ equations, Tcl/Tk), GNU GPL,
  version 8.1 of July 2023 per its readme, 1,364 commits, not archived, last commit date not shown. It is the platform. From
  the pages opened I could not confirm that it holds a labour-augmented K+S model: NOT CONFIRMED.
- Papers: "When more flexibility yields more fragility", Journal of Economic Dynamics and Control 2017, abstract at
  https://ideas.repec.org/a/eee/dyncon/v81y2017icp162-186.html (OPENED): two labour governance regimes defined by wage
  determination, firing, labour protection and productivity-gains sharing; rigid regimes coordinate better. The page does not
  mention unions and not code. The deunionisation paper, https://ideas.repec.org/p/fce/doctra/2005.html (OPENED, abstract):
  deunionisation as an outcome of competition between firms; no bargaining mechanism or code shown. Full texts were not
  opened (one source returned an access-denied page), so union bargaining details are NOT SOURCED.
- Compared with ours: we have no bargaining; employers bid up to a maximum wage and workers ask (`clearing.py`). The
  paper's point, that the wage-setting regime changes aggregate stability, needs demand feedback.
- Bearing: nothing applicable to the open labour complaints at the level I could verify. For multiplayer, a wage-setting
  regime as data (who bargains, how gains are shared) would let a state or guild act without a civilisation branch; that is a
  design idea of mine, not a sourced mechanism.

## 4. JAS-mine and LABSim

- Link check: https://github.com/jasmineRepo/LABSim exists (OPENED): life-course microsimulation of individuals and households
  embedding the EUROMOD tax-benefit model; authors Richiardi, Bronka, Richardson, van De Ven; Italy and UK branches; input data
  not included; 7 commits on main. Language and licence not shown for LABSim. The organisation page
  (https://github.com/jasmineRepo, OPENED) shows LABSim last updated February 2023 and JAS-mine-core as Java, EUPL-1.2, updated
  in 2026, so the platform is maintained and LABSim looks dormant (reading).
- Mechanism (OPENED): labour supply runs last each period. Potential wage from a Heckman-corrected wage equation; net income
  from the nearest-matching EUROMOD household; hours from a utility-maximising structural labour supply model estimated on the
  tax-benefit input data. Students and the long-term sick do not enter.
- Compared with ours: ours offers every hour left after the plot and household work leave (`sim/economy/labour_supply.py`,
  `LabourOffer`), with the plot-return floor. Theirs chooses hours by utility over income and leisure. The shape is better
  (hours respond to the wage and the outside option) but the parameters are estimated on modern data, so importing them would
  hardcode modern behaviour (CLAUDE.md 4.1).
- Bearing: 556: LABSim gives labour supply one module with one owner, ordered last. 645: it models market work only, so
  nothing applicable on household help.

## 5. QuantEcon search and matching

- Link check: PARTLY RIGHT. QuantEcon.py is MIT licensed, Python, active CI, Sloan-funded
  (https://github.com/QuantEcon/QuantEcon.py, OPENED; the page does not mention JAX). The lecture index
  (https://python.quantecon.org/intro.html, OPENED) lists nine job search lectures (McCall; with separation; Markov wages;
  fitted value iteration; risk; persistent and transitory shocks; career choice; on-the-job search; learning), a Q-learning one
  and Lake model lectures. The McCall lecture (https://python.quantecon.org/mccall_model.html, OPENED) uses Python with JAX;
  text CC BY-SA 4.0. DMP and Gale-Shapley: NOT FOUND on QuantEcon; the index lists neither and the Julia site fetch returned
  empty.
- Mechanism (OPENED): the reservation wage is (1 minus discount factor) times (unemployment compensation plus discount factor
  times the expected best of an offer and waiting); it depends on the discount factor, compensation and the offer
  distribution. The page never says "outside option"; compensation is the closest thing (reading). Career lecture
  (https://python.quantecon.org/career.html, OPENED): wage is career plus job, each redrawn at random; a career change needs a
  new job; no explicit switching cost.
- Compared with ours: our reservation wage is subsistence plus a fatality premium (`reservation_wage` in
  `sim/labour/market/clearing.py`) and the ask drifts by the unsold share, bounded below by the plot return (`asks.py`). The
  plot return is the right reading of McCall's compensation. What ours lacks is the value of waiting: a worker's ask does not
  depend on how likely a sale is or how offers are spread.
- Bearing: 608: a McCall ask is anchored by the offer distribution, whereas ours is bounded only by the plot floor. 678: the
  on-the-job search lecture is the worker's side of `poach` in `clearing.py`. Matching friction in McCall is an arrival rate;
  ours is searchers per vacancy, the same role.

## Comparison with our labour market

| Question | Ours | Surveyed models |
|---|---|---|
| Outside option and reservation wage | cost of living plus risk; ask floors at plot return | benefit plus value of waiting (McCall); utility decaying with unemployment (WorkSim) |
| How a workforce forms and moves | training, teacher cap, entrant logit, `taught_from` | fixed empirical transition graph (network model); capital tiers with decay (WorkSim) |
| Matching friction | matching function of searchers per vacancy | urn weighted by vacancies (network); Poisson offers by tightness (WorkSim); arrival rate (McCall) |
| Household hours | all hours offered after plot and leave | utility-maximising hours from an estimated model (LABSim) |
| Wage setting | clearing; stayers keep contract wages | regime as data (K+S, not verified in detail) |

## Recommendations (each a candidate complaint)

1. Make the ask depend on the chance of a sale, a McCall-style continuation value from last year's sold share, with the plot return as the benefit; serves 608 and the unsold-hours Norse spin-up.
2. Let a scarce trade's long-unfilled vacancy relax its hiring requirement (a lesser-skilled worker at a training discount) as a second channel beside the wage; serves 678.
3. Weight a displaced worker's applications by vacancies in trades reachable through `taught_from` and training years, a graph derived from what trades teach and never an empirical table; serves 619 and 644.
4. Add skill decay for trained workers idle for years in `sim/labour/learning_curve.py`, so an unsold trade loses its workforce physically; serves 619 and 473.
5. Give households an hours choice from the wage against the home value of an hour, in one owner module, replacing the all-hours offer; serves 556 and 645.
6. Add a baseline relationship check for the occupational distribution (shares and flows, not dated outcomes); serves 619.
7. Record that an empirical transition graph, estimated utility parameters and fixed wage-regime tables are rejected under 4.1, so later agents do not import them; serves 619.
