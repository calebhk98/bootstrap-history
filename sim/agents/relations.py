"""Relations: what one country holds toward another, in the declared `relations` store (data/world/stores.json).

The store is keyed by the ordered pair `country|other_country`; the record under it is that country's own side
toward the other (its stance, trust, treaty terms, tariff, embargo, private note) and a dated history. Anything
that wants to remember how two powers dealt with each other (a tariff, a treaty, a seizure, a gift) writes here
through `set_side` and `record_event`, and anything that decides how a power acts toward another reads here.
Functions take the game's store book (`sim.stores`), so a seat, a state or a mod can use them alike."""
import copy

STORE = "relations"
MAX_HISTORY = 200
MAX_NOTE = 500
# fields other powers may see; the rest (trust, note) is the owner's alone
PUBLIC_FIELDS = ("stance", "treaty", "tariff", "embargo", "history")

DEFAULT_SIDE = {"stance": "neutral", "trust": 0.0, "treaty": {}, "tariff": None, "embargo": False, "note": "", "history": []}


def read(stores, country, other):
    """`country`'s side toward `other`: a copy, the default when nothing is recorded."""
    saved = stores.view(STORE).get((country, other))
    side = copy.deepcopy(DEFAULT_SIDE)
    side.update(copy.deepcopy(saved) if saved else {})
    return side


def set_side(stores, country, other, **fields):
    """Replace the named fields of `country`'s side toward `other` (a `treaty` dict is replaced whole)."""
    unknown = sorted(set(fields) - set(DEFAULT_SIDE))
    if unknown:
        raise KeyError("a relation has no field %s" % ", ".join(unknown))
    side = read(stores, country, other)
    side.update(fields)
    side["note"] = " ".join(str(side["note"]).splitlines()).strip()[:MAX_NOTE]
    stores.view(STORE).set((country, other), None if side == DEFAULT_SIDE else side)
    return side


def set_term(stores, country, other, term, value):
    """Set one treaty term on `country`'s side; a value of None removes it."""
    terms = read(stores, country, other)["treaty"]
    if value is None:
        terms.pop(term, None)
    else:
        terms[term] = value
    return set_side(stores, country, other, treaty=terms)


def record_event(stores, country, other, year, kind, **facts):
    """Append a dated event to both countries' history of the pair. `facts` are JSON values."""
    event = {"year": year, "kind": kind, "facts": facts}
    for first, second in ((country, other), (other, country)):
        history = read(stores, first, second)["history"]
        history.append(copy.deepcopy(event))
        set_side(stores, first, second, history=history[-MAX_HISTORY:])
    return event


def public_view(side):
    """What another power may see of a side."""
    return {field: side[field] for field in PUBLIC_FIELDS}


def partners_with_records(stores, country):
    """Countries `country` has a recorded side toward, sorted."""
    prefix = country + "|"
    return sorted(key[len(prefix):] for key, _value in stores.view(STORE).items() if key.startswith(prefix))


def tariff_on(stores, country, other):
    """The share of a good's value `country` charges on goods crossing from `other` into its markets (0 when none).
    Read straight from the record: prices ask this on every quote."""
    saved = stores.view(STORE).get((country, other))
    return float(saved.get("tariff") or 0.0) if saved else 0.0


def embargoes(stores, country, other):
    """Whether `country` stops goods crossing from `other` into its markets."""
    saved = stores.view(STORE).get((country, other))
    return bool(saved.get("embargo")) if saved else False
