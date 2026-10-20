"""The lever and levers commands: a country seat sets its own government's revenue, budget, forces, works, reserve,
monopolies, subsidies and mandates (Complaint 595).

The rules are plain functions in `sim/agents/government_levers.py`; this module finds the seat's own government, hands
the request over and shapes the reply. A seat sets only its own country's levers."""
from sim.agents.api import government_levers
from sim.engine.state_seat import COUNTRY_SEAT
from sim.engine.ui_port import material_prices
from sim.refusal import Refusal

from .command_registry import command

WORDS = {"true": True, "false": False, "on": True, "off": False, "clear": None, "none": None, "null": None}


def _refusal(cause, error, choices=None, **fields):
    reply = {"ok": False, "cause": cause, "error": error + " Nothing was changed."}
    if choices is not None:
        reply["choices"] = list(choices)
    return dict(reply, **fields)


def own_country(sim):
    """The country the acting seat plays for."""
    return sim.state.seats[sim.state.acting_seat].country or str(sim.civ["id"])


def seat_government(sim, cmd):
    """(government, country, None) the acting seat holds, or (None, None, refusal reply)."""
    seat = sim.state.seats[sim.state.acting_seat]
    if seat.kind != COUNTRY_SEAT:
        return None, None, _refusal("household_seat_has_no_government",
                                    "seat %r holds a household, not a government; join with seat_kind country to hold one."
                                    % sim.state.acting_seat)
    country = own_country(sim)
    named = cmd.get("country")
    if named is not None and named != country:
        return None, None, _refusal("not_your_country", "you hold the government of %s and can set only its levers, not %s's."
                                    % (country, named), [country], country=named)
    government = sim.actors.government_of(None if country == str(sim.civ["id"]) else country)
    if government is None:
        return None, None, _refusal("no_government", "%s has no government to set." % country)
    return government, country, None


def lever_context(sim, country):
    """What the country declares and has: its revenue forms, the goods the economy knows, its people."""
    if country == str(sim.civ["id"]):
        forms, people = list(sim.civ.get("state_revenue") or []), sim.population.total
    else:
        profile = sim.actors.state.countries[country]
        forms, people = list(profile.extra.get("state_revenue") or []), profile.population
    return government_levers.LeverContext(forms, set(material_prices(sim)), people)


def set_lever_reply(sim, cmd):
    """The reply to setting one lever on the acting seat's own government."""
    government, country, refusal = seat_government(sim, cmd)
    if refusal:
        return refusal
    result = government_levers.set_lever(government.record, cmd, lever_context(sim, country))
    if isinstance(result, Refusal):
        return {"ok": False, "cause": result.cause, "choices": result.choices, "error": str(result), **result.facts}
    return dict(result, ok=True, country=country, levers=government_levers.current(government.record),
                note="read by the government's budget from the next year's accounts.")


def _from_text(text):
    """`<lever> [<name>] <value>` as command fields; a scalar lever has no name."""
    words = str(text or "").split()
    fields = {"lever": words[0]} if words else {}
    rest = words[1:]
    if words and words[0] not in government_levers.SCALAR_KINDS and rest:
        fields["name"], rest = rest[0], rest[1:]
    if rest:
        word = rest[0]
        try:
            fields["value"] = float(word)
        except ValueError:
            fields["value"] = WORDS.get(word.lower(), word)
    return fields


@command("lever", shape="text", group="society",
         summary="set a lever of your country's government: a tax rate, budget line, army, navy, works, reserve, monopoly, subsidy or mandate",
         usage=["lever revenue <form> <rate>", "lever budget <line> <share>", "lever army <soldiers>", "lever navy <ships>",
                "lever works <work> <m2>", "lever reserve <years>", "lever monopoly <good> true|false",
                "lever subsidy <good> <money a year>", "lever mandate <good> <tonnes a year>",
                '{"cmd":"lever","lever":"revenue","name":"land_tax","value":0.08,"as":"senate"}'],
         options={"lever": "revenue, budget, army, navy, works, reserve, monopoly, subsidy or mandate",
                  "name": "the revenue form (a new form also needs \"basis\"), budget line, work or good the lever is about; "
                          "army, navy and reserve have none",
                  "value": "revenue: share of the base (0 to 1; days a year for a labour due); budget: share of the line kept "
                           "(0 to 1); army: soldiers wanted; navy: ships wanted; works: m2 of the work wanted; reserve: years "
                           "of the standing need held before a surplus is spent; monopoly: true or false; subsidy: money a "
                           "year to the good's producers; mandate: tonnes a year the state buys. null clears a setting",
                  "basis": "a new revenue form's base (see the refusal's choices)",
                  "country": "only your own country is accepted"},
         description="Sets one lever of the government your country seat holds; the next year's budget and revenue read it. "
                     "A seat sets only its own country's levers. Refusals carry a cause: household_seat_has_no_government, "
                     "not_your_country, unknown_lever, unknown_name, unknown_basis, value_not_number, value_out_of_range, "
                     "value_not_boolean, nothing_to_clear; choices lists what would be accepted. Until Complaints 625 and 626 land "
                     "a rate may be any share the form's base allows.")
def _cmd_lever(sim, nodes, cmd, ended):
    if cmd.get("text") and not cmd.get("lever"):
        cmd = dict(_from_text(cmd["text"]), **{key: value for key, value in cmd.items() if key != "text"})
    return set_lever_reply(sim, cmd)


@command("levers", shape="bare", group="society",
         summary="the levers set on your country's government",
         usage=["levers", '{"cmd":"levers"}'],
         description="Lists the levers your country seat has set (revenue rates, budget shares, army, navy, works, reserve, "
                     "subsidies, mandates) and the monopolies its government holds, with the kinds that can be set.")
def _cmd_levers(sim, nodes, cmd, ended):
    government, country, refusal = seat_government(sim, cmd)
    if refusal:
        return refusal
    return {"ok": True, "country": country, "levers": government_levers.current(government.record),
            "kinds": list(government_levers.LEVER_KINDS), "budget_lines": government_levers.budget_line_names()}
