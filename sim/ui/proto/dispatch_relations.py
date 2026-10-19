"""The relations and set_relation commands: a seat's country's side toward another country, and a note on it (Complaint 597).

The record belongs to the country, not the seat (sim/agents/relations.py), so a note outlives the seat that wrote it
and a seat can set only its own country's side."""
import os

from sim.agents.api import relations
from sim.engine.ui_port import ROOT
from sim.json_files import read_json

from .command_registry import command

SETTABLE = ("stance", "note", "term")


def _stances():
    return read_json(os.path.join(ROOT, "data", "world", "relation_stances.json"))["stances"]


def own_country(sim):
    """The country the acting seat plays for."""
    return sim.state.seats[sim.state.acting_seat].country or sim.civ["id"]


def countries(sim):
    """Every country a relation can name: the home one, the seats' and the partners'."""
    seat_countries = {seat.country for seat in sim.state.seats.values() if seat.country}
    return sorted({sim.civ["id"]} | seat_countries | set(sim.partner_countries()))


def _refusal(cause, error, **fields):
    return dict({"ok": False, "cause": cause, "error": error + " Nothing was changed."}, **fields)


def _other_country(sim, cmd):
    """(other country, refusal) for the command's `with`."""
    other = cmd.get("with") or cmd.get("what") or cmd.get("country")
    known = countries(sim)
    if not isinstance(other, str) or other not in known:
        return None, _refusal("unknown_country", "name a country: %s." % ", ".join(known), choices=known)
    if other == own_country(sim):
        return None, _refusal("same_country", "%s is your own country." % other)
    return other, None


def _row(sim, country, other):
    return {"with": other, "ours": relations.read(sim.stores, country, other),
            "theirs": relations.public_view(relations.read(sim.stores, other, country))}


@command("relations", shape="word", group="society",
         summary="your country's standing with other countries, and your notes on them",
         usage=["relations", "relations <country>", '{"cmd":"relations","with":"<country>"}'],
         options={"<country>": "show only the relation with this country (default: every country with a record)"},
         description="Each row is your country's own side (stance, trust, treaty terms, tariff, embargo, your private "
                     "note, a dated history) and what the other country shows of its side toward you (never its note "
                     "or trust). Notes and history belong to the country, so they stay when a seat leaves.")
def _cmd_relations(sim, nodes, cmd, ended):
    country = own_country(sim)
    if cmd.get("with") or cmd.get("what") or cmd.get("country"):
        other, refusal = _other_country(sim, cmd)
        if refusal:
            return refusal
        return dict({"ok": True, "country": country}, **_row(sim, country, other))
    rows = [_row(sim, country, other) for other in relations.partners_with_records(sim.stores, country)]
    reply = {"ok": True, "country": country, "relations": rows}
    if not rows:
        reply["hint"] = "no relation recorded yet; 'set_relation <country> stance <stance>' or 'set_relation <country> note <text>'"
    return reply


def _from_text(text):
    """`<country> stance <value>`, `<country> note <words>` or `<country> term <name> <value>` as command fields."""
    words = str(text or "").split()
    fields = {"with": words[0]} if words else {}
    if len(words) >= 3 and words[1] in SETTABLE:
        fields[words[1]] = " ".join(words[2:])
        if words[1] == "term" and len(words) >= 4:
            fields["term"], fields["value"] = words[2], _number_or_text(" ".join(words[3:]))
    return fields


def _number_or_text(text):
    try:
        number = float(text)
    except ValueError:
        return text
    return int(number) if number.is_integer() else number


@command("set_relation", shape="text", group="society",
         summary="set your country's stance, a treaty term or a note toward another country",
         usage=["set_relation <country> stance <stance>", "set_relation <country> note <text>",
                "set_relation <country> term <name> <value>",
                '{"cmd":"set_relation","with":"<country>","stance":"friendly","note":"...","term":"<name>","value":3}'],
         options={"<country>": "the other country", "stance": "one of the stances 'relations' lists on a refusal",
                  "note": "your private words on that country (cut when long)", "term": "a treaty term name, with value",
                  "side": "only your own country is accepted: you cannot set another country's side"},
         description="Sets your country's side of the pair; the other country's side is its own to set. Notes and terms "
                     "are kept with the country, not the seat.")
def _cmd_set_relation(sim, nodes, cmd, ended):
    if cmd.get("text") and not cmd.get("with"):
        cmd = dict(_from_text(cmd["text"]), **{key: value for key, value in cmd.items() if key != "text"})
    country = own_country(sim)
    side = cmd.get("side")
    if side is not None and side != country:
        return _refusal("not_your_country", "you play for %s and can set only its side of a relation." % country, choices=[country])
    other, refusal = _other_country(sim, cmd)
    if refusal:
        return refusal
    if not any(cmd.get(field) is not None for field in SETTABLE):
        return _refusal("nothing_to_set", "give a stance, a note or a term with its value.")
    stances = _stances()
    if cmd.get("stance") is not None and cmd["stance"] not in stances:
        return _refusal("unknown_stance", "the stances are %s." % ", ".join(stances), choices=stances)
    if cmd.get("term") is not None and not str(cmd["term"]).strip():
        return _refusal("nothing_to_set", "a term needs a name.")
    if cmd.get("stance") is not None:
        relations.set_side(sim.stores, country, other, stance=cmd["stance"])
    if cmd.get("note") is not None:
        relations.set_side(sim.stores, country, other, note=str(cmd["note"]))
    if cmd.get("term") is not None:
        relations.set_term(sim.stores, country, other, str(cmd["term"]).strip(), cmd.get("value"))
    return dict({"ok": True, "country": country}, **_row(sim, country, other))
