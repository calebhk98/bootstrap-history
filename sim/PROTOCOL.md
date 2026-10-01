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
      {"cmd":"start","id":"zinc_metal"}            begin a project (error explains
                                                    exactly what is missing if you can't;
                                                    if it would oversubscribe a hired
                                                    trade your other active work already
                                                    draws on, says so right here, in
                                                    "this_oversubscribes_a_trade" - it
                                                    still starts, this is a warning)
      {"cmd":"stop","id":"zinc_metal"}             abandon a project; sunk cost is sunk
      {"cmd":"exclude","what":"freedman_staff"}    never let rush, rush preview, auto_open or
      {"cmd":"exclude","what":"trait:buys_people"}  auto_commission begin this id; also
      {"cmd":"exclude","what":"category:<cat>"}     category:<cat> and trait:<trait>. Saved with
      {"cmd":"include","what":"<entry>|all"}        the game; rush and rush preview list what
      {"cmd":"exclude"}                             they left out, with the reason, under
                                                    "excluded". Bare exclude lists the entries.
                                                    `start` by hand is unaffected.
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
      (engine/proto/command_registry.py). Each handler declares its own
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
      "technology", "concern" or "granted"), `events`, and, when anything
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
      a second guess at it.

      HAZARD FIGURES. In `risk`, each hazard's `what_you_can_do[kind]` carries
      `mitigations`: one {node, label, status ("in force" or "lapsed"),
      removes_share, points} per defence, and for a lapsed one closed_because,
      concern_to_open and how. `staff_loss_before_what_you_have_built`,
      `staff_loss_after_what_you_have_built`, `output_factor_after_what_you_have_built`
      and `national_public_health` ({share_removed, from}) are the figures the
      yearly shocks apply. Each `score` component has a `counts` sentence;
      `institutions` also lists `counted` and `finished_but_closed`.

      MACHINE-READABLE MODES. 'state json', 'portfolio json' and 'risk json'
      (typed, inside `play`) print the raw reply - the exact line a script
      would get from `agent` - instead of the rendered screen. Every player
      of this game is an AI agent parsing text; this exists because several
      have lost runs parsing prose that was never meant to be machine-read.
      It is the identical resp dict either way, so the JSON and the prose can
      never disagree, and fog is scrubbed once, upstream of both.
