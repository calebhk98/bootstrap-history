"""SMOKE: for complaints 196, 197, 217, 221 and 236, in a fogged England on an unopened game: what `available` returns to a player under fog, and
the hints a refused command gives. The grammar and the filters are called on plain inputs in test_command_search_and_text."""
from .harness import *  # noqa: F401,F403


def scenario(name, **claims):
    """One named scenario check: it passes when every claim holds, and names the claims that do not."""
    failed = sorted(label for label, held in claims.items() if not held)
    check(name, not failed, failed)


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
         a_subject_word_is_refused_as_a_tag_with_the_tags_to_choose=_tag.get("ok") is False and _tag.get("cause") == "unknown_tag"
         and "education" in _tag.get("choices", []) and "optics" not in _tag.get("choices", []),
         offset_past_the_end_lists_none_of_the_matches=_ids(_past) == [] and _past.get("count", 0) > 0)
scenario("scenario: under fog a search never matches a node by its filing cabinet, and a topic word is searched as a word",
         signal_flags_is_in_view=bool(_ids(_signal)) and "com_signal_flags" in _ids(_signal),
         find_electricity_does_not_list_it="com_signal_flags" not in _ids(_electricity_find),
         subject_electricity_does_not_list_it="com_signal_flags" not in _ids(_electricity_subject),
         a_bare_topic_word_returns_what_find_returns=_ids(_physics_subject) == _ids(_physics_find) and _physics_subject.get("count", 0) > 0,
         physics_and_furnace_return_results=all(reply.get("ok") is not False and _ids(reply) for reply in (_physics_subject, _furnace)))

_labour = _ask(_england, cmd="labour", trade="laborer")
scenario("scenario: a small defect stays fixed: `labour laborer` is accepted as the labourer trade",
         labour_laborer_is_accepted_as_labourer=_labour.get("ok") is not False)
