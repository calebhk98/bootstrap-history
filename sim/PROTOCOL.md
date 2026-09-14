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

    python3 rome/sim/simulator.py validate
    python3 rome/sim/simulator.py path junction_transistor
    python3 rome/sim/simulator.py costs --top 25
    python3 rome/sim/simulator.py run --strategy recommended --mc 400
    python3 rome/sim/simulator.py run --strategy recommended --no-events   # pure engineering timeline
    python3 rome/sim/simulator.py compare --mc 400
    python3 rome/sim/simulator.py play --strategy recommended
    python3 rome/sim/simulator.py play --manual                            # real free choice, no autopilot
    python3 rome/sim/simulator.py agent                                    # JSON protocol, see below

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
                                                    floor, prerequisites and its note
      {"cmd":"why","id":"zinc_metal"}              the full explanation for one node:
                                                    cost, staff, risk, chain, what it
                                                    unlocks, why it is or isn't startable
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
                                                    the years still run.
      {"cmd":"quit"}                               end the session

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

      MACHINE-READABLE MODES. 'state json', 'portfolio json' and 'risk json'
      (typed, inside `play`) print the raw reply - the exact line a script
      would get from `agent` - instead of the rendered screen. Every player
      of this game is an AI agent parsing text; this exists because several
      have lost runs parsing prose that was never meant to be machine-read.
      It is the identical resp dict either way, so the JSON and the prose can
      never disagree, and fog is scrubbed once, upstream of both.
