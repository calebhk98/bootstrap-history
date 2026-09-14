"""What the player can see, and what their work is at risk of losing.

Split out of simulator.py, which had grown to 5,600 lines. These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and verified byte-identical.
"""
import collections, json, math, os, random, re
from collections import defaultdict

from .data import *          # the shared tables and loaders
from .data import (closure, load)


# THE GAME TELLING YOU WHAT IS IMPORTANT IS THE GAME PLAYING ITSELF. A user
# asked, about a different number entirely, "shouldn't the payback be
# something you don't know until after research?" - and a normal-play tester
# found the same fault in prose rather than in a figure: school_founded's own
# note calls itself "the pivot of the entire game" and says "every year of
# delay here costs more than any single technology", and corpus_dispersed's
# says outright that it is "THE highest expected-value node in the tree".
# Under fog, which branch matters most is exactly the decision fog exists to
# leave to the player; a sentence that grades a node against the rest of the
# tree answers that question for them as plainly as a number would, fog or no
# fog, because it is the designer's own ranking, not something the founder in
# the story could know. It is cut everywhere a node's note is shown, not only
# under fog, because telling a player outright which of their own choices is
# correct is the same move whether or not the rest of the tree is hidden.
#
# NARROW ON PURPOSE, same lesson as FOREIGN_MARKERS and NEVER_ABANDON below.
# A sentence only qualifies if it BOTH names the game or the tree itself AND
# makes a ranking claim about it ("highest", "pivot", "largest single", ...),
# or matches one of the handful of exact phrases below that rank a node
# without naming "game"/"tree" in so many words ("costs more than any single
# technology", "must not cut"). A sentence that calls something "the most
# important instrument" a pilot has, or Cayley's discovery "his single most
# important insight", is a true statement about the real world and survives -
# it never mentions the game or the tree at all. Only a sentence that steps
# outside the fiction to grade the tree's own node against the rest of the
# tree is self-play, and only those are dropped. Deliberately NOT touched:
# "Nothing in the technical tree requires it. You may decline..." on
# school_founded's own note - stating that a thing is optional is the
# opposite of the fault this exists to fix, and "the whole game" on
# point_contact_transistor's note ("Getting here from 100 AD is the whole
# game") is left alone too, because the goal's own identity is already known
# under fog by design - see help's "what you are trying to do".
_SELF_PLAY_PHRASES = (
    "pivot of the entire game",
    "costs more than any single",
    "highest expected-value node in the tree",
    "highest expected-value defensive investment",
    "highest-leverage thing you can spend money on",
    "is simply the highest-leverage",
    "largest single call on your personal hours",
    "must not cut",
    # AND TELLING YOU WHAT TO DO FIRST, which is the same offence in the
    # imperative rather than the comparative and so slipped past both the
    # phrase list and the meta-plus-ranking test. Under fog, what to build
    # first IS the question being asked of the player. A user reading the
    # game found these after the ranking claims were already cut; there are
    # only two in the whole tree, so they are named rather than pattern
    # matched, because a broad rule for imperatives would eat the recipe
    # instructions that are the point of the note field.
    "do this before writing any other recipe down",
    "build it first, use it to learn",
)
_SELF_PLAY_META = re.compile(
    r"\b(the game|this game|the entire game|the tree|this tree)\b", re.I)
_SELF_PLAY_RANK = re.compile(
    r"\bhighest\b|\blargest\b|\bpivot\b|\bmost important\b|\bsingle most\b", re.I)


def strip_self_play_advice(text):
    """Drop any sentence that ranks a node against the game or the tree,
    and hand back what is left. See the block comment above for why, and
    for exactly what does and does not qualify.
    """
    if not text:
        return text
    parts = re.split(r'(?<=[.!?]) ', text)

    def _is_self_play(p):
        low = p.lower()
        if any(ph in low for ph in _SELF_PLAY_PHRASES):
            return True
        return bool(_SELF_PLAY_META.search(p) and _SELF_PLAY_RANK.search(p))

    return " ".join(p for p in parts if not _is_self_play(p)).strip()


class FogMixin:
    # FOG IS A RATCHET, NOT A REWIND. A tester found the exploit in as many
    # words: "since `load` restores the game but not the player's memory, a
    # player can save, build a node, look at what appeared in `available`,
    # load back, and keep the knowledge. Fog of war is one command away from
    # being off" (playtest/AUDIT_rounds_1_6.md, C1), reproduced live - save at
    # year 1300, step to 1350, load the 1300 save, and the fifty years of
    # frontier `available` had shown cost nothing at all, because the ledger
    # went back to 1300 and the knowledge did not. The dishonest half is not
    # that reload fails to un-teach a human who already read a name - no save
    # format can do that - it is that reload also handed back every denarius
    # and year that discovery cost, for free, as many times as you like.
    #
    # The fix is a property instead of a plain attribute, so it holds
    # regardless of WHICH code assigns to `.revealed` - load_state
    # (protocol.py) is the path the exploit uses, but this does not require
    # editing it or knowing about every future caller: assigning a smaller
    # set here only ever grows what is already known, never shrinks it. A
    # genuinely fresh Sim is untouched - the first assignment ever made (both
    # `play` and `agent` set `s.revealed = set()` right after construction,
    # before any `load_state`) has nothing to union with yet, so it is a
    # plain replace, exactly as before this existed.
    @property
    def revealed(self):
        return self.__dict__.get("_revealed", set())

    @revealed.setter
    def revealed(self, value):
        cur = self.__dict__.get("_revealed")
        self.__dict__["_revealed"] = (set(value) if cur is None
                                      else set(cur) | set(value))

    def reveal_from(self, k):
        """Completing something teaches you what it leads towards, vaguely."""
        if not getattr(self, "fog", False):
            return
        self.revealed = set(getattr(self, "revealed", set()))
        self.revealed.add(k)
        for other, n in self.nodes.items():
            if k in n.get("pre", []):
                self.revealed.add(other)
            for g in n.get("req_any", []):
                if k in (g.get("options") or {}):
                    self.revealed.add(other)

    def is_visible(self, k, _memo=None):
        """Can the player see this node at all?

        _memo: an optional dict shared across one recursive descent. is_visible
        calls start_reason, and start_reason calls is_visible on every missing
        prerequisite of a node with missing prerequisites - which, on a node
        deep in the tree, is every one of ITS missing prerequisites too. Without
        sharing one memo down that whole call tree, checking visibility of a
        single deep node re-derived the visibility of common ancestors once per
        path to them, which is exponential in the depth of the tree. A profiler
        on `can_start('dynamo')` on norse_900ad under fog counted 12,465 nested
        calls to start_reason from three top-level ones, at 0.45s each; a plain
        `available` call, which checks all ~2,800 nodes this way, did not return
        in 60 seconds. The memo makes one recursive descent O(nodes touched)
        instead of O(paths to them); a fresh dict per outward-facing call (the
        default) keeps it exact - nothing here is cached ACROSS commands, so a
        node built or revealed between one call and the next is seen correctly
        next time.
        """
        if not getattr(self, "fog", False):
            return True
        if k in self.done or k in self.active:
            return True
        if k in getattr(self, "revealed", set()):
            return True
        memo = {} if _memo is None else _memo
        if k in memo:
            return memo[k]
        memo[k] = False        # provisional: the tree is a DAG so this should
                                # never actually be read back, but a cycle must
                                # not recurse forever if one ever sneaks in.
        # anything you could start right now is visible by definition: you can
        # see the work in front of you even if you cannot see past it
        #
        # _why=False: this discards start_reason's message too - is_visible
        # only ever wants the boolean - and it is what turns the recursive
        # descent (this function calls start_reason, which calls
        # missing_prereq_message, which calls is_visible on every missing
        # prerequisite, which calls back into start_reason...) from building
        # a player-facing sentence at every single level into building one
        # only at the outermost call that actually asked for it.
        result = self.start_reason(k, _memo=memo, _why=False)[0]
        memo[k] = result
        return result

    def missing_prereq_message(self, missing, _memo=None):
        """Format a list of not-yet-done prerequisite ids as one player-facing
        message, filtered through the same visibility test `start_reason`
        (and so `why`) applies. A second caller computing its own missing
        list and printing the ids raw is exactly how `bounty` leaked
        industrial zinc's power_grid, the getter's induction-coupling
        prerequisite and the vacuum tube's hidden cathode: the filter lived
        in start_reason alone, and nothing stopped a second command from
        skipping it. There must be exactly one way to turn "missing" into
        words.
        """
        if not missing:
            return None
        known = [p for p in missing if self.is_visible(p, _memo=_memo)]
        hidden = len(missing) - len(known)
        if not getattr(self, "fog", False) or not hidden:
            msg = "missing prerequisites: " + ", ".join(missing)
            return msg + self._free_prereq_hint(missing)
        bits = []
        if known:
            bits.append("missing prerequisites: " + ", ".join(known))
        bits.append("%d other thing%s you have not heard of yet"
                    % (hidden, "" if hidden == 1 else "s"))
        msg = "; and ".join(bits) if known else \
            ("this needs %s, and you do not yet know what %s"
             % (bits[-1], "they are" if hidden > 1 else "it is"))
        # ONLY EVER THE VISIBLE ONES. `known` is already the fog filter this
        # whole method exists to apply, so the hint is built from it and a
        # hidden prerequisite is never named by the hint either.
        return msg + self._free_prereq_hint(known)

    # WHAT IT COSTS TO SAY YES. Eight nodes in this tree - cap_measure_temp,
    # cap_measure_elec, cap_measure_mass_mg, cap_measure_time_s,
    # cap_power_water, cap_power_steam, cap_power_electric, cap_power_grid -
    # cost nothing, take no hours, take no years and cannot fail. They are the
    # engine's way of saying "you built a thermometer, so now you can measure
    # temperature", and a player still has to start each one by hand.
    #
    # A player who won this game called that out: "thermometer completion does
    # not itself satisfy later high-temperature work until the zero-cost
    # cap_measure_temp capability is separately started/completed. Mechanically
    # consistent with the game's knowledge/capability distinction, but can feel
    # administrative." They are right that it is consistent and right that it
    # reads as paperwork, and the refusal they were reading said only "missing
    # prerequisites: cap_measure_temp" - a name, with no indication that the
    # thing behind it is free and one command away.
    #
    # NOT AUTO-GRANTED, deliberately. Each of these carries 20 a year of
    # upkeep if it is ever OPENED, so completing them on the player's behalf
    # would be spending their money on a decision they were never asked about.
    # They do not need opening to satisfy a prerequisite - start_reason tests
    # `p not in self.done`, not operating - so the honest fix is to say what
    # the refusal was already about: this one is free, start it.
    FREE_PREREQ_NAMED_AT_MOST = 3

    def _free_prereq_hint(self, missing):
        """", and X costs nothing..." for whichever missing prerequisites are
        free, instant and startable right now - or "" when none are."""
        ready = []
        for p in missing:
            n = self.nodes.get(p)
            if not n:
                continue
            if ((n.get("_total_cost") or 0) > 1 or (n.get("ph") or 0) > 0
                    or (n.get("yrs") or 0) > 0 or (n.get("risk") or 0) > 0):
                continue
            # ONLY IF THEY CAN ACT ON IT NOW. Naming a free node that is
            # itself blocked is not help, it is a second refusal wearing the
            # first one's clothes.
            if all(q in self.done for q in n["pre"]):
                ready.append(p)
        if not ready:
            return ""
        ready = ready[:self.FREE_PREREQ_NAMED_AT_MOST]
        if len(ready) == 1:
            return (". %s costs nothing, takes no time and cannot fail: "
                    "start %s" % (ready[0], ready[0]))
        return (". %s cost nothing, take no time and cannot fail: start "
                "them now (%s)"
                % (", ".join(ready), ", ".join("start " + p for p in ready)))

    def fog_scrub(self, text):
        """Strip node ids the player has not discovered out of a message."""
        if not text or not getattr(self, "fog", False):
            return text
        out = text
        for k in self.nodes:
            if k in out and not self.is_visible(k):
                out = out.replace(k, "something you have not heard of")
        return out

    def fog_summary(self, k):
        """One sentence. Deliberately not the whole note, and never the unlocks."""
        # Stripped before the first sentence is taken, not after: school_
        # founded's note OPENS with "The pivot of the entire game." - the
        # exact sentence fog_summary would otherwise hand back as the whole
        # answer, under fog, for the one command whose entire job is to stay
        # vague. See strip_self_play_advice above.
        note = strip_self_play_advice((self.nodes[k].get("note") or "").strip())
        if not note:
            return self.nodes[k]["name"]
        for sep in (". ", "? ", "! "):
            if sep in note:
                note = note.split(sep)[0].strip() + "."
                break
        # Hard cap. A "one sentence" summary that runs to 160 characters, times
        # thirty entries in a list, is most of the reply.
        return note if len(note) <= 110 else note[:107].rstrip(" ,;") + "..."

    def knowledge_risk(self):
        """How exposed your finished work is to being forgotten, and to what.

        A playtester read the guide's warning about the Third Century Crisis,
        then reasonably decided to skip the academies because `path` told them,
        correctly, that no academy is a technical prerequisite of a transistor.
        They then lost 25 technologies in one year, 24 more nine years later,
        and 16 more after that, and rebuilt them while the goal stood still.

        Their complaint is the sharp one: this project's whole thesis is that
        the technical dependency graph is not the real dependency graph, and
        the protocol was exposing only the technical graph. The risk existed
        solely as prose, in a knowledge file, attached to the MITIGATION rather
        than to anything the player could see while deciding. A tool that shows
        you one graph while the guide insists a second one governs you is a tool
        that misleads by omission.

        So the numbers behind the dice are now readable while there is still
        time to act on them.
        """
        # `has`, NOT running(): every other capability in this engine was moved
        # onto running() - a school with nobody paid to keep it open trains
        # nobody - and this one deliberately stays where it is. Books that
        # exist are books that exist, and a play tester had already reported
        # the opposite reading as a bug, having lost their corpus to a sacking
        # and assumed the hedge had followed `operating`. See Sim.corpus_hedge
        # (core.py): the sack itself calls the same method, so this screen
        # cannot quote a hedge the sack does not honour.
        chance, frac, hedge = self.corpus_hedge()
        at_risk = sum(1 for k in self.done if self.nodes[k]["tier"] >= 2)
        # WHAT YOU HAVE ALREADY LOST, and have to build again. Without this the
        # only record of a sacking is a log line a century back, and a play
        # tester discovered theirs one refusal at a time - "missing
        # prerequisites: <thing you built two hundred years ago>".
        _gone = sorted((k for k, _y in (getattr(self, "forgotten", None) or {}).items()
                        if k not in self.done),
                       key=lambda k: -(self.forgotten[k]))
        upcoming = []
        for h in (self.civ.get("hazards") or []):
            yrs = h.get("years") or []
            if not yrs:
                continue
            y0 = yrs[0]
            y1 = yrs[1] if len(yrs) > 1 else yrs[0]
            if self.year > y1:
                continue                      # already survived, or missed
            row = {"name": h.get("name", "hazard"),
                   "years": [y0, y1],
                   "in_progress": y0 <= self.year <= y1,
                   "sacks_a_site": bool(h.get("sack_chance")),
                   "sack_chance_per_year": h.get("sack_chance"),
                   "staff_loss": h.get("staff_loss"),
                   "note": h.get("note")}
            # WHAT YOU CAN DO ABOUT IT. Every hazard here is fightable, and
            # until now nothing said so: testers watched the plague arrive on
            # the year they were told it would and treated it as weather.
            row["what_you_can_do"] = {}
            for kind in ("staff_loss", "sack_chance", "output_factor", "real_erosion"):
                if kind in h or (kind == "sack_chance" and h.get("sack_chance")):
                    row["what_you_can_do"][kind] = self.hazard_advice(kind)
            if "sack_chance" in h:
                row["sack_chance_after_what_you_have_built"] = round(
                    h["sack_chance"] * self.hazard_relief("sack_chance")[0], 4)
            if "staff_loss" in h:
                row["staff_loss_after_what_you_have_built"] = round(
                    h["staff_loss"] * self.hazard_relief("staff_loss")[0], 4)
            upcoming.append(row)
        # WHAT IS ACTUALLY NEAR, in full, and the rest by name. Every dated
        # hazard now carries a real historical note and England has fifteen of
        # them; sending all of it made one `risk` reply seventeen thousand
        # bytes, which is the wall this whole interface was broken up to stop
        # producing. A player deciding what to do this decade does not need
        # four hundred words on enclosure in 1700.
        _soon = [r for r in upcoming
                 if r.get("in_progress") or (r["years"][0] - self.year) <= 120]
        _later = [r for r in upcoming if r not in _soon]
        if _later:
            for r in _later:
                r.pop("note", None)
                r.pop("what_you_can_do", None)
        upcoming = _soon[:6] + _later
        if len(_soon) > 6:
            upcoming = _soon[:6]
            for r in _soon[6:] + _later:
                r.pop("note", None)
                r.pop("what_you_can_do", None)
                upcoming.append(r)
        # Norse hazards do not sack anything, and a playtester watched this
        # advertise a loss risk and recommend a hedge for a full 500 year run in
        # which no sacking could ever occur. Risk you cannot face is not risk.
        # A COMPACT CHRONOLOGICAL VIEW, sorted nearest-first, that says the
        # same thing `known_hazards_ahead` says in scattered, per-kind detail
        # but ESCALATES as a date closes in rather than repeating itself -
        # see hazard_timeline's own comment (society.py) for why "hedged_by:
        # nothing yet" sitting unchanged on this screen for a hundred and
        # fifty years was the actual defect, not merely the lack of a list.
        timeline = self.hazard_timeline()
        can_be_sacked = any(h.get("sacks_a_site") for h in upcoming)
        if not can_be_sacked:
            return {
                "technologies_at_risk": at_risk,
                "loss_chance_if_a_site_is_sacked": round(chance, 2),
                "fraction_lost_when_it_happens": round(frac, 2),
                "expected_technologies_lost_per_sacking": 0.0,
                "hedged_by": hedge,
                "better_hedge_available": None,
                "note": "no remaining hazard for this civilization sacks a site, "
                        "so nothing here is currently at risk of being forgotten",
                "critical_capabilities_not_operating": self.capability_gaps() or None,
                "known_hazards_ahead": upcoming,
                "timeline": timeline,
            }
        return {
            "technologies_at_risk": at_risk,
            "loss_chance_if_a_site_is_sacked": round(chance, 2),
            "fraction_lost_when_it_happens": round(frac, 2),
            # PER SACKING means the sacking has already happened, so `chance`
            # - which is the probability that a sacking costs you anything at
            # all - must not be applied a second time. A break tester summed
            # the numbers on this screen against what a sacking actually took
            # and found this 20% low, which is exactly 1 - 0.8.
            "expected_technologies_lost_per_sacking": round(at_risk * frac, 1),
            "and_the_chance_a_sacking_costs_you_anything": round(chance, 2),
            # done versus operating, on the ONE screen whose whole job is
            # telling you what protects you. `hedged_by` below only answers
            # the sack hedge (has(), by design - see corpus_hedge); this
            # answers everything else this run has completed but let lapse.
            "critical_capabilities_not_operating": self.capability_gaps() or None,
            **({"you_have_already_lost": len(_gone),
                "and_have_to_build_again": _gone[:10],
                "the_most_recent_went_in": self.forgotten[_gone[0]]} if _gone else {}),
            # Under fog, do not name a node the player has not discovered. A
            # tester was told in `state` that corpus_dispersed would hedge them,
            # asked `why` about it, and was told they had never heard of it.
            # Both replies came from the same program in the same second.
            "hedged_by": hedge if (not getattr(self, "fog", False)
                                   or self.is_visible(hedge or "")) else "nothing yet",
            "better_hedge_available": (
                None if hedge == "corpus_dispersed" else
                ("corpus_dispersed" if not getattr(self, "fog", False)
                 else "there is said to be a way to guard against this; "
                      "you have not found it yet")),
            "known_hazards_ahead": upcoming,
            "timeline": timeline,
        }

    # Institutions that belong to one named society. Granting them to everyone
    # was the bug; refusing to let anyone else BUILD them would be a worse one,
    # because a founder can perfectly well introduce an aqueduct to Tenochtitlan.
    # This only blocks the free gift.
    # Standing, knowledge and persona are not plant. They carry upkeep because
    # they cost you to maintain, and they cannot be let go to save money the way
    # a mill or a mine can. A playtester went bankrupt and the abandonment
    # mechanic shed `identity_cover`, which is a persona AND a real prerequisite
    # of the goal, and they sat softlocked for 470 years unable to rebuild it.
    # Knowledge cannot be repossessed. Everything else can lapse.
    #
    # This started as a broad category list, added to stop bankruptcy shedding
    # `identity_cover` and softlocking the run. It then caused the opposite
    # problem: it protected patron_local, collegium_licensed, freedman_staff and
    # workshop_first, which between them carried 3,380 denarii of upkeep against
    # 1,501 of revenue, so a ruined run could never stop bleeding and recovery
    # took centuries. Both of those are real. A patronage can lapse and a
    # workshop can close; what you cannot lose is who you are and what you know.
    #
    # A tester watched creditors make the founder forget Newton's laws
    # (sc2_physics_newtons_laws, cat "physics", up 40) - already covered above
    # - and separately watched abstract science and medicine outside pure
    # mathematics go the same way: cell theory, DNA, the phase diagram of
    # iron, none of them a building, all of them carrying real upkeep (40 to
    # 400 denarii, from "keeping up scholarly correspondence" rather than rent)
    # and so all of them ELIGIBLE under the up-exceeds-revenue test that gates
    # both shed_loss_makers and enforce_credit_limit's seizure. "theory" and
    # "knowledge" are what the tree itself calls these categories, which is
    # the same evidence "physics" and "mathematics" were added on: you cannot
    # be made to un-know a thing to balance a ledger, whatever it is filed
    # under. NARROW ON PURPOSE, same lesson as FOREIGN_MARKERS below: most
    # knowledge (tex_drop_spindle, "basic textile technique", among it) costs
    # nothing to keep and was never at risk, needing no protection here at
    # all - see the note on that in never_abandon's caller. This list is only
    # for the knowledge that DOES carry upkeep and would otherwise be shed for
    # it.
    NEVER_ABANDON = {"mathematics", "physics", "method", "notation",
                     "algebra", "geometry", "probability", "analysis",
                     "theory", "knowledge"}

    def never_abandon(self, k):
        """Protected: knowledge, and anything the goal actually needs.

        Keying the softlock guard on the GOAL CLOSURE rather than on a list of
        category names is what makes both halves work. You can let a patron go
        and rebuild him later; you cannot have the game quietly delete a step
        you need and then refuse to fund rebuilding it.
        """
        if self.nodes[k]["cat"] in self.NEVER_ABANDON:
            return True
        if not hasattr(self, "_goal_closure"):
            try:
                self._goal_closure = closure(self.nodes, self.goal)
            except Exception:
                self._goal_closure = set()
        return k in self._goal_closure

    FOREIGN_MARKERS = ("_roman", "_rome", "annona", "insula", "societas",
                       "collegium", "argentarii", "latifundi",
                       # The cursus publicus is the Roman imperial dispatch
                       # relay and the Pharos is one specific Ptolemaic
                       # building at Alexandria. Neither is a generic capability
                       # any society might have, and with no marker of their own
                       # both were being handed free to Han and to the Norse -
                       # the last two of the thirteen Roman-branded grants that
                       # testers kept finding in other people's civilisations.
                       "cursus", "pharos")

    # A Roman masonry arch is a way of laying stone and anyone can learn it. The
    # annona is the Roman state's grain dole and Roman citizenship is a status
    # only Rome can confer, and neither is a thing you can BUILD in Luoyang.
    # A tester played five hundred years of Han China with `citizenship`
    # ("the difference between a governor executing you and Rome hearing you")
    # sitting in their available list the whole time, and called it what it was:
    # unfinished civilization gating rather than a deliberate choice.
    # NARROW, and I made this too wide first time and broke Han China with it.
    # Blocking anything with "collegium" in the name cut the licensed
    # association out of the tree, and with it school_founded, endowment_land,
    # academy_network and both patronage tiers, which is the entire
    # institutional ladder: Han finished 156 of the 168 nodes the transistor
    # needs and then failed for want of eighteen craftsmen it had 320 million
    # denarii to hire. Every society has partnerships, money-lenders and
    # licensed associations under its own names, and the Han even had a grain
    # stabilisation office. What no other society has is Roman citizenship,
    # because only Rome can confer it. That is the whole list.
    # And in the end the list is empty, which is the right answer. My first
    # version blocked six markers and cut Han China off from the whole
    # institutional ladder. Narrowing it to Roman citizenship alone moved the
    # wall one node back, because the licensed association requires legal
    # standing, and a model in which only Romans can have legal standing is
    # worse than the flavour-text problem it was fixing. `citizenship` is now
    # what it always modelled - a status the courts will hear - and every
    # society has one under its own name. What remains civ-specific is which
    # institutions you are GRANTED for free, which FOREIGN_MARKERS still
    # handles: the Han are not handed the annona.
    FOREIGN_INSTITUTIONS = ()
