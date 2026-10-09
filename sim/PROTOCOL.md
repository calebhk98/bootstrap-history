# The protocol, and why it is shaped like this

This was the module docstring, which meant it was also the whole of
`simulator.py --help`: five and a half kilobytes of design essay in front of
anyone who typed the most reflexive command there is. It is worth keeping and
it was in the wrong place.

---


## What it is

Three things at once, as requested:
  * a RECORD    : `validate`, `costs`, `path` dump the tree and its economics
  * a TOOL      : `run` Monte-Carlos a strategy and tells you where it breaks
  * a GAME      : `play` steps you through it year by year, and `agent` lets a
                  script or an AI play it instead of a person at a keyboard

No third-party dependencies. Python 3.8+.

    python3 sim/simulator.py validate
    python3 sim/simulator.py path junction_transistor
    python3 sim/simulator.py costs --top 25
    python3 sim/simulator.py run --strategy recommended --mc 400
    python3 sim/simulator.py run --strategy recommended --no-events   # silences only the dated weather/plague/political hazards, not a noise-free run
    python3 sim/simulator.py run --strategy recommended --deterministic  # every roll fixed; this is the noise-free run
    python3 sim/simulator.py compare --mc 400
    python3 sim/simulator.py play --strategy recommended
    python3 sim/simulator.py play --manual                            # real free choice, no autopilot
    python3 sim/simulator.py agent                                    # JSON protocol, see below

MACHINE-PLAYABLE INTERFACE (`agent`, and `play --manual`)
-----------------------------------------------------------------------------
`play` used to be a demonstration, not a game: typing a node id only moved it
to the front of the OPTIMIZER's own ordering, and the optimizer (step() 4b)
went on starting whatever else it wanted that year regardless. There was no
way to make a choice and live with only that choice's consequences, and
nothing but a human typing into input() could drive it at all.

Two fixes, usable separately or together:

  --manual (on `play`, and always-on inside `agent`)
      Switches off step() 4b, the optimizer's auto-start loop, entirely.
      Nothing becomes active except what start_project() was explicitly told
      to start. Money, materials, staff, hazards and the calendar all still
      proceed on their own; only the research CHOICE stops being automatic.
      A player who starts nothing makes no progress. That is correct.

  `agent`  a line-oriented JSON protocol, for a script or an LLM
      Reads one JSON command per line from stdin and writes one JSON object
      per line to stdout (or, with --script FILE, reads a JSON list of the
      same command objects from a file and plays them in order). Every
      response is exactly one line of valid JSON; a failed command comes back
      as {"ok": false, "error": "..."} explaining what to do instead, never a
      stack trace or a bare False.

      {"cmd":"state"}                              current situation, in full
      {"cmd":"available"}                          every node that can legally start now,
                                                    with cost, founder hours, calendar
                                                    floor, prerequisites and its note;
                                                    each row says on_road_to_goal (yes or
                                                    no, never a distance) and
                                                    is_supply_or_capability; a row `start`
                                                    would refuse carries cannot_pay_now, and
                                                    the subjects table's you_could_pay_for
                                                    counts what `start` accepts
      {"cmd":"available","state":"blocked","tag":"mechanical_power"}
                                                   filters: state is startable (default),
                                                    blocked, active or done; tag is a
                                                    topic, category a node category; find
                                                    also matches stems and topic words,
                                                    never a knowledge-file name; a
                                                    subject that is not a subject
                                                    heading is searched as find; limit
                                                    beats all; a find reply carries
                                                    "how_matched"; an offset past the
                                                    end says so in "nothing_matched".
                                                    Non-startable states reply with
                                                    "rows" (id, name, tags, why_not,
                                                    missing); an empty search adds
                                                    "try_instead". Fog limits every list
                                                    to nodes the player has heard of.
      {"cmd":"why","id":"zinc_metal"}              the full explanation for one node:
                                                    cost, staff, risk, chain, what it
                                                    unlocks, why it is or isn't startable.
                                                    A blocked node carries blocked_kind and
                                                    blockers, a list of {kind, text, ids}
                                                    (kinds: knowledge, power, supply,
                                                    specialists, money, politics, closed);
                                                    the start refusal is the first entry.
                                                    standing_effect gives the reputation and
                                                    scandal finishing it adds; hazard_effect,
                                                    when it softens a hazard ahead, lists
                                                    {name, kind, years, now, with_it}, the
                                                    same figures `risk` prints.
                                                    earliest_completion_years and
                                                    earliest_completion_year are the
                                                    soonest finish with no failure;
                                                    compact adds blocked_kinds and puts
                                                    the supply options in blocked_by.
                                                    The heard-of rows of `available`, and
                                                    the rows of path and stuck, carry kind (stuck
                                                    also uses calendar and idle; each_kind
                                                    labels each project in hand). `labour`
                                                    carries "workforce": single-person
                                                    dependencies, expected yearly losses,
                                                    reserve and training.
      {"cmd":"path","id":"zinc_metal"}             everything still undone on the way
                                                    to this node, in dependency order
      {"cmd":"start","id":"zinc_metal","precaution":true}  as below, also paying for the
                                                    pilot plant or redundant team `why` quotes
                                                    (pay_to_lower_the_risk), for a lower chance
                                                    of failing
      {"cmd":"start","id":"zinc_metal"}            begin a project (error explains
                                                    exactly what is missing if you can't;
                                                    if it would oversubscribe a hired
                                                    trade your other active work already
                                                    draws on, says so right here, in
                                                    "this_oversubscribes_a_trade" - it
                                                    still starts, this is a warning)
      {"cmd":"stop","id":"zinc_metal"}             abandon a project; sunk cost is sunk
      {"cmd":"programme","action":"set","target":"<goal or category>",
       "max_total_cost":..,"max_annual_draw":..,
       "reserve_cash":..,"max_total_hours":..,       a standing plan: before each year of step it
       "max_annual_hours":..,"pause_debt":..,        starts what the route allows through rush.
       "pause_war_risk":..,"pause_shortage":..,      Hour caps stop starts once the founder hours
       "auto_resume":true}                           it committed reach them. pause_debt (money
      {"cmd":"programme","action":"show"}            owed), pause_war_risk (yearly sack chance, as
      {"cmd":"programme","action":                   risk shows) and pause_shortage (share of
        "pause"|"resume"|"clear"}                    planned work lost) pause it; the step reply's
                                                    "programme" rows say why in
                                                    did_nothing_because. It stays paused until
                                                    resume, or resumes itself with auto_resume.
      {"cmd":"exclude","what":"freedman_staff"}    never let rush, rush preview, auto_open or
      {"cmd":"exclude","what":"trait:buys_people"}  auto_commission begin this id; also
      {"cmd":"exclude","what":"category:<cat>"}     category:<cat> and trait:<trait>. Saved with
      {"cmd":"include","what":"<entry>|all"}        the game; rush and rush preview list what
      {"cmd":"exclude"}                             they left out, with the reason, under
                                                    "excluded". Bare exclude lists the entries.
                                                    `start` by hand is unaffected.
      {"cmd":"figures"}                            the headline figures that explain their own
      {"cmd":"figures","id":"<name>"}               change. With an id (cash, income, upkeep,
      {"cmd":"why","id":"<figure name>"}            recurring_net, population, literacy_general,
                                                    literacy_elite, price_index, hazard):
                                                    {name, label, unit, current, previous,
                                                    previous_year, change, causes:[{cause,
                                                    previous, current, contribution}], drivers:
                                                    [{driver, previous, current}], note}.
                                                    The causes add up to the change; what the
                                                    named parts leave out is a cause called
                                                    "not itemised". previous is null until a
                                                    year has been stepped. Figures register in
                                                    sim/ui/figures_headline.py. The cash
                                                    figure takes its causes from the cash book
                                                    (below), so for cash nothing is left "not
                                                    itemised" beyond rounding.
      {"cmd":"money"}                              the ledger screen; its "cash_book" is
                                                    {year, opening, closing, causes:{cause:
                                                    signed amount}, earlier_years:[{year,
                                                    opening, closing, causes}]}: every change to
                                                    the founder's cash since the last yearly
                                                    snapshot, by cause (opening + causes =
                                                    closing). Written by HouseholdState.credit /
                                                    debit / reset_cash, the only writers of the
                                                    purse (sim/engine/cash_book.py); a save keeps
                                                    the open period and a few closed years.
      {"cmd":"leverage"}                           {leverage_points:[{lever, why_it_matters,
                                                    figures}], note}: literacy, labour, finance,
                                                    institutions, knowledge, materials, each
                                                    from the engine's own figures. `path` adds
                                                    the same leverage_points plus
                                                    years_following_the_chain_alone.
      {"cmd":"disclose"}                           {inventions:[{id, mode, licensees, operating}],
                                                    can_license_to:[actor ids]}: what you chose for
                                                    each invention you made; mode is default (it
                                                    spreads by being seen in use), secret, license
                                                    or publish.
      {"cmd":"disclose","id":"<id>","mode":"secret"|"publish"}
                                                   secret: outsiders learn it only as fast as the
                                                    trades and materials it needs allow, and
                                                    believe the concern later. publish: anyone
                                                    copies at once, you gain standing once, and it
                                                    cannot be taken back.
      {"cmd":"disclose","id":"<id>","mode":"license","licensee":"<firm or state id>","fee":N,"royalty":R}
                                                   the licensee pays `fee` from its purse to you
                                                    and can make it at once; a firm also pays you
                                                    share R of its takings each year (a state has
                                                    no takings, so no royalty). Replies {ok, note,
                                                    inventions} or {ok:false, error}.
      {"cmd":"idle"}                               {directed_hours_this_year, committed_hours,
                                                    idle_hours, delay_kinds:{kind:[ids]},
                                                    what_the_wait_is, potential_uses:{
                                                    startable_today, startable_at_no_cash_cost,
                                                    train_oversubscribed_trades, wage_work}}.
                                                    Never spends hours.
      {"cmd":"portfolio"}                          every active project: the founder-
                                                    hours it is ACTUALLY getting this
                                                    year and why (its rank in the queue,
                                                    how many projects share the pool),
                                                    the precise reason it is not moving
                                                    faster (staffing / trade_hours /
                                                    materials / money / calendar /
                                                    founder_hours), and every hired
                                                    trade's aggregate demand this year
                                                    against what it can supply - read
                                                    straight off the allocator, never a
                                                    second guess at its own numbers
      {"cmd":"bounty","id":"zinc_metal"}           post a public prize instead of
                                                    building it yourself (tier <=2 crafts
                                                    only; converts denarii into hours)
      {"cmd":"quote","what":"bounty","id":"zinc_metal"}   price, multiplier, eligibility and refusal
      {"cmd":"quote","what":"hire","trade":"smith","n":2}   paid now and due each year after
      {"cmd":"quote","what":"commission","trade":"smith","hours":200}   fee; hours last this year
      {"cmd":"quote","what":"open","id":"fin_restaurant"}   the opening charge, before `open`
      {"cmd":"quote","what":"train","trade":"machinist","n":2}   keep paid now, your hours, and
                                                    `wage_bill_added_per_year` once they join
                                                    Each quote returns `paid_now`, the figure the
                                                    command then charges. hire, commission, open,
                                                    train and bounty replies carry `paid_now` too.
      {"cmd":"buy","what":"forest","n":100}        buy 100 ha of coppice woodland
      {"cmd":"buy","what":"mine","material":"iron","n":500}   sink a mine
      {"cmd":"buy","what":"slaves","n":4}          the economic actions the optimizer
      {"cmd":"buy","what":"manumit","n":4}         could take, exposed to the player
      {"cmd":"policy","set":{"auto_hire":"replace"}}   auto_hire takes true, false or "replace":
                                                    replace-only hires back only the people lost
                                                    that year and never grows the staff; its audit
                                                    rows (`automation`) say so. A mine ordered by
                                                    auto_mine has an `order` id on its audit row,
                                                    its tranche and its working
      {"cmd":"sell","material":"iron","n":5}       sell stock at the current value
      {"cmd":"sell","what":"concern","id":"<id>"}  sell a concern you run through the exchange: the
                                                    buyer is the AI actor that can make it and pay
                                                    and keeps most money after paying; the price
                                                    is the concern's margin over the valuation
                                                    horizon. Reply: sold, buyer, price. You keep
                                                    the know-how
      {"cmd":"sell","what":"farm","n":40}          return farmland to the land market at what
                                                    `buy farm` charges per hectare, no fee
      {"cmd":"step","years":5}                     advance the calendar; returns what
                                                    completed and what happened. If
                                                    years>1 and this year alone already
                                                    has substantial founder-hours going
                                                    to waste with something genuinely
                                                    startable, says so up front as
                                                    "multi_year_hours_warning" and names
                                                    the hours at stake - founder-hours
                                                    do not bank at all between years, so
                                                    an idle year repeated N times is N
                                                    idle years, not one. Non-blocking:
                                                    the years still run. Every reply has
                                                    "alerts": a short list (empty when
                                                    quiet) of deaths, sackings, closures,
                                                    losses, credit trouble and population
                                                    collapse, worst tier first; the
                                                    staffing closure line (closed,
                                                    reopened, still shut, cause, remedies)
                                                    stands for closures. A disaster year's
                                                    log lines come back as one "events"
                                                    row whose "details" lists them; a
                                                    lasting shortage is "conditions" on
                                                    every state and step reply (material,
                                                    throughput, years, trend), logged in
                                                    full only when new or materially
                                                    changed. The step also
                                                    stops early for a concern closed for
                                                    want of staff, a newly blocked
                                                    project, a severe failure or the goal
                                                    becoming startable ("stopped_early").
                                                    With years>1 and a concern resting
                                                    on one person, "multi_year_staffing_warning"
                                                    names it. With --session each
                                                    simulated year is saved as it ends and
                                                    a progress line goes to stderr, so an
                                                    interrupt keeps the finished years.
                                                    A population fall past a threshold
                                                    also adds "demographic_emergency" to
                                                    every state reply.
      {"cmd":"move_base"}                          list the tiles your nation holds that
                                                    you could move to, with people,
                                                    days on the road and the cost
      {"cmd":"move_base","to":"italia_01"}         move the base (typed: `move <tile>`).
                                                    The town and its trades come from
                                                    that tile's share of the nation.
                                                    Costs the journey's wages, part of
                                                    this year's founder hours, local
                                                    contracts and most local standing.
                                                    Refused for a tile nobody lives on.
      {"cmd":"build_way","way":"road",             build a road ("road"), railway ("rail"), canal
       "from":"<tile>","to":"<tile>"}                ("canal") or bridge ("bridge", over a river
                                                    between two tiles on it) between two bordering
                                                    tiles you hold, or a port ("port", "to" the same
                                                    tile) on a coast tile without a natural harbour
                                                    (typed: `build_way road <tile> <tile>`, `build_way
                                                    port <tile>`); add "preview":true to quote the km,
                                                    labour hours, tonnes of material, money and
                                                    years first. Pays at market prices and takes a
                                                    crew from the labour market for the build years;
                                                    built ways are what journeys and hauls route over.
      {"cmd":"prospect","tile":"<tile>",           prospect a tile you hold for hidden deposits of a
       "material":"coal","person_days":2000}       mined material (typed: `prospect <tile> coal
                                                    2000`); pays prospectors and keeps the finds.
                                                    A mine names a deposit you have found ("buy
                                                    mine" takes an optional "deposit" id) and
                                                    raises no more than the deposit allows.
      {"cmd":"map"} / {"cmd":"map","full":true}    the land you hold: "you_are_based_at",
                                                    "tiles" (name, region, terrain,
                                                    people, days_from_your_base,
                                                    "deposits"), "next_door" (bordering
                                                    tiles not held), "tiles_held". Names
                                                    are a country and a number; the data
                                                    names no towns. `move_base` rows carry
                                                    the same name, region and terrain.
                                                    Typed: `map`, `country`, `geography`.
      {"cmd":"education"}                          "literacy" (general and elite, each
                                                    with its ceiling, share of the
                                                    ceiling and next year's value),
                                                    "schools" (the visible schooling
                                                    nodes), "schooling_flow",
                                                    "effective_schooling_flow",
                                                    "literate_trades", "trainees",
                                                    "not_held".
      {"cmd":"demography"}                         "cohorts", "last_year" (births, deaths,
                                                    nutrition_ratio; null until a year has
                                                    been simulated in this session),
                                                    "disease_burden", "epidemics_under_way",
                                                    "trades", "not_held".
      {"cmd":"divergence"}                         start values against now ("population",
                                                    "wage_index", "price_index",
                                                    "literacy_general", "literacy_elite",
                                                    "territory"), "technologies_you_built",
                                                    "dated_events" (status happened, under
                                                    way, upcoming or before the run began;
                                                    "causes_checked" is true when the event
                                                    states causes, with "causes_hold_now" and
                                                    "failed_causes"; "causes_not_modelled"
                                                    lists causes with no simulated
                                                    counterpart), "baseline" (the run
                                                    against the baseline ensemble: each
                                                    measure against its band, and which
                                                    built technologies the baseline society
                                                    would not yet hold; when no ensemble is
                                                    cached, "available" is false and
                                                    "how_to_generate" names the command
                                                    `simulator.py baseline-ensemble`) and
                                                    "cannot_know". Under fog an upcoming
                                                    event has no name.
      {"cmd":"finish"}                             end the run here and return the final
                                                    report with the full score (fog's
                                                    withheld total included); the save
                                                    still loads but the run stays ended.
                                                    A `step` that reaches the goal also
                                                    returns a "victory" block: date,
                                                    elapsed years, points so far,
                                                    achievements, how to get the score.
      {"cmd":"quit"}                               end the session
      {"cmd":"help"}                               front page and topic list
      {"cmd":"help","topic":"commands"}            every command, grouped (see below)
      {"cmd":"help","topic":"hire"}                one command, or any alias, in detail

      THE COMMAND LIST IS NOT MAINTAINED HERE. The examples above are a tour;
      `help` is the complete list, generated from the command registry
      (sim/ui/proto/command_registry.py). Each handler declares its own
      summary, usage, options, description and aliases with @command, and the
      dispatch table, typed aliases and help are all read from that one
      registry, so a command cannot run without being documented. The suite
      checks that every dispatchable command and typed alias appears in help.

      help reply shapes. `topic:"commands"` returns `commands` (name to
      summary and description), `usage` (name to example forms), `groups`
      (group to command names) and `aliases` (alias to command). A command
      or alias topic returns `command`: name, group, summary, usage, options
      (option to meaning), description and aliases. A word that is also a
      topic (money, log, stuck, ...) returns the topic text plus `command`.
      An unknown word returns `no such topic`, `did you mean` and `topics`.

      A project or hire that needs more people than exist in the country is
      refused, and the reason says so plainly.

      A `step` reply also carries `completed` (each record has `kind`:
      "technology", "concern" or "granted"), `events` (each row has `severity`, one of
      the eight tiers in `sim/ui/proto/event_severity.py`, run_ending first and
      informational last; the text rendering lists the worst tiers first and
      marks them), and, when anything
      completed or failed, `summary`: `completed`, `by_kind`, `failed`,
      `minor_failures` and, when the goal moved, `goal` (`measures` of
      label/before/after and `road_steps_gained`). The text rendering leads
      with a one-line SUMMARY once a step has several results; the full list
      follows it. Event messages: a failure starts "FAILED at" and is
      compact and marked "(minor)" when its loss is small against what you
      can fund (weighted up on the goal's road); a completion may be followed
      by "goal effect:" lines (metric before -> after, or that it is on the
      road; under fog never the total), and a finished concern left closed
      says "STATUS: CLOSED / NOT OPERATING" with what switches on when opened
      and, if free staff could not supervise it, "could not open it".

      The `state` object (also embedded in every `step` reply) reports: year,
      capital, revenue, founder hours available, founder_alive, scholars,
      artisans, reputation, suspicion, scandal, eminence, protection,
      done_count, active (each project's progress, including
      hours_offered_this_year/hours_effective_this_year and the allocator's
      own pool_rank_this_year/pool_active_count_this_year/pool_total_this_year
      - why THIS project got the share it got, read off the allocator, not
      recomputed), resource_throttle and throttle_binding (what is limiting
      work, if anything), and ended/end_reason once the run is over (goal
      reached, died, or ran out of horizon). `available` and `why` never
      consult the optimizer's own ordering for a decision, only for a stable
      listing order; every decision an agent needs is reachable through
      start/stop/bounty/buy/step alone, all the way to the transistor.

      WHY A PROJECT IS NOT MOVING FASTER, precisely. Every active project's
      `waiting_on` (in `state`, `why` and `portfolio`) is exactly one of:
        staffing         - this society cannot field the trade it needs AT ALL
        trade_hours      - the trade exists and could supply enough, but your
                           OWN other active work already has it booked this
                           year (see `portfolio`'s demand-vs-supply table)
        materials        - a single economy-wide shortage (see `capacity`)
                           is scaling every active project's hours down by
                           the same factor, this one included
        money            - the bill is more than you can raise, or more than
                           this year's pace (cost / calendar floor) can absorb
        calendar         - fully funded and fully worked; only time is left
        founder_hours    - waiting its turn: this year's pool is shared with
                           other active projects, named by rank and total
      `portfolio`'s own `constraint` field on each project is exactly this
      classification, and is built from the same `waiting_on` sentence, not
      a second guess at it. Each project also carries `blocker_kind`, that
      constraint named in the shared blocker kinds of sim/engine/blockers.py
      (staffing and trade_hours are specialists, materials is supply,
      founder_hours is hours), and `portfolio` leads with `bottlenecks`:
      [{kind, count, projects, hours_still_to_work, what_it_means, pools}],
      one per kind, most fixable first; pools are the engine's demand against
      supply for that kind (trade hours, directed hours, capital, the binding
      material).

      HAZARD FIGURES. In `risk`, each hazard's `what_you_can_do[kind]` carries
      `mitigations`: one {node, label, status ("in force" or "lapsed"),
      removes_share, points} per defence, and for a lapsed one closed_because,
      concern_to_open and how. `staff_loss_before_what_you_have_built`,
      `staff_loss_after_what_you_have_built`, `output_factor_after_what_you_have_built`
      and `national_public_health` ({share_removed, from}) are the figures the
      yearly shocks apply. Each `score` component has a `counts` sentence;
      `institutions` also lists `counted` and `finished_but_closed`.

      INTEREST GROUPS (Complaint 110). `groups` (aliases `interest_groups`, `factions`) lists
      the groups the economy has organised against the founder: {name, kind, cause (in words),
      people, income_lost_per_year, grievance_share, pull_on_the_state, state_undertakes_to_make_good,
      demands, petitions, organised_since}, with `state_leaves_unpaid_to_raise_from_taxpayers`,
      `state_in_deficit` and a `note`. `kind` is `displaced_producers` (the society's producers of
      a commodity the founder sold into the market) or `squeezed_employers` (employers of a trade
      whose price the founder's and the firms' hiring pushed up). A group's pull is the share of
      the state's attention its lost income earns; the state's answer is decided by its capacity
      and its purse: it books the claim as a line of its budget (`concession: group:<kind>:<subject>`),
      what its purse cannot pay is raised in the levy on taxpayers it sees (`requisition_report`
      names the group), a state not in deficit may forbid starting the techniques that make the
      commodity (a `politics` blocker in `why`, lifted by protection above the state-opposition
      line), and every petition puts blame (scandal) on the founder and a log line naming the
      group and its cause. `risk` carries `interest_groups` and `state_attention` carries
      `interest_groups` (names and causes) while any group is organised. Groups are actors of
      kind `interest_group` in the actor registry (ActorRecord fields `group_kind`, `subject`,
      `cause`, `members`, `lost_income`, `grievance`, `strength`, `claim`, `demands`).
      Other kinds are measured from the bodies of people and the firms: `displaced_workers` (a
      stratum whose trade's pay fell below what it had come to expect), `landholders` (a propertied
      stratum whose property income fell), `firm_owners` (firms whose profit fell below what their
      owners expected) and `falling_incomes` (the part of a stratum's fall in welfare those do not
      explain). Only `displaced_producers` can obtain a prohibition; the rest are made good from the
      state's purse as far as its capacity lets it.

      ANSWERING THE STATE'S DEMANDS (Complaint 110). `answer` (aliases `answer_demand`, `stance`) with
      `{"cmd":"answer","what":"comply"|"refuse"}` sets how you meet the requisition and the supply
      levy the state assesses (the office it presses on you is not declinable); bare `answer` shows
      the stance. The reply's `note` gives the odds: a refusal is enforced with a chance set by the
      state's capacity, turned aside in part by your protection; if enforced the state takes the
      demand and a penalty in proportion to its capacity, otherwise nothing. The log names each
      refusal and its outcome. Any other actor answers the same way through the player command
      `{"command":"answer_demand","stance":"refuse"}` (ActorRecord field `demand_stance`).

      MACHINE-READABLE MODES. 'state json', 'portfolio json' and 'risk json'
      (typed, inside `play`) print the raw reply - the exact line a script
      would get from `agent` - instead of the rendered screen. Every player
      of this game is an AI agent parsing text; this exists because several
      have lost runs parsing prose that was never meant to be machine-read.
      It is the identical resp dict either way, so the JSON and the prose can
      never disagree, and fog is scrubbed once, upstream of both.


DISPLAY UNITS (Complaint 285)
-----------------------------------------------------------------------------
Replies keep the numbers the engine writes. When the player has chosen a unit
for a dimension (`options`, saved as `display_units` in the application config:
a unit id per dimension of `area`, `mass`, `temperature`, `money`), every
quantity of that dimension in any reply gains a sibling field
`<field>_display`: `{"value": 12.3, "unit": "acre", "symbol": "ac"}`. The
original field is unchanged and still in its documented unit (`*_hectares` in
hectares, `*_tonnes` in tonnes, `*_kg` in kilograms, money fields in the
civilisation's coin). With nothing chosen no `_display` field appears and replies
are byte-identical to before. Commands take the units their help names.

Which fields are quantities is data: `field_rules` in `data/world/units.json`
(a regular expression on the field name, the dimension, the native unit).
Units, their symbols and conversions are data in the same file; a mod adds
`<mod_id>:<name>` units in its own `data/world/units.json`. Code: `sim/engine/units.py`
(registry, one `format_<dimension>` per dimension, `add_display`),
`sim/ui/units_text.py` (text screens), `sim/ui/cli_units_options.py` (the
options entry). Text screens show the chosen unit's value and symbol.
Compound units (price per tonne, yield per hectare) are not converted yet.


LOANABLE-FUNDS MARKET (Complaint 106)
-----------------------------------------------------------------------------
`money` gains `loanable_funds_market`, the civilisation's capital market as it
met at the start of the current year (the screen prints it as one line under
the credit limit):

    {"met": true,                      false (and only `market_rate`, the
                                       civilisation's starting rate) before the
                                       first yearly meeting
     "market_rate": 0.12,              yearly rate on loans in the civilisation
     "funds_lenders_hold": 1.2e10,     what households, firms, the founder and
                                       the state hold in loanable form (coin)
     "lenders_will_still_advance_you": null | number
                                       what lenders still advance beyond what
                                       others owe; your credit_limit is never more
     "the_state_owes": 0.0,            what the government actor has borrowed
     "means": "..."}

`interest_rate_on_arrears` is now the market rate plus a premium that grows
with the share of `credit_limit` used, less the founder's standing (which only removes premium; the rate is never below the market rate); it is not a
fixed number for the game. `credit_limit` falls as the market rate rises and is
bounded by `lenders_will_still_advance_you`. The state's own debt and interest
appear in the state's outlays (purpose `interest`; a negative purse is
debt) and nowhere in the founder's replies.
