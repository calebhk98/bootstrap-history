"""The {"cmd":"help"} pages, generated from the command registry.

`help` lists every registered command by group, `help <command>` (or an
alias) shows that command's usage, options and description, and `help <topic>`
shows a topic page. Commands declare their own text with @command (see
command_registry.py); topics register with @help_topic below.
"""

import json

from ..core import Sim
from . import command_registry

TOPICS = {}          # topic name -> builder(sim) returning the page dict
TOPIC_ALIASES = {}   # other word -> topic name


def help_topic(name, aliases=()):
    """Register a topic page: the builder takes the sim and returns a dict."""
    def register(builder):
        TOPICS[name] = builder
        for alias in aliases:
            TOPIC_ALIASES[alias] = name
        return builder
    return register


JSON_MODE_NOTE = (
    "add the word 'json' to almost any command (or \"json\":true in a JSON "
    "command) to get its reply as the raw structured object instead of the "
    "rendered screen; 'compact' implies 'json' and, on 'why', 'state' and "
    "'stuck', adds a small shared set of blocked/explanation fields")


def _command_text(name, fog):
    entry = command_registry.COMMANDS[name]
    if fog and entry["fog_hidden"]:
        return "not available under fog of war"
    return "%s. %s" % (entry["summary"], entry["description"])


@help_topic("commands", aliases=("command", "all"))
def _topic_commands(sim):
    """The command index: every registered command, grouped, with aliases."""
    names = list(command_registry.COMMANDS)
    return {
        "commands": {"json / compact": JSON_MODE_NOTE,
                     **{name: _command_text(name, sim.fog) for name in names}},
        "usage": {name: command_registry.COMMANDS[name]["usage"] for name in names},
        "groups": command_registry.grouped(),
        "aliases": command_registry.alias_map(),
        "more": 'help <command> or help <alias> for one command\'s usage, '
                'options and description',
    }


def _front_page(sim, typed_hints):
    fog = sim.fog
    return {
        "what this is": (
            "You are one person, dropped into a pre-industrial society, "
            "carrying the knowledge of how modern technology works but none "
            "of the industry that makes it. You are playing %s, beginning in "
            "%d. Knowing how a thing works is free. Building it is not: it "
            "takes your own hours, other people's hours, money, materials, "
            "and years."
            % (sim.civ.get("name", "a society"), sim.cfg["start_year"])),
        "how a turn works": (
            "You begin projects, then advance time. Nothing happens unless "
            "you make it. You are charged for food, rent and appearances "
            "every year whether or not you are building anything."),
        "what you are trying to do": (
            "Build %s, before the horizon at %d. You know what it is and "
            "what it is for; what you cannot see is the road there, only "
            "the next step of it."
            % (sim.nodes[sim.goal]["name"].lower() if sim.goal in sim.nodes else "it",
               sim.end_year)
            if fog else
            "Reach %s, and see the rest of what you can build on the way."
            % sim.goal),
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
        **({} if fog else {
            "and the sixth, once you have a goal in mind": (
                "{\"cmd\":\"path\",\"id\":\"<goal>\"} - everything still "
                "standing between here and there, AND which of those "
                "you could start TODAY. This is the walkthrough."),
        }),
        "the complete command index, and your own exact history": (
            "{\"cmd\":\"help\",\"topic\":\"commands\"} lists every "
            "command the game has, not only the five above - including "
            "'log', 'values', 'money', automation and save/load. "
            "{\"cmd\":\"log\"} is worth checking on its own: a "
            "paginated, exact record of everything that happens from "
            "here on."),
        "and the one rule that catches everybody": (
            "Finishing something earns you nothing. A concern earns when "
            "you 'open' it, and costs its upkeep only then too. "
            '{"cmd":"ventures"} lists what you know how to run and have '
            "not opened."),
        "when you cannot see why you are not getting on": '{"cmd":"stuck"}',
        "how to send a command": (
            'One command per line, in plain words: "available", '
            '"step 5", "hire smith 2", "why fud_wheelbarrow". Pasting a '
            'JSON command works too, if you happen to have one.'
            if typed_hints else
            'One JSON object per line on standard input, for example '
            '{"cmd":"available"} or {"cmd":"step","years":5}. Each reply is '
            'one JSON object.'),
        "you do not need to hold this process open": (
            'Pass --session FILE and the whole game is written to that '
            'file after every command and read back when you start '
            'again. So a script or an agent may run one command per '
            'invocation and throw the process away: `echo state | '
            'python3 sim/simulator.py play --session game.json` '
            'prints the readable screen and exits, and the next '
            'invocation carries on from exactly where it left off. '
            'There is no need for a held-open pipe, a FIFO or tmux. '
            'See {"cmd":"help","topic":"sittings"}.'),
        "one command in detail": 'help <command> or help <alias>, e.g. {"cmd":"help","topic":"hire"}',
        "more": {topic_name: '{"cmd":"help","topic":"%s"}' % topic_name for topic_name in HELP_TOPICS},
    }


@help_topic('labour')
def _topic_labour(sim):
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



@help_topic('population')
def _topic_population(sim):
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
            "move": "move the base to another tile: 'move' lists them, "
                    "'move <tile>' goes. It costs the journey's wages, "
                    "part of your year's hours, your local contracts and "
                    "most of your local standing",
        }}



@help_topic('money')
def _topic_money(sim):
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



@help_topic('economy', aliases=['buy'])
def _topic_economy(sim):
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



@help_topic('automatic', aliases=['policy'])
def _topic_automatic(sim):
    return {"what happens on its own": (
        "Some things the engine will do for you if you let it: grow the "
        "staff, teach trades, sink mines, buy woodland, shut down what you "
        "cannot pay for, pay off a scandal. Every one is a switch you "
        "control, and every one can be done by hand instead."),
        "see them": '{"cmd":"policy"}',
        "change one": '{"cmd":"policy","set":{"auto_hire":true}}'}



@help_topic('sittings', aliases=['save', 'load', 'script', 'scripting', 'agent', 'automation', 'batch', 'oneshot', 'one-shot', 'noninteractive', 'non-interactive', 'pipe'])
def _topic_sittings(sim):
    return {"playing across several sittings": (
        "Pass --session FILE on the command line. The game is written to "
        "that file after every command and read back when you start again, "
        "so you do not need to hold a process open or write a script."),
        "one command per invocation, for a script or an agent": (
            "This is the supported way to drive the game from a shell, "
            "and it needs no pipe held open, no FIFO and no tmux. Send "
            "one command on standard input, read the reply, let the "
            "process exit, and run it again for the next command:\n"
            "    echo state | python3 sim/simulator.py play "
            "--session game.json\n"
            "    echo 'step 5' | python3 sim/simulator.py play "
            "--session game.json\n"
            "The second invocation resumes exactly where the first "
            "stopped. `play` gives you the readable screen; `agent` "
            "gives you JSON on stdout and takes the same --session."),
        "why you may not have found this": (
            "it was only ever filed under 'sittings', which is a word "
            "about a person playing over several evenings. Every agent "
            "that has played this game so far built a harness to hold a "
            "process open before discovering it did not have to.")}



@help_topic('stuck', aliases=['blocked'])
def _topic_stuck(sim):
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



@help_topic('log', aliases=['history', 'diary'])
def _topic_log(sim):
    fog = sim.fog
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



@help_topic('protection', aliases=['standing'])
def _topic_protection(sim):
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



@help_topic('eminence', aliases=['prominence'])
def _topic_eminence(sim):
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



@help_topic('risk', aliases=['hazards'])
def _topic_risk(sim):
    return {"risk": ("What history is about to do to you, with dates, and "
                     "what you have built that blunts each one. Every "
                     "hazard is fightable and the numbers are real."),
            "see it": '{"cmd":"risk"}'}



@help_topic('fog')
def _topic_fog(sim):
    fog = sim.fog
    return {"fog of war": (
        "ON. You can see what you have built, what you could begin today as "
        "a one line summary, and things you have heard of but cannot yet "
        "begin. You cannot see where anything leads, and there is no way to "
        "view the whole tree." if fog else "OFF. You can see the whole tree.")}


def _agent_help(sim, topic=None):
    """The help reply: the front page, a topic, or one command's page."""
    from .. import protocol as _protocol      # read live: cli.py patches TYPED_HINTS
    topic = (topic or "").strip().lower()
    if not topic:
        return _front_page(sim, _protocol.TYPED_HINTS)
    topic_name = topic if topic in TOPICS else TOPIC_ALIASES.get(topic)
    entry = command_registry.resolve(topic)
    if topic_name is None and entry is None:
        matches = command_registry.close_matches(topic, list(TOPICS) + list(TOPIC_ALIASES))
        return {"no such topic": topic, "did you mean": matches,
                "topics": list(TOPICS)}
    page = dict(TOPICS[topic_name](sim)) if topic_name else {}
    if entry is not None:
        page["command"] = command_registry.page(entry["name"], sim.fog)
    return page


command_registry.register_command(
    "help", group="game", aliases=("h", "?", "commands"),
    summary="this index, a topic, or one command's page",
    usage=["help", "help commands", "help <command>", "help <topic>"],
    options={"<command>": "any command or alias: shows its usage, options and description",
             "<topic>": "a topic page; the front page lists them"},
    description="Bare help is the front page. `help commands` lists every command by "
                "group. An unknown word gets close matches.")

HELP_TOPICS = tuple(TOPICS)
