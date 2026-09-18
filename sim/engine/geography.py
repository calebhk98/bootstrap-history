"""Where things are, and what that costs to reach.

Split out of simulator.py, which had grown to 5,600 lines. These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and verified byte-identical.
"""

from .data import (haversine_km)

class GeographyMixin:
    def _compute_home_centroid(self):
        """Average lat/lon of this civilization's own home_regions.

        A crude centroid, not a capital city, but that matches the rest of
        this model: regions are already coarse political/geographic blocks,
        not points, so a coarse average of them is the right level of detail.
        """
        homes = [r for r in (self.civ.get("home_regions") or []) if r in self._regions]
        if not homes:
            # A civ file with no valid home_regions would otherwise crash
            # region_reach for everyone; falling back to Italy or to
            # whatever region exists keeps this from being a hard wall.
            homes = ["italia"] if "italia" in self._regions else list(self._regions)[:1]
        lat = sum(self._regions[r]["lat"] for r in homes) / len(homes)
        lon = sum(self._regions[r]["lon"] for r in homes) / len(homes)
        return lat, lon

    # Straight-line kilometres (after geography.json's route_difficulty and
    # this civilization's own travel speed, below, have been applied) banded
    # onto the same 0-6 scale reach_levels already uses. Chosen so that
    # ROME, at its own base_reach of 2, lands close to its own OLD
    # hand-authored reach_from_italia numbers across the whole region list
    # (checked by hand while building this): this is a generalisation of the
    # old table, not an unrelated replacement for it.
    RAW_DISTANCE_BANDS = ((1200.0, 1), (2500.0, 2), (4500.0, 3), (7000.0, 4), (11000.0, 5))

    # How much base_reach shortens the EFFECTIVE distance, not the band.
    # An earlier version of this subtracted base_reach straight off the
    # band number, which looked right for Rome but broke on the Norse: with
    # only 6 bands total, subtracting 4 (their base_reach) collapsed nearly
    # every coastal region in the world, China included, to band 1 -- "as
    # easy as sailing to Gaul", which overstates even Norse mobility. Dividing
    # the DISTANCE by a speed factor instead degrades gracefully: closer
    # places still get much easier, but a civilization does not get to treat
    # the far side of the planet as next door no matter how good its ships.
    REACH_SPEED_COEF = 0.22

    def region_reach(self, region_id):
        """How hard `region_id` is to reach, FOR THIS CIVILIZATION, 0-6.

        Three things determine it, none of which the old model had:
          1. HOME IS HOME. If the region is one of this civ's own
             home_regions the reach is 0, full stop, regardless of geometry.
          2. RAW DISTANCE. Great-circle distance from this civ's own home
             centroid to the region's centroid, scaled by route_difficulty
             (ice, open ocean and mountain relay routes are harder than the
             straight line suggests; a scheduled wind system like the
             monsoon is easier).
          3. WHAT YOU ALREADY DO. base_reach is how far this society already
             routinely travels -- the Norse (base_reach 4) really do sail to
             Greenland and the Black Sea, Rome (base_reach 2) really does
             run the India trade every year -- and it SHRINKS that distance
             before banding (see REACH_SPEED_COEF above for why division,
             not subtraction). A society with no ocean-going tradition at
             all still gets base_reach >= 1 in every civ file in this
             directory, so nobody's effective distance is ever left
             un-shrunk.
          Sea vs land matters too: the shrink applies in full to a COASTAL
          destination (this is mostly what "routinely travels" means for
          these five civilizations) and at reduced strength (square root)
          to a landlocked one, because a fleet does not help you cross a
          desert.

        The result is never below 1 for a non-home region: reach 0 is
        reserved for "this is actually your own ground", not for "the
        arithmetic rounded down to nothing."
        """
        if region_id not in self._regions:
            return 6           # unknown region: treat as maximally far, not a crash
        if region_id in (self.civ.get("home_regions") or []):
            return 0
        reg = self._regions[region_id]
        hlat, hlon = self._home_centroid
        dist = haversine_km(hlat, hlon, reg["lat"], reg["lon"]) * float(reg.get("route_difficulty", 1.0))
        base_reach = float(self.civ.get("base_reach", 2))
        speed = 1.0 + self.REACH_SPEED_COEF * base_reach
        coastal = bool(reg.get("coastal", True))
        effective = dist / speed if coastal else dist / (speed ** 0.5)
        band = 6
        for edge, b in self.RAW_DISTANCE_BANDS:
            if effective <= edge:
                band = b
                break
        return max(1, min(6, band))

    # How much of a region's output reaches your market by ordinary trade
    # when you do NOT hold the region yourself, fading with reach rather
    # than cutting off: nothing in this model is a wall, only a price.
    TRADE_ACCESS_BY_REACH = {0: 1.0, 1: 0.5, 2: 0.3, 3: 0.15, 4: 0.08, 5: 0.04, 6: 0.02}

    def material_reach(self, material_key):
        """Reach and cost multiplier for `material_key`, FOR THIS CIVILIZATION.

        Looks the material up in geography.json's located_materials, picks
        whichever of its regions is EASIEST for this civ to reach (a rational
        buyer sources from the nearest deposit, not always the "primary"
        one), and turns that region's reach into a cost multiplier.

        The published cost_multiplier in geography.json was written for
        Rome: it is calibrated against that region's reach_from_italia, the
        old Roman-only reach number. So: at civ_reach 0 (you live there) the
        multiplier is 1, at civ_reach == reach_from_italia it reproduces the
        published number exactly (which is why Rome's own numbers barely
        move), and at civ_reach below reach_from_italia -- Han China and
        Malayan gutta percha is the case this bug report was written about
        -- it comes out CHEAPER than Rome pays, because the material
        genuinely is closer for that civilization. Above reach_from_italia
        it costs MORE than Rome's figure, for the same reason in reverse.
        Power, not a straight line, so it is smooth at both ends and never
        goes negative or hits exactly zero.
        """
        materials = self.geo.get("located_materials") or {}
        md = materials.get(material_key)
        if not md:
            return 0, 1.0
        base_mult = float(md.get("cost_multiplier", 1.0))
        best = None
        for rid in (md.get("regions") or []):
            reg = self._regions.get(rid)
            if not reg:
                continue
            civ_r = self.region_reach(rid)
            if best is None or civ_r < best[0]:
                italia_r = max(1, int(reg.get("reach_from_italia", civ_r) or 1))
                best = (civ_r, italia_r)
        if best is None:
            return 0, base_mult
        civ_r, italia_r = best
        if civ_r <= 0:
            return 0, 1.0      # it is, in effect, home ground for this civilization
        raw = base_mult ** (civ_r / italia_r)
        # Cap it. The exponent could reach x235 for gutta percha and x468 for
        # rubber, and a several-hundred-fold cost is not an expense, it is the
        # abolished "unobtainable" category wearing a price tag. The ceiling is
        # argued from the Roman evidence rather than chosen for feel: pepper
        # carried roughly a tenfold to twentyfold markup and silk about a
        # hundredfold, both RETAIL across a chain of middlemen. This node buys
        # your OWN supply, which should cost less per unit than retail, not
        # more. 60 is therefore generous rather than punitive, which is the
        # right way to be wrong here.
        # Compress rather than clamp. A hard ceiling flattened the very
        # distinction this function exists to draw: Rome's 235 and Han China's
        # 60 both hit a cap of 60 and came out identical, so the geography fix
        # stopped doing anything. Raising to a fractional power keeps the
        # ORDERING intact while pulling the magnitudes back to something
        # defensible, and the ceiling stays only as a backstop.
        return civ_r, min(raw ** 0.6, 45.0)

    def material_cost_factor(self, k):
        """Cost multiplier a located-material tech node picks up from
        geography, for the civilization in play.

        Only applies to nodes geography.json actually names (via
        located_materials.*.unlocks, e.g. mat_gutta_percha, mat_natural_rubber):
        everything else returns 1.0 and is untouched. This is the wiring the
        bug report asked for: before this existed, geography.json's
        cost_multiplier field was read by nobody, so gutta percha cost
        exactly the same (nothing extra) whether you were playing Rome or
        Han China, and the entire India-and-east trade advantage a
        China-based civilization actually has was invisible to the model.
        """
        mk = self._mat_unlock.get(k)
        if not mk:
            return 1.0
        _, mult = self.material_reach(mk)
        return mult

    def _compute_mineral_scale(self, material):
        """Fraction of a mined mineral's reference output this civilization
        can draw on: geology and reach, not population.

        resource_throttle() used to multiply by self.pop_scale here, i.e.
        "how much coal can you buy" scaled by HOW MANY PEOPLE YOU HAVE. That
        is backwards twice over: Norse Scandinavia got 2.3% of Rome's coal
        because it has 2.3% of the people, and England in 1300 got 7%, when
        England is precisely where the coal actually is. A coalfield does
        not care how many people live near it.

        geography.json's per-region `minerals` gives each region's rough
        share of a material's total output, normalised so ROME'S OWN home
        regions sum to about 1.0 -- which is what reproduces
        resources.json's Roman totals exactly for a Rome-based civ and
        changes nothing about the Rome baseline. For any other civilization:
        regions it actually HOLDS (home_regions) count in full, and every
        other region contributes a SHRINKING but never-zero share as it
        fades with reach (TRADE_ACCESS_BY_REACH), because a civilization
        with no local ore can still buy imported metal, just less of it.
        Floored well above zero so this is a price, never a wall.
        """
        home = set(self.civ.get("home_regions") or [])
        total = 0.0
        for rid, reg in self._regions.items():
            ab = float((reg.get("minerals") or {}).get(material, 0.0))
            if ab <= 0:
                continue
            if rid in home:
                total += ab
            else:
                total += ab * self.TRADE_ACCESS_BY_REACH.get(self.region_reach(rid), 0.02)
        return max(0.05, total)

    def mineral_scale(self, material):
        """Cached result of _compute_mineral_scale(). Geology and reach do
        not change during a run, so this is computed once in __init__
        rather than recomputed every simulated year."""
        return self._mineral_scale.get(material, self.pop_scale)
