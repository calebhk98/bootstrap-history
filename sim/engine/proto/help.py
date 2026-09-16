"""The {"cmd":"help"} topic tree."""

import collections, hashlib, json, math, os, random, re
from collections import defaultdict

from ..data import *          # the shared tables and loaders
from ..data import (ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, closure,
                   critical_path, downstream_count, is_downstream, load, money_word,
                   topo_order, trade_family)
from ..fog import strip_self_play_advice

from ..core import Sim

# TYPED_HINTS is NOT imported here: cli.py patches engine.protocol.TYPED_HINTS
# directly at runtime, so _agent_help reads it through the protocol module
# itself, live - see _wrap's own comment on the same pattern, in
# engine/proto/util.py.




HELP_TOPICS = ("commands", "labour", "population", "economy", "money",
               "automatic", "sittings", "fog", "eminence", "risk",
               "protection", "stuck", "log")


def _agent_help(s, topic=None):
    """Everything a player needs, from inside the game, a topic at a time.

    A tester should not have to be told the commands out of band, and neither
    should a player. But the whole of it at once was four and a half kilobytes
    of JSON before a single move had been made, and testers were spending a
    command just to re-read it. If it is too much for a machine it is far too
    much for a person. So: a short front page, and topics on request.
    """
    # LIVE, NOT A SNAPSHOT: see _wrap's own comment on DISPLAY_WIDTH, in
    # engine/proto/util.py, for why this goes through the protocol module
    # rather than the plain imported name.
    from .. import protocol as _protocol
    TYPED_HINTS = _protocol.TYPED_HINTS
    fog = getattr(s, "fog", False)
    topic = (topic or "").strip().lower()

    if not topic:
        return {
            "what this is": (
                "You are one person, dropped into a pre-industrial society, "
                "carrying the knowledge of how modern technology works but none "
                "of the industry that makes it. You are playing %s, beginning in "
                "%d. Knowing how a thing works is free. Building it is not: it "
                "takes your own hours, other people's hours, money, materials, "
                "and years."
                % (s.civ.get("name", "a society"), s.cfg["start_year"])),
            "how a turn works": (
                "You begin projects, then advance time. Nothing happens unless "
                "you make it. You are charged for food, rent and appearances "
                "every year whether or not you are building anything."),
            # UNDER FOG TOO. This used to say "there is no score but the state
            # of what you have built", and a normal-play tester spent five
            # hundred years optimising breadth on the strength of it, then met
            # "Getting here from 100 AD is the whole game" on the ending
            # screen. They had the money and the years to reach it. Fog hides
            # the SOCIETY's tree; it has no business hiding what a man who
            # knows how a transistor works is trying to build. The NAME, never
            # the id: naming the id would hand back the prerequisite crawl that
            # the visibility guard exists to stop.
            "what you are trying to do": (
                "Build %s, before the horizon at %d. You know what it is and "
                "what it is for; what you cannot see is the road there, only "
                "the next step of it."
                % (s.nodes[s.goal]["name"].lower() if s.goal in s.nodes else "it",
                   s.end_year)
                if fog else
                "Reach %s, and see the rest of what you can build on the way."
                % s.goal),
            "you arrive alone": (
                "No employees, no slaves, nobody who owes you anything. Anyone "
                'who works for you is hired, taught, commissioned or bought. See '
                '{"cmd":"help","topic":"labour"}.'),
            "the five you need first": {
                "state": "where you stand",
                "available": "what you could begin today",
                "why <id>": "everything known about one thing",
                "start <id>": "begin it",
                "step <years>": "let time pass",
            },
            # THE ACTUAL WALKTHROUGH, and it used to appear in exactly one
            # line of `help commands` and nowhere near the five above. An
            # England player spent about forty minutes guessing before
            # finding it, and said it "trivially reorganized the rest of
            # play" once they had. It is also the answer to the single most
            # requested thing two other players asked for in separate
            # sessions: what the goal still needs, joined to what you could
            # start on it today, instead of two separate reports you cross
            # off against each other by eye.
            **({} if fog else {
                "and the sixth, once you have a goal in mind": (
                    "{\"cmd\":\"path\",\"id\":\"<goal>\"} - everything still "
                    "standing between here and there, AND which of those "
                    "you could start TODAY. This is the walkthrough."),
            }),
            # NAMED OUTRIGHT, not left to be found inside "more" below by a
            # player who has to already suspect it exists. A player who won
            # the whole game reported using specialised commands for a long
            # while without realising `help commands` was a complete index
            # of everything the game can do, and separately flagged `log` -
            # an exact, paginated history of starts, completions, failures,
            # hazards, openings, closures and staffing - as something they
            # wished they had leaned on from the start. Both are true from
            # turn one.
            "the complete command index, and your own exact history": (
                "{\"cmd\":\"help\",\"topic\":\"commands\"} lists every "
                "command the game has, not only the five above - including "
                "'log', 'values', 'money', automation and save/load. "
                "{\"cmd\":\"log\"} is worth checking on its own: a "
                "paginated, exact record of everything that happens from "
                "here on."),
            # See cmd_play's opening screen for why this is not buried in a
            # topic: a finished concern earns nothing until its doors open, and
            # a tester left seven of them shut and went bankrupt in year three.
            "and the one rule that catches everybody": (
                "Finishing something earns you nothing. A concern earns when "
                "you 'open' it, and costs its upkeep only then too. "
                '{"cmd":"ventures"} lists what you know how to run and have '
                "not opened."),
            "when you cannot see why you are not getting on": '{"cmd":"stuck"}',
            # Which of the two front ends is reading. `play` types words and
            # `agent` sends JSON, and telling a person at a keyboard to send
            # one JSON object per line - which this did - is telling them to
            # do something the program they are using does not ask for.
            "how to send a command": (
                'One command per line, in plain words: "available", '
                '"step 5", "hire smith 2", "why fud_wheelbarrow". Pasting a '
                'JSON command works too, if you happen to have one.'
                if TYPED_HINTS else
                'One JSON object per line on standard input, for example '
                '{"cmd":"available"} or {"cmd":"step","years":5}. Each reply is '
                'one JSON object.'),
            # SAID HERE, IN THE FIRST THING ANYBODY READS. This game is played
            # mostly by AI agents driving it from a shell, and every one of
            # them so far has built a tmux or FIFO harness to hold the process
            # open, because nothing they read told them they did not have to.
            # One wrote it up as the only real friction in the interface. The
            # capability has always existed - `help sittings` has described it
            # all along - but "sittings" is a word about a person at a
            # keyboard over several evenings, and no script author would ever
            # type it looking for this. So it is said in the briefing, in the
            # terms the reader actually has: you do not need a held-open
            # process, one command per invocation is a supported way to play.
            "you do not need to hold this process open": (
                'Pass --session FILE and the whole game is written to that '
                'file after every command and read back when you start '
                'again. So a script or an agent may run one command per '
                'invocation and throw the process away: `echo state | '
                'python3 rome/sim/simulator.py play --session game.json` '
                'prints the readable screen and exits, and the next '
                'invocation carries on from exactly where it left off. '
                'There is no need for a held-open pipe, a FIFO or tmux. '
                'See {"cmd":"help","topic":"sittings"}.'),
            "more": {t: '{"cmd":"help","topic":"%s"}' % t for t in HELP_TOPICS},
        }

    if topic in ("commands", "command", "all"):
        return {"commands": {
            "state": "where you stand; add full:true for every field",
            "available": "what you could begin today, summarised by subject; "
                         "add subject, find, afford, limit/offset, or all:true; "
                         "add sort (price/hours/years/earns/upkeep/risk/alpha/"
                         "fewest_missing) and reverse to change the order, and "
                         "page with offset/heard_offset all the way to the end. "
                         "fewest_missing is about the heard-of list only - it "
                         "orders by how few of a thing's OWN prerequisites are "
                         "still missing, not by distance to any goal you have "
                         "set; see 'path <goal>' for that, once fog is off",
            "why <id>": "everything known about one thing",
            "start <id>": "begin work on something",
            "stop <id>": "abandon it, losing what you have spent",
            "rush": "start everything you could begin today in one go, "
                    "highest-leverage first; add limit:N to cap it",
            "step <years>": "let time pass",
            "money": "the whole ledger: what comes in, what goes out",
            "values": "what this society actually believes, as numbers - the "
                     "same fields a completion's 'changes the society' line "
                     "names",
            "log": "your own history - what you did and what followed, most "
                   "recent first; add failures:true, find, since/before, "
                   "order, offset. Never the whole thing in one go",
            "quote <what>": "what something would cost before you commit to it; "
                            'so far {"cmd":"quote","what":"mine",'
                            '"material":"coal","n":500}',
            "close <material>": "shut your own workings down and stop paying to "
                                "keep them standing",
            "risk": "what history is about to do to you, and what blunts it",
            "labour": "who you employ and what trades exist here",
            "population": "the country's own numbers, the one town your "
                          "household actually reaches, and - per trade - how "
                          "many exist in the country, how many are within "
                          "your reach, and how many you employ",
            "materials": "stocks on hand, annual production and demand, and "
                         "current buy/sell values for every tracked material",
            "capacity": "why active projects are moving at their present pace: "
                        "annual material throughput and shortages, trade-hour "
                        "demand and supply, power, staffing, and finance. "
                        "Throughput is this year's flow; durable unused material "
                        "is shown separately by 'materials' as stock on hand",
            "sell <material> <tonnes>": "sell material you actually have in stock",
            "hire / fire / train / commission": "see the labour topic",
            "buy": "farmland, worker housing, a named trade school, material "
                   "stock, forest, nitre, mine, slaves, or manumit; see economy",
            "work <trade> <hours>": "do an ordinary job for ordinary pay",
            "allocate <id> <hours>": "a STANDING order: give this active "
                "project this many of your own hours every year from now "
                "on, ahead of anything you have not directed; 'allocate "
                "<id> 0' (or 'off') clears it. 'allocate work <trade> "
                "<hours>' is the same standing order for selling hours as "
                "wages instead of a project. Bare 'allocate' lists what is "
                "currently set; hours nobody directs keep being shared out "
                "by priority exactly as before",
            "bounty <id>": "pay someone else to solve it instead",
            "open <id>": "start actually running something you have worked out "
                         "how to do; until you do, it earns nothing and costs "
                         "nothing",
            "ventures": "what you are running, and what you know how to run and "
                        "have not opened",
            "mothball <id> / restore <id>": "shut a finished work down, or reopen it",
            "bribe <amount>": "spend money to reduce a scandal",
            "policy": "every automatic behaviour, and a switch for each",
            "path <id>": ("not available under fog of war" if fog
                          else "the route to one thing: everything still "
                               "standing between here and there, AND which "
                               "of those you could start today - the "
                               "walkthrough, effectively; try 'path' on "
                               "your goal first"),
            "score": "what you are optimising: each ending-score component, "
                    "raw and weighted, any time - not only at the end; the "
                    "technology-coverage share stays withheld under fog "
                    "until the run is over, the same way the goal's own "
                    "road total does",
            "save <file> / load <file>": "write or read a game",
            "help": "this; add a topic",
            "quit": "stop",
        }}

    if topic == "labour":
        return {"labour": (
            "You arrive alone. Everything anyone else does for you is hired by "
            "the year, bought as a single job, taught by you from nothing if "
            "this society has no such trade, or bought outright as a person. "
            "Trades are NOT interchangeable: a smith is not a scribe, and a "
            "project asking for an engineer cannot be built by smiths however "
            "many you have."),
            "commands": {
                "labour": 'who exists here and what they cost; add "trade" for one',
                "hire": '{"cmd":"hire","trade":"smith","n":3} - paid every year, '
                        "whether you have work for them or not",
                "fire": '{"cmd":"fire","trade":"smith","n":1}',
                "train": '{"cmd":"train","trade":"machinist","n":2} - teaches a '
                         "trade that does not exist here, out of your own hours",
                "commission": '{"cmd":"commission","trade":"smith","hours":400} - '
                              "buy a job rather than a person",
            }}

    if topic == "population":
        return {"population": (
            "You are one household, in one town, not the whole of the "
            "country you were handed into. Every number `labour` shows you - "
            "who you can hire, how fast hiring one more moves the wage - is "
            "sized to that one town's market, not to the millions the "
            "civilisation actually holds. `population` shows both, side by "
            "side, trade by trade, so a refusal or a rising wage can be read "
            "as a statement about your own reach rather than about the "
            "Roman Empire, Han China or any other country's true size. "
            "Every country-wide and reach figure it shows is an explicit "
            "ESTIMATE, not a census."),
            "commands": {
                "population": "no argument needed - the whole picture at once",
            }}

    if topic == "money":
        # `help money` and `help economy` printed the same page, and both were
        # listed as separate topics, so a play tester read one and expected
        # something else from the other. Money is where it comes from and where
        # it goes; economy is what you can buy with it.
        return {"where it comes from": (
            "Your practice - the trade this society already had, which you can "
            "do from the first day - plus every concern you have OPENED, plus "
            'what your own workshop sells. {"cmd":"money"} itemises all of it '
            "and the rows sum to the revenue above them."),
            "your practice pays less than the tree quotes": (
                "About a third: one person in a rented room is not an organised "
                "concern, and that gap does not close with time. Selling your "
                "hours for wages takes another bite, because you cannot be in "
                "two places."),
            "a concern you open starts small": (
                "It reaches its full figure over about three years."),
            "where it goes": (
                "Living and appearances, wages, the upkeep of what you are "
                "RUNNING, mines standing whether or not you work them, and "
                "interest on arrears."),
            "money costs money to hold": (
                "Living and appearances is about a sixtieth of your capital a "
                "year, on top of a subsistence floor and your household, plus "
                "a fixed sum for each rank you hold. In a patronage society a "
                "man visibly richer than he lives is suspected, and a man "
                "seeking standing must spend on it. An idle million bleeds "
                "about fifteen thousand a year doing nothing, which is why "
                "money sitting still is money going backwards."),
            "what you can buy": '{"cmd":"help","topic":"economy"}',
            "debt": "You may spend past what you have, as far as somebody will "
                    "lend you and no further. Arrears cost interest."}

    if topic in ("economy", "buy"):
        return {"the ledger": '{"cmd":"money"} itemises what comes in and what '
                              "goes out, including where the income comes from",
                "buy forest": '{"cmd":"buy","what":"forest","n":100} hectares of '
                              "coppice, which is where charcoal comes from",
                "buy nitre": ('{"cmd":"buy","what":"nitre","n":2000} lays the '
                              "requested square metres of nitre bed. Saltpetre "
                              "is made, not mined; a shortage warning calculates "
                              "a purchase from the live deficit plus 20% headroom."),
                "buy farm": "buy farm 120 lowers staple costs through productive land",
                "buy housing": "buy housing 5 adds five durable worker places",
                "buy trade school": "buy school smith 2 makes two more smiths' worth "
                                    "of annual labour locally available",
                "materials": "materials shows durable stock and flow; buy material "
                             "iron 10 or sell iron 5 trades tonnes at current prices",
                "buy mine": '{"cmd":"buy","what":"mine","material":"coal","n":500} '
                            "tonnes a year of your own workings; it takes years "
                            "to sink, and it costs to keep standing whether or "
                            "not you use it. ASK THE PRICE FIRST with "
                            '{"cmd":"quote","what":"mine","material":"coal",'
                            '"n":500}, and close it with '
                            '{"cmd":"close","material":"coal"}. Materials: '
                            + Sim.mine_catalog_hint(Sim),
                "buy slaves": '{"cmd":"buy","what":"slaves","n":5}. This is '
                              "available because it was the ordinary condition of "
                              "production in most of these societies, and a model "
                              "that hides it lies about the cost of everything.",
                "manumit": '{"cmd":"buy","what":"manumit","n":5} frees people you '
                           "hold. They then work better, and it is the decent thing.",
                "debt": "You may spend past what you have, as far as somebody will "
                        "lend you and no further. Arrears cost interest. "
                        "Money in arrears also stalls HOUR progress on work "
                        "you already have in hand: a project still owing "
                        "money draws on what you could raise this year, and "
                        "if that is nothing, its hours mostly go to waste "
                        "rather than into the work - not just the money, the "
                        "founder-hours too. 'state' shows which active "
                        "project this is happening to and names the cause "
                        "(why_underfunded); a project already fully paid is "
                        "never affected by this, whatever else is in "
                        "arrears."}

    if topic in ("automatic", "policy"):
        return {"what happens on its own": (
            "Some things the engine will do for you if you let it: grow the "
            "staff, teach trades, sink mines, buy woodland, shut down what you "
            "cannot pay for, pay off a scandal. Every one is a switch you "
            "control, and every one can be done by hand instead."),
            "see them": '{"cmd":"policy"}',
            "change one": '{"cmd":"policy","set":{"auto_hire":true}}'}

    # ALSO UNDER THE NAMES A SCRIPT AUTHOR WOULD TRY. "sittings" describes a
    # person at a keyboard over several evenings. An AI agent looking for how
    # to drive this thing from a shell types "script", "agent", "batch" or
    # "oneshot", finds nothing, and builds a FIFO harness instead - which is
    # exactly what happened, repeatedly.
    if topic in ("sittings", "save", "load", "script", "scripting", "agent",
                 "automation", "batch", "oneshot", "one-shot",
                 "noninteractive", "non-interactive", "pipe"):
        return {"playing across several sittings": (
            "Pass --session FILE on the command line. The game is written to "
            "that file after every command and read back when you start again, "
            "so you do not need to hold a process open or write a script."),
            "one command per invocation, for a script or an agent": (
                "This is the supported way to drive the game from a shell, "
                "and it needs no pipe held open, no FIFO and no tmux. Send "
                "one command on standard input, read the reply, let the "
                "process exit, and run it again for the next command:\n"
                "    echo state | python3 rome/sim/simulator.py play "
                "--session game.json\n"
                "    echo 'step 5' | python3 rome/sim/simulator.py play "
                "--session game.json\n"
                "The second invocation resumes exactly where the first "
                "stopped. `play` gives you the readable screen; `agent` "
                "gives you JSON on stdout and takes the same --session."),
            "why you may not have found this": (
                "it was only ever filed under 'sittings', which is a word "
                "about a person playing over several evenings. Every agent "
                "that has played this game so far built a harness to hold a "
                "process open before discovering it did not have to.")}

    if topic in ("stuck", "blocked"):
        return {"stuck": (
            "Type 'stuck' at any time. It answers, in one place, why you are "
            "not getting on: what each piece of work in hand is waiting for, "
            "whether anything is startable and affordable, whether a raw "
            "material is throttling everything, whether you have room for more "
            "people, and how deep in arrears you are."),
            "the usual answers": (
                "hours (you only have so many), money (you can raise only so "
                "much), a trade this society does not have, a material nobody "
                "is selling, or room for the people it would take."),
            "where to look next": (
                '{"cmd":"available"} for what you could begin, '
                '{"cmd":"labour"} for people, {"cmd":"money"} for the ledger.')}

    if topic in ("log", "history", "diary"):
        return {"log": (
            "Your own history, in the order it happened: what you started, "
            "what finished, what failed and why, a concern opening or "
            "closing, staff hired or let go, a hazard landing, money running "
            "out. Type 'log' alone for the twenty most recent lines."),
            "see only the bad news": "'log failures'",
            "search it": "'log find plague'",
            "a year range": "'log since 300 before 400'",
            "read forward from the start instead of back from now": "'log oldest'",
            "page through to the end": "'log offset 20'",
            "why it never dumps everything": (
                "a long run's history runs to tens of thousands of lines, "
                "more than anyone - human or script - can read in one reply, "
                "so this always pages and there is no way to ask for all of "
                "it at once."),
            "fog": ("respects it: a line cannot go on naming something you "
                    "have since forgotten or never heard of just because it "
                    "was visible the year it happened.")}

    if topic in ("protection", "standing"):
        return {"protection": (
            "How far your standing shields you when you produce an effect "
            "nobody can explain. It decides whether a strange result out of "
            "your workshop is read as learning or as sorcery, and it is the "
            "only thing money can buy here directly."),
            "what raises it": (
                "A patron, citizenship, a licensed collegium, land endowed in "
                "public, a school, and your reputation - and spending on "
                "advocacy and piety, which is what `bribe` does when you have "
                "no scandal to answer. Protection caps at 92% in total, and "
                "money is only 30 points of that however much you spend - a "
                "break tester read the 92 as the ceiling on bribery, offered a "
                "million, and stopped at the same 32% a hundred had bought. "
                "The rest has to be earned."),
            "what it does NOT protect you from": (
                "Eminence. Being too large is the one hazard no protection "
                "touches; see {\"cmd\":\"help\",\"topic\":\"eminence\"}."),
            "where to watch it": '{"cmd":"state"} shows it under STANDING'}

    if topic in ("eminence", "prominence"):
        return {"eminence": (
            "The one hazard no patron, no bribe and no reputation protects you "
            "from, because it IS reputation. It rises with how well known you "
            "are and how visibly rich, it is multiplied by standing close to "
            "the throne, and past the danger line it rolls every year for your "
            "ruin. Sejanus was the most protected man in Rome until the morning "
            "he was not."),
            "what lowers it": (
                'One command does, and its price is real: {"cmd":"withdraw"} '
                "halves your prominence now and gives up half the reputation "
                "you hold above what your work by itself is worth. Reputation "
                "here is your credit limit, your protection, the wages you must "
                "pay and the pace of your projects, so you cannot get small and "
                "stay grand - and you cannot do it twice in twelve years, "
                "because being seen to retire repeatedly is not retiring."),
            "what survives it": (
                "A wide, dispersed institution - academy_network makes the "
                "hazard itself smaller, and corpus_dispersed means what you "
                "know is in too many places to burn. Being merely rich and "
                "merely famous is the dangerous combination."),
            "and time helps": (
                "A city gets used to you. The longer you have been a fixture "
                "and the more of your work it has already seen, the less "
                "alarming the next thing is - the same familiarity that decays "
                "the alarm your work causes takes up to a third off this."),
            "if it lands": (
                "45% of the time it is a confiscation and a forced retirement, "
                "35% your patron is destroyed in somebody else's quarrel, and "
                "20% it is the end of the run. `state` shows both figures."),
            "where to watch it": '{"cmd":"state"} shows it under STANDING'}

    if topic in ("risk", "hazards"):
        return {"risk": ("What history is about to do to you, with dates, and "
                         "what you have built that blunts each one. Every "
                         "hazard is fightable and the numbers are real."),
                "see it": '{"cmd":"risk"}'}

    if topic == "fog":
        return {"fog of war": (
            "ON. You can see what you have built, what you could begin today as "
            "a one line summary, and things you have heard of but cannot yet "
            "begin. You cannot see where anything leads, and there is no way to "
            "view the whole tree." if fog else "OFF. You can see the whole tree.")}

    return {"no such topic": topic, "topics": list(HELP_TOPICS)}
