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
      stack trace or a bare False. The text is for a reader and its wording
      may change; a refusal that has a stable code also carries "cause" (for
      example "literacy_wall", "household_room", "unknown_node"), and
      "choices" when it lists the answers it would have accepted. Read those,
      not the text. The same holds for prose that reports what happened: a
      step's events and the `log` entries may carry "event_kind" and "facts"
      (the figures the sentence states), the same after a save and load as
      before it; "stopped_early" has "stopped_kind"; a project's
      "waiting_on" has "waiting_on_kind"; the score's "why" has "why_kind";
      an automation row may carry "reason_kind" and its figures.

      Keeping one process alive. Every `agent` and `play` process builds or
      loads the game and rebuilds the economy before its first command. With
      --session, a process per command pays that every time; one process
      reading many commands pays it once (the measurement is in Complaints/497).
      A caller that cannot hold a pipe open between its own tool calls can
      start the process on a named pipe and write to the pipe later:
      `mkfifo in; python3 sim/simulator.py agent --session s.json
      --save-interval 60 < in > out &`, then `echo '{"cmd":"state"}' > in`.
      --save-interval SECONDS (on `agent` and `play`; default 0) sets how often
      the session file is written. 0 writes after every command, as always; a
      positive figure writes when that long has passed since the last write,
      after `save`, `load` and `quit`, when the game ends, and on leaving the
      process. The file holds the same game either way, and a process killed
      between writes loses the commands since the last one.
      `sim/tests/test_cli_one_process_session.py` checks that the final save
      equals the one a process per command ends in.

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
                                                    blockers, a list of {kind, cause, text, ids}
                                                    (cause names the refusing check, e.g.
                                                    absent_trades, craft_staff; kinds: knowledge, power, supply,
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
                                                    exactly what is missing if you can't,
                                                    and blocked_kind / blocked_cause give
                                                    the first blocker as codes;
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
                                                    did_nothing_because (text) and
                                                    did_nothing_kind (a stable code; plus
                                                    did_nothing_material for a shortage).
                                                    It stays paused until
                                                    resume, or resumes itself with auto_resume.
      {"cmd":"exclude","what":"freedman_staff"}    never let rush, rush preview, auto_open or
      {"cmd":"exclude","what":"trait:buys_people"}  auto_commission begin this id; also
      {"cmd":"exclude","what":"category:<cat>"}     category:<cat> and trait:<trait>. Saved with
      {"cmd":"include","what":"<entry>|all"}        the game; rush and rush preview list what
      {"cmd":"exclude"}                             they left out, with the reason, under
                                                    "excluded". Bare exclude lists the entries.
                                                    `start` by hand is unaffected.
      {"cmd":"world_events"}                       the dated world event log, the same for every seat:
      {"cmd":"world_events","id":"<years|kind>"}    {events:[{year,kind,actors,tiles,cause,facts}]}.
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
                                                    closing). Written by the ledger's seat
                                                    account (sim/ledger/seat_account.py), the
                                                    only writer of the purse; a save keeps the
                                                    open period and a few closed years.
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
      {"cmd":"patent"}                             {patents:{id:{granted, expires, licensees, live}},
                                                    shares_held, shares_issued, offers}: what the seat
                                                    holds as an actor. {"cmd":"patent","id":"<id>"}
                                                    applies for the exclusive right to an invention you
                                                    hold, where a state knows the institution. Others may
                                                    still practise it unlicensed: the state enforces the
                                                    right only as far as its capacity reaches, and a holder
                                                    who catches an infringer is paid its margin.
      {"cmd":"found","what":"bank","capital":<amount>}
                                                   put capital of yours into a bank of the agent economy
                                                    (it takes households' deposits and lends them on); needs
                                                    a node declaring deposit_banking. {ok, bank, capital} or
                                                    {ok:false, error, cause} with cause no_banking_institution,
                                                    capital_not_positive, capital_exceeds_cash or economy_not_open.
      {"cmd":"offer","to":"<actor id>","give":{...},"take":{...}}
                                                   offer a firm, a state, a stratum or another seat things
                                                    for things: money, patent [ids], licence [ids] with
                                                    royalty {id: share of takings}, shares {issuer id: share
                                                    of its equity}. An AI actor answers at its next turn;
                                                    another seat uses accept or decline. {ok, offered, to,
                                                    expires} or {ok:false, error}.
      {"cmd":"offers"}                             the offers made to this seat. {"cmd":"accept","offer":"<id>"}
                                                    and {"cmd":"decline","offer":"<id>"} answer one.
      {"cmd":"pay","what":"debt"}                  pay the state once: all of its debt (or what your money
                                                    covers), {"what":"claims"} what it has undertaken to
                                                    make good to organised interest groups, or
                                                    {"cmd":"pay","amount":N} a sum (past the debt it stays
                                                    in the state's purse as a reserve). {ok, paid, message,
                                                    capital, state_debt} or {ok:false, error}. Works that
                                                    do this on finishing declare the node mechanic
                                                    `transfer` (data/branches/MECHANICS.md).
      {"cmd":"rollout"}                            the works that declare `coverage`, with units open, the
                                                    share of the people served and the units that would
                                                    serve everyone. {"cmd":"rollout","id":"<id>","share":S}
                                                    opens or expands the work by the units that reach share
                                                    S (0.5 or 50): {ok, message, covered, units}.
      {"cmd":"settle"}                             the tiles settlers could reach, best land first, and the
                                                    settlers and outfit cost. {"cmd":"settle","tile":"<id>"}
                                                    founds a colony there: settlers leave the home working
                                                    age, and the colony is a people of its own, fed by that
                                                    tile. {"cmd":"colonies"} lists those held.
      {"cmd":"shares","do":"issue","share":S,"to":"<id>","price":P}
                                                   sell share S of your own equity; its holders draw
                                                    dividends from your margin each year.
                                                    {"cmd":"shares","do":"buy","issuer":"<id>","share":S,"from":"<id>","price":P}
                                                    buys shares in another actor. Both are offers.
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
      {"cmd":"buy","what":"living_stock","material":"ramie_stock_kg","n":100,"partner":"han_china_100ad"}
                                                    stock bought from a partner that sells it
      {"cmd":"buy","what":"smuggled_stock","material":"silkworm_eggs_kg","n":0.1}
                                                    stock taken from a partner that will not sell it:
                                                    the carrying is paid either way, the partner's state
                                                    may catch it (`caught`), seize the stock and shut its
                                                    markets to you for years; `quote` first gives the
                                                    cost and `chance_caught`
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
      Other kinds are measured from the bodies of people, the firms and the state's own books:
      `displaced_workers` (a stratum whose trade's pay fell below what it had come to expect),
      `jobless_workers` (a stratum whose trade's hours the labour core's clearing left unhired by
      more than it expected; `technique` names the running technique that did the work with fewer
      hands), `landholders` (a propertied stratum whose share of the land market's rent fell; the
      share of the society's output where no land was let), `firm_owners` (firms whose profit fell
      below what their owners expected), `clergy` and `scholars` (a church or an academy, actors
      founded by a civilisation's `cast.actors`, whose collections fell: the rent of its
      endowment, a tithe on the sales of the goods that serve one need, patronage that falls as
      schooling spreads), `office_holders` (salaries paid on the state's administration and court
      lines and the fees on its revenue fell below what they expected), `soldiers` (the army's
      budget line is in arrears; an army without its pay loses loyalty and, below the mutiny line,
      deserts and takes its arrears from the treasury, logged as MUTINY) and `falling_incomes` (the
      part of a stratum's fall in welfare those do not explain). `displaced_producers` and
      `jobless_workers` can obtain a prohibition: producers against the techniques that make their
      commodity, a substitute for it (goods that serve the same household need), their goods
      category or the line it refines; jobless workers against `technique` and any technique that
      makes what it makes or a substitute for it. The rest are made good from the state's purse as
      far as its capacity lets it.

      ANSWERING THE STATE'S DEMANDS (Complaint 110). `answer` (aliases `answer_demand`, `stance`) with
      `{"cmd":"answer","what":"comply"|"refuse"|"negotiate"|"conceal"}` sets how you meet the
      requisition and the supply levy the state assesses and a confiscation it demands (the office it
      presses on you is not declinable); bare `answer` shows the stance. The reply's `note` gives the
      odds. Refusing: enforced with a chance set by the state's reach, turned aside in part by your
      protection; if enforced the state takes the demand and a penalty in proportion to its capacity,
      otherwise nothing; either way the state marks you defiant (it assesses you as more visible, fading
      over the years) and the blame lands on you. Negotiating (with optional `"service": <money's worth
      of work>`): you offer a smaller sum, the state takes it with a chance that falls with its capacity
      and rises with the share offered, else insists on the whole. Concealing: part of your wealth is
      held where the state cannot count it (its visible scale, and so the confiscation it can demand,
      shrink), costs a share a year, and is taken with a penalty if the state finds it. The log names each
      outcome. Any other actor answers the same way through the player command
      `{"command":"answer_demand","stance":"negotiate","service":0}` (ActorRecord fields `demand_stance`,
      `service_offer`, `concealed`, `defiance`).

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
are byte-identical to before. A civilisation's own file may name `display_units`
(`{"area": "iugerum", "mass": "libra"}`); the front end for people uses them for
any dimension the player has not chosen, and `agent --pretty` does too (JSON
replies for scripts do not).

Commands take the units their help names (`buy farm` hectares, `buy mine`
tonnes a year, `buy nitre` square metres, `sell`/`quote material` tonnes,
`bribe` and the `rush` caps in the civilisation's coin). Any of them also
takes a `unit`: `{"cmd":"buy","what":"farm","n":10,"unit":"acre"}`, the text
form `buy farm 10 acre`, or `"n": "10 acre"`. The unit is any registry unit of
that quantity's dimension (id, name, plural or symbol; a civilisation's own unit
only in its civilisation), or `shown` for the unit the player displays. The
engine converts through the registry; without a `unit` the quantity is the
named native unit, so a script never depends on a display choice. A unit of the
wrong kind is refused with the units that would do.

Which fields are quantities is data: `field_rules` in `data/world/units.json`
(a regular expression on the field name, the dimension, the native unit).
Units, their symbols and conversions are data in the same file; a mod adds
`<mod_id>:<name>` units in its own `data/world/units.json`. Code: `sim/engine/units.py`
(registry, one `format_<dimension>` per dimension, `add_display`),
`sim/ui/units_text.py` (text screens), `sim/ui/cli_units_options.py` (the
options entry). Text screens show the chosen unit's value and symbol.
Compound units (price per tonne, price per hectare) follow both choices. Quantities written inside
sentences by the engine go through `sim/engine/units_prose.py`
(`mass_text`, `area_text`, `money_text`, `temperature_text`);
`sim/tests/test_complaint_285_no_hand_units.py` fails on a sentence that
formats one by hand.


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

SEATS: SEVERAL PLAYERS IN ONE GAME
-----------------------------------------------------------------------------
A seat is one player: a household, what it has built and learned, its goal
and its founder. A game starts with the first seat, and a civilisation file's
`cast.seats` or the `join` command adds more.

    {"cmd":"state","as":"second"}      any command, for the seat it names
    {"cmd":"seats"}                    who is playing, and whose run has ended
    {"cmd":"join","seat":"second"}     add a player (optional "kit", "country")
    agent --seat second / play --seat second
                                       the seat this process plays, when a
                                       command names none

Without `as` a command is for the session's seat, which is the first seat for
every script written before seats existed. An unknown seat is a refusal that
changes nothing. Reads about the world (`market`, `population`, `society`) are
the same for every seat; reads about a holder (`state`, `available`, `log`,
`money`) show the addressed seat. `seats` shows another seat's country and
whether its run has ended, not its purse or its work.

A seat is a household seat unless `join` says otherwise:

    {"cmd":"join","seat":"senate","seat_kind":"country"}                       hold your own country's government
    {"cmd":"join","seat":"khan","seat_kind":"country","country":"han"}         hold another country's

A country seat's holder is that country's `Government` actor (the reply's `holder`, an actor id such as
`government:rome_100ad`), and it has no founder and no household: the reply carries `founder: null` and
`household: null`, and `seats` shows its row with `kind` and `holder` and no purse. It has no kit and knows no
techniques of its own (a `kit` is refused with `cause` `country_seat_has_no_kit`). It is not among the seats the
household phases of the year run, and it never ends the game or holds it open; the government acts with the year of
the actors. Refusals carry `cause`: `unknown_country` (`choices` lists the countries that have a government),
`unknown_seat_kind`. Commands that need a household (`state`, `available`, the projects, labour and money groups) are
refused for a country seat with `cause` `country_seat_has_no_household`; the reads about the world, the seats, the
game and relations work, and `step` runs the year for everyone. The levers of the state itself are Complaint 595.
Two country seats may name one country (a replacement joins before a handover); until one hands over they share its
government.

    {"cmd":"handover","to":"second"}   hand your seat to the seat "second", which must already be in the game and empty

A handover gives the replacement the known techniques, works, holdings, cash, institutions, goal, country and notes
of the seat you play, and your seat leaves the game; the replacement keeps its own founder. The replacement must be
an empty seat (one `join` just added): it may hold cash, debts and known techniques, which merge with yours, but no
works, staff, holdings, institutions, arrears or goal record, because those would be overwritten. Your debts and claims
(facility draws, term loans as borrower or lender, deposits, arrears) pass to the replacement, so a handover never
forgives a debt, and every store keyed by your seat's id (goods, offers, shares, licences, other actors' records) is
renamed to the replacement's. Notes belong to the
seat that wrote them and pass with it. Records kept by country (relations, with their notes) stay with the country,
which the replacement now plays for. Only your own seat can be handed over (`"from"` naming another is refused).
Refusals change nothing and carry `cause`: `unknown_seat` (`choices` lists the seats), `same_seat`, `not_your_seat`,
`no_replacement`, `replacement_not_empty` (`holds` lists what it holds), `replacement_wrong_kind` (a country seat
passes only to an empty country seat, a household seat to a household seat). The reply carries `from`, `to`, `known_nodes`, `country`, `notes` (how many passed) and `seats`.
A country seat uses the same command: its kind, holder and country are fields of the seat and move with it.

`step` advances the year for every seat still playing. A seat's run ends for
that seat alone (a founder who dies with nobody to carry the work in a game
with mortal founders, a denunciation, a fall): its commands that need a living
holder are refused with the reason, and the others play on. The game is over
when no seat is playing, or every seat still playing has reached its goal. In
a game with immortal founders no founder dies, so this never arises.

## Relations between countries

The relations store (`sim/agents/relations.py`, declared in `data/world/stores.json`) holds, per ordered pair of
countries, that country's own side toward the other: `stance`, `trust`, `treaty` terms, `tariff`, `embargo`, a private
`note` and a dated `history` of `{year, kind, facts}`. It belongs to the country, so it survives the seat that wrote
it, and it is saved with the game. Other mechanisms record into it with `relations.record_event` and `set_side`.

    {"cmd":"relations"}                                   every country this seat's country has a record with
    {"cmd":"relations","with":"han"}                      one pair: "ours", and "theirs" (the other side's stance,
                                                          treaty, tariff, embargo and history; never its note or trust)
    {"cmd":"set_relation","with":"han","stance":"friendly"}   also "note":"...", or "term":"<name>","value":<json>
    {"cmd":"set_relation","with":"han","term":"tariff","value":0.1}   your state's tariff on goods from that country (a share of their value at the source); value 0 removes it
    {"cmd":"set_relation","with":"han","embargo":"on"}   stops goods from that country crossing into your markets; "off" lifts it
                                                          (a null value removes the term)

A seat sets only its own country's side: `"side"` naming another country is refused with `cause`
`not_your_country` (`choices` lists the one allowed). Other refusal causes: `unknown_country` (`choices` lists
the countries), `same_country`, `unknown_stance` (`choices` lists them, from `data/world/relation_stances.json`),
`nothing_to_set`. Replies carry `country`, `with`, `ours` and `theirs`.

### The state's levers

A country seat (`join` with `seat_kind: country`) sets the levers of the government it holds; the next year's budget
and revenue read them. `levers` lists what is set; `lever` sets one, and a null `value` clears it (the civilisation
file's figure or the derived one applies again).

    {"cmd":"levers","as":"senate"}                                  the levers set, the kinds, and the budget lines
    {"cmd":"lever","lever":"revenue","name":"land_tax","value":0.08}   a declared form's rate; a new form also needs "basis"
    {"cmd":"lever","lever":"budget","name":"dole","value":0.5}      the share of a standing line kept (0 to 1)
    {"cmd":"lever","lever":"army","value":20000}                    soldiers wanted (the army moves toward it at a bounded rate)
    {"cmd":"lever","lever":"navy","value":10}                       ships wanted
    {"cmd":"lever","lever":"works","name":"water_works","value":50000}   m2 of masonry equivalent wanted
    {"cmd":"lever","lever":"reserve","value":3}                     years of the standing need held before a surplus is spent
    {"cmd":"lever","lever":"monopoly","name":"salt_kg","value":true}   hold (true) or release (false) a good as a state monopoly
    {"cmd":"lever","lever":"subsidy","name":"wheat_kg","value":1000}   money a year handed to the good's producers
    {"cmd":"lever","lever":"mandate","name":"wheat_kg","value":50}     tonnes a year the state must buy of the good

A reply carries `lever`, `name`, `before`, `after`, `country` and `levers`. A seat sets only its own country's levers:
`country` naming another is refused with `cause` `not_your_country`, a household seat with
`household_seat_has_no_government`. Other causes: `unknown_lever`, `unknown_name` and `unknown_basis` (`choices` lists
what is accepted), `value_not_number`, `value_out_of_range` (`low`, `high`), `value_not_boolean`, `nothing_to_clear`.
Until tax rates are a state choice with consequences (Complaints 625 and 626) a rate may be any share of its base.

### Armies and campaigns

A country seat raises armies out of the soldiers its state keeps (the army line), sends them to a tile, recalls them and
stands them down. `armies` lists them; `army` acts. The year's campaign phase (run on `step`) marches each army along
the route graph, feeds it from what it carries, the land it crosses and a pack-animal column from the country's own
tiles within reach, takes its losses to hunger, disease and unpaid pay, and where it ends on another actor's tile
besieges and storms it. A tile it wins passes to its country at the control level the data names, and rises with the
years it is held with an army on it. There is no declaration of war: an army that ends on another actor's tile is an
attack on it. A state no seat plays raises and orders armies to the tiles other armies threaten, and attacks nobody.

    {"cmd":"army","action":"raise","soldiers":5000,"tile":"italy_03"}   a new army on a tile of yours (your best-endowed when none)
    {"cmd":"army","action":"march","army":"army_1","tile":"iran_03"}     orders it to a tile; it marches in the year's phase
    {"cmd":"army","action":"recall","army":"army_1"}                     orders it back to the tile it was raised on
    {"cmd":"army","action":"disband","army":"army_1"}                    its soldiers return to the state's force
    {"cmd":"armies"}                                                      your armies, and the soldiers in none

A reply carries the army's `army`, `tile`, `soldiers`, `target`, `food_kg`, `supply_state` (share of its ration met in the
last stretch), `pay_owed` and this year's `events` (hunger, disease, desertion, withdrew, conquest). Refusals carry a
`cause`: `household_seat_has_no_government`, `army_size_not_positive`, `not_enough_soldiers` (`available`), `tile_not_yours`,
`unknown_tile`, `unknown_army` (`choices`), `not_your_army`, `unknown_action`. Battles go to the world event log as
kind `battle` (`attacker_win_probability`, `attacker_lost`, `defender_lost`).

## Commands from mods

A mod may add commands, named `<mod_id>:<name>` (typed or as `{"cmd": "<mod_id>:<name>"}`), with an optional bare
alias that works while nothing else claims the word. They appear in `help` like any command. A macro replays existing
commands through this same protocol, so fog guards and option checks apply to it; a mod policy runs at the start or
end of each year of a `step` and appears in the `programme` lines of the reply. See `mods/README.md`.
