"""Scenarios for complaints 196, 197, 217, 221 and 236 in a game: what `available` returns to a player under fog, and
the hints a refused command gives. The grammar and the filters are called on plain inputs in test_command_search_and_text."""
from .harness import *  # noqa: F401,F403


def scenario(name, **claims):
    """One named scenario check: it passes when every claim holds, and names the claims that do not."""
    failed = sorted(label for label, held in claims.items() if not held)
    check(name, not failed, failed)  # presentation: the refusal wording named in each scenario


def _fogged_england():
    """England as the typed game starts it: fog on, the poor scholar's kit (the economy unopened: the research list reads only the tree)."""
    return build_unopened(lambda: S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                                        civ=S.load_civ("england_1300"), cfg={"start_kit": "poor_scholar"}))


_england = _fogged_england()
_england.goal, _england.done_year = GOAL, {}
_england.fog, _england.revealed = True, set()


def _ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


def _ids(reply):
    return [row["id"] for row in reply.get("available", [])]


_all = _ask(_england, cmd="available", all=True, limit=3)
_tag = _ask(_england, cmd="available", tag="optics")
_past = _ask(_england, cmd="available", subject="metallurgy", offset=9999)
_physics_subject = _ask(_england, cmd="available", subject="physics")
_physics_find = _ask(_england, cmd="available", find="physics")
_electricity_find = _ask(_england, cmd="available", find="electricity")
_electricity_subject = _ask(_england, cmd="available", subject="electricity")
_furnace = _ask(_england, cmd="available", subject="furnace")
_signal = _ask(_england, cmd="available", find="signal")

scenario("scenario: under fog `available` pages, refuses a tag that is a subject, and says when an offset is past the end",
         all_with_limit_shows_only_the_limit=len(_all.get("available", [])) == 3,
         tag_refusal_names_both_lists=not _tag.get("ok") and "subject" in _tag.get("error", "") and "education" in _tag.get("error", ""),
         offset_past_the_end_says_so="past the end" in str(_past.get("nothing_matched", "")))
scenario("scenario: under fog a search never matches a node by its filing cabinet, and a topic word is searched as a word",
         signal_flags_is_in_view=bool(_ids(_signal)) and "com_signal_flags" in _ids(_signal),
         find_electricity_does_not_list_it="com_signal_flags" not in _ids(_electricity_find),
         subject_electricity_does_not_list_it="com_signal_flags" not in _ids(_electricity_subject),
         a_bare_topic_word_returns_what_find_returns=_ids(_physics_subject) == _ids(_physics_find) and _physics_subject.get("count", 0) > 0,
         physics_and_furnace_return_results=all(reply.get("ok") is not False and _ids(reply) for reply in (_physics_subject, _furnace)))

_han = sim("han_china_100ad")
_han.end_year = _han.cfg["start_year"] + 50
_ask(_han, cmd="start", id="hom_button")
_ask(_han, cmd="step", years=1)
_ask(_han, cmd="open", id="hom_button")
_closed = _ask(_han, cmd="close", what="hom_button", material="hom_button")
_quoted = _ask(_han, cmd="quote", what="mine", material="hom_button")
_labour = _ask(_han, cmd="labour", trade="laborer")
_ventures = _ask(_han, cmd="ventures", closed=True)
scenario("scenario: refused commands point at the command that exists, and small defects stay fixed",
         close_a_concern_points_at_mothball=not _closed["ok"] and "mothball hom_button" in _closed["error"],
         quote_a_project_names_the_quote_commands=not _quoted["ok"] and "quote open" in _quoted["error"],
         labour_laborer_is_accepted_as_labourer=_labour.get("ok") is not False,
         ventures_closed_says_what_it_shows="closed" in json.dumps(_ventures).lower())
