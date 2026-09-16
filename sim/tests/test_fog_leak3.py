"""fog_leak3: split verbatim from the old test_regressions.py (original lines 8671-8786).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# FOG LEAK #3: `bounty` named hidden prerequisites outright where `why` -
# reading the exact same missing list through start_reason's visibility
# filter - correctly said only "N other things you have not heard of yet".
# An external blind playthrough found three examples (industrial zinc
# leaking power_grid, the getter leaking its induction-coupling prerequisite,
# the vacuum tube leaking its hidden cathode) because `bounty` built its own
# "missing prerequisites" list straight off n["pre"], with no fog filter of
# its own. Reproduced generically below rather than pinned to one node name,
# so it keeps catching this the next time a command grows a second copy of
# the missing-prerequisite sentence instead of calling
# missing_prereq_message (fog.py) - the one place this is now written.
# =============================================================================
_bl = sim(capital=1_000_000.0)
_bl.fog = True
_bl.revealed = set()
_bl_cats = ("glass_optics", "metallurgy", "precision", "power", "agriculture",
           "information", "instruments")
_bl_candidates = [k for k, n in NODES.items()
                  if n["cat"] in _bl_cats and n["pre"]
                  and any(p not in _bl.done for p in n["pre"])]
_bl_target = None
_bl_hidden = []
for _k in _bl_candidates:
    _n = NODES[_k]
    _missing = [p for p in _n["pre"] if p not in _bl.done]
    _hidden = [p for p in _missing if not _bl.is_visible(p)]
    if _hidden:
        _bl_target, _bl_hidden = _k, _hidden
        break
check("a bounty-eligible-by-type node with at least one hidden prerequisite "
      "exists to test against - this is a property of the live tree, not "
      "an invented fixture",
      _bl_target is not None, _bl_target)
if _bl_target:
    # HEARD OF THE NODE ITSELF, not its prerequisites - the same state a
    # revealed-but-not-yet-startable entry is in under ordinary play.
    _bl.revealed = {_bl_target}
    _bl_out = S._agent_dispatch(_bl, NODES, {"cmd": "bounty", "id": _bl_target})
    _bl_why = S._agent_dispatch(_bl, NODES, {"cmd": "why", "id": _bl_target})
    check("`bounty` does not print the raw id of a prerequisite the player "
          "has not heard of",
          _bl_out.get("ok") is False
          and not any(h in (_bl_out.get("error") or "") for h in _bl_hidden),
          (_bl_out.get("error"), _bl_hidden))
    check("...and says the same 'N things you have not heard of' shape `why` "
          "gives for the identical node, not a different, leakier sentence",
          "have not heard of" in (_bl_out.get("error") or ""),
          _bl_out.get("error"))
    check("...matching exactly what start_reason/`why` computes for the same "
          "missing list - one fog filter, not two that could drift apart",
          _bl_out.get("error") == _bl.missing_prereq_message(
              [p for p in NODES[_bl_target]["pre"] if p not in _bl.done]),
          (_bl_out.get("error"),
           _bl.missing_prereq_message(
               [p for p in NODES[_bl_target]["pre"] if p not in _bl.done])))

# --- the second half of the same finding: the game told a player "X is
# already active; stop it first if you want to switch to a bounty instead",
# they stopped it, and `bounty` then refused as not bounty-eligible - advice
# to make an irreversible move (losing the hours and money already spent)
# toward an outcome the game could have ruled out before ever suggesting it.
# Find a real node that is tier>2 (never bounty-eligible) and has no missing
# prerequisites, so it can actually be made `active`.
_bls = sim(capital=1_000_000.0)
_bls_target = next((k for k in _bls.order
                    if not _bls.bounty_eligible(k) and _bls.can_start(k)), None)
check("a real, startable, never-bounty-eligible node exists to "
      "test the ordering against",
      _bls_target is not None, _bls_target)
if _bls_target:
    _ok_bls, _why_bls = _bls.start_project(_bls_target)
    check("set-up: the node is actually active",
          _ok_bls and _bls_target in _bls.active, _why_bls)
    _bls_out = S._agent_dispatch(_bls, NODES, {"cmd": "bounty", "id": _bls_target})
    check("bounty on an active, never-eligible node is refused for "
          "ineligibility, not advised to 'stop it first' toward an outcome "
          "that was never going to work",
          _bls_out.get("ok") is False
          and "stop it first" not in (_bls_out.get("error") or ""),
          _bls_out.get("error"))
    check("...and the refusal actually explains why it is not eligible "
          "(tier/category), the real reason, rather than a generic one",
          "not bounty-eligible" in (_bls_out.get("error") or ""),
          _bls_out.get("error"))


# --- BREAK: 'available reverse:true' - the exact key:value spelling
# `help commands` advertises - fell through to the subject branch and was
# read as a search for the literal text "reverse:true", matching nothing,
# with no error. Same shape as the all:true/limit:N hole fixed earlier;
# 'reverse' is a bare flag like 'all', not a value key, and had never been
# added to the colon pre-pass. 'log failures:true' carried the identical
# hole with an even quieter failure (no subject fallback there at all, so
# the flag was just silently dropped).
_rt1, _ = _PT("available sort:risk reverse:true")
check("'available sort:risk reverse:true' parses reverse as the boolean "
      "flag it is, not as a search subject",
      _rt1 == {"cmd": "available", "sort": "risk", "reverse": True}, _rt1)
_rt2, _ = _PT("available reverse:true")
check("...and the same spelling with nothing else on the line still works",
      _rt2 == {"cmd": "available", "reverse": True}, _rt2)
_rt3, _ = _PT("available reverse:false")
check("...and reverse:false means leave it off, the same as never typing "
      "the word, exactly like all:false already does",
      _rt3 == {"cmd": "available"}, _rt3)
_rt4, _ = _PT("log failures:true")
check("'log failures:true' sets the failures flag rather than being "
      "silently dropped",
      _rt4 == {"cmd": "log", "failures": True}, _rt4)
_rt5, _ = _PT("log oldest:true")
check("...and the same fix covers log's other bare-flag words (oldest, "
      "newest, forward, backward, recent), not only 'failures'",
      _rt5.get("order") == "oldest", _rt5)


