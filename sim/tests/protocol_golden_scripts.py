"""The scripted agent sessions the protocol golden transcripts are recorded from.

Each script is a fixed civilisation, seed and horizon (dice off) and a list of steps; a step is one `agent`
invocation fed its commands on stdin. A step with "session" is a `--session` run: the game is saved after
every command and loaded again by the next invocation. Commands are plain protocol JSON.
"""


def reads(names):
    return [{"cmd": name} for name in names]


FOUNDER = {
    "name": "rome_founder",
    "arguments": ["--civ", "rome_100ad", "--seed", "7", "--deterministic", "--no-events", "--horizon", "30"],
    "steps": [{"run": (
        # overview reads
        reads(["state", "figures", "economy", "money", "cashbook", "ventures", "labour", "idle", "portfolio",
               "goals", "stuck", "leverage", "anatomy", "mines", "capacity", "materials", "market", "risk",
               "log", "score", "world_events", "changes", "notes", "map", "education", "demography",
               "population", "values", "groups", "relations", "policy", "game_options", "commitments",
               "divergence", "seats", "keep", "saving", "automation", "colonies", "rollout", "reserve",
               "allocate", "priority", "disclose", "patent", "shares", "offers", "causes"])
        + [{"cmd": "state", "compact": True}, {"cmd": "available", "limit": 6},
           {"cmd": "available", "state": "blocked", "limit": 3}, {"cmd": "figures", "id": "cash"},
           {"cmd": "why", "id": "identity_cover"}, {"cmd": "path", "id": "identity_cover"},
           {"cmd": "help"}, {"cmd": "help", "topic": "commands"}, {"cmd": "help", "topic": "hire"},
           {"cmd": "world_events", "id": "years"}, {"cmd": "move_base"}, {"cmd": "rush"}]
        # projects: start, queue, stop, refusals
        + [{"cmd": "start", "id": "hom_eraser_breadcrumb"}, {"cmd": "start", "id": "arrival_orientation"},
           {"cmd": "start", "id": "hom_toothbrush"}, {"cmd": "start", "id": "nonexistent_node"},
           {"cmd": "start", "id": "mil_dreadnought"}, {"cmd": "priority", "id": "hom_toothbrush"},
           {"cmd": "priority"}, {"cmd": "stop", "id": "hom_eraser_breadcrumb"},
           {"cmd": "stop", "id": "hom_eraser_breadcrumb"}, {"cmd": "pursue", "id": "identity_cover"},
           {"cmd": "programme", "action": "show"}, {"cmd": "exclude", "what": "category:law"},
           {"cmd": "exclude"}, {"cmd": "include", "what": "all"}, {"cmd": "portfolio"}, {"cmd": "idle"}]
        # labour
        + [{"cmd": "quote", "what": "hire", "trade": "smith", "n": 1}, {"cmd": "hire", "trade": "smith", "n": 1},
           {"cmd": "hire", "trade": "chemist", "n": 1}, {"cmd": "train", "trade": "scribe", "n": 1},
           {"cmd": "commission", "trade": "smith", "hours": 10}, {"cmd": "labour", "trade": "smith"},
           {"cmd": "fire", "trade": "smith"}, {"cmd": "fire", "trade": "smith"}]
        # money
        + [{"cmd": "quote", "what": "bounty", "id": "hom_toothbrush"}, {"cmd": "bounty", "id": "pwr_oil_shale"},
           {"cmd": "bounty"}, {"cmd": "bribe"}, {"cmd": "pay", "what": "debt"}, {"cmd": "pay", "amount": 5},
           {"cmd": "buy", "what": "forest", "n": 10}, {"cmd": "buy", "what": "forest", "n": 0.01},
           {"cmd": "sell", "material": "iron", "n": 5}, {"cmd": "quote", "what": "open", "id": "fin_restaurant"},
           {"cmd": "found", "what": "bank", "capital": 100}, {"cmd": "note", "text": "first note"},
           {"cmd": "notes"}, {"cmd": "money"}, {"cmd": "cashbook"}]
        # time, save and load inside one run
        + [{"cmd": "step"}, {"cmd": "state", "compact": True}, {"cmd": "save", "file": "founder.json"},
           {"cmd": "step", "years": 2}, {"cmd": "log"}, {"cmd": "changes"}, {"cmd": "ventures"},
           {"cmd": "load", "file": "founder.json"}, {"cmd": "state", "compact": True},
           {"cmd": "step", "years": 2}, {"cmd": "score"}, {"cmd": "unknown_command_word"}])}],
}

SECOND_SEAT = {
    "name": "han_two_seats_fog",
    "arguments": ["--civ", "han_china_100ad", "--seed", "3", "--deterministic", "--no-events",
                  "--horizon", "20", "--fog"],
    "steps": [{"run": [
        {"cmd": "state", "compact": True}, {"cmd": "available", "limit": 4}, {"cmd": "seats"},
        {"cmd": "join", "seat": "second"}, {"cmd": "join", "seat": "second"}, {"cmd": "seats"},
        {"cmd": "state", "as": "second", "compact": True}, {"cmd": "available", "as": "second", "limit": 4},
        {"cmd": "start", "id": "arrival_orientation", "as": "second"},
        {"cmd": "start", "id": "arrival_orientation"},
        {"cmd": "hire", "trade": "scribe", "n": 1, "as": "second"},
        {"cmd": "shares", "do": "issue", "share": 0.1, "to": "second", "price": 10},
        {"cmd": "offers", "as": "second"}, {"cmd": "offers"}, {"cmd": "shares", "as": "second"},
        {"cmd": "money", "as": "second"}, {"cmd": "market", "as": "second"},
        {"cmd": "start", "id": "mil_dreadnought"}, {"cmd": "why", "id": "mil_dreadnought"},
        {"cmd": "path", "id": "junction_transistor"}, {"cmd": "relations"},
        {"cmd": "set_relation", "with": "rome_100ad", "stance": "friendly"},
        {"cmd": "set_relation", "with": "atlantis", "stance": "friendly"}, {"cmd": "relations"},
        {"cmd": "lever", "lever": "army", "value": 1}, {"cmd": "army"}, {"cmd": "armies"},
        {"cmd": "step", "years": 2}, {"cmd": "state", "as": "second", "compact": True},
        {"cmd": "seats"}, {"cmd": "handover", "to": "second"}, {"cmd": "handover", "to": "nobody"},
        {"cmd": "step"}, {"cmd": "score", "as": "second"}, {"cmd": "log", "as": "second"},
        {"cmd": "world_events"}, {"cmd": "divergence"}, {"cmd": "population"}, {"cmd": "map"},
        {"cmd": "finish"}]}],
}

SESSION = {
    "name": "norse_session_round_trips",
    "arguments": ["--civ", "norse_900ad", "--seed", "5", "--deterministic", "--no-events", "--horizon", "25"],
    "steps": [
        {"session": "norse.json", "run": reads(["state", "available"])},
        {"session": "norse.json", "run": [{"cmd": "start", "id": "arrival_orientation"},
                                          {"cmd": "start", "id": "nonexistent_node"}]},
        {"session": "norse.json", "run": [{"cmd": "hire", "trade": "smith", "n": 1},
                                          {"cmd": "state", "compact": True}]},
        {"session": "norse.json", "run": [{"cmd": "step", "years": 2}]},
        {"session": "norse.json", "run": [{"cmd": "portfolio"}, {"cmd": "ventures"}, {"cmd": "economy"},
                                          {"cmd": "cashbook"}]},
        {"session": "norse.json", "run": [{"cmd": "bounty", "id": "pwr_oil_shale"}, {"cmd": "step"}]},
        {"session": "norse.json", "run": [{"cmd": "log"}, {"cmd": "score"}, {"cmd": "seats"},
                                          {"cmd": "finish"}]},
    ],
}

SCRIPTS = [FOUNDER, SECOND_SEAT, SESSION]
