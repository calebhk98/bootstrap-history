# Resolution audit: combined tech-tree realism review, part 05

**Scope:** only `COMBINED_TECH_TREE_REALISM_REVIEW_part_05.md`: English
opening-project rows 108–272 and the complete Mexica opening review.

**Result:** every definite inherited-state, contamination, missing-gate, and
“already known” finding in the final review part is dispositioned. Together
with the earlier audits, all five source parts now have an explicit resolution
record and regression coverage.

## England in 1300

All 52 rows in this file judged `LIKELY ALREADY KNOWN BY 1300` are now explicit
English starting knowledge. They cover writing materials, ordinary medicine,
bloomery and mining practice, joining and finishing crafts, coal and seep
knowledge, textbooks, navigation, rigging, dyeing, tanning, and basic textile
preparation and tools.

Paper remains correctly split: England has imported paper as material, but not
the `rag_paper` production recipe. Consequently hand papermaking, the pulp
stamper, and surface sizing are not inherited through the contaminated baseline
shown in the old report. The remaining generic missing gates are the shared
causal repairs already protected by the part 02 and part 03 tests.

## Mexica opening state

The audit report captured the old civilization-blind ambient grant system. The
current explicit Mexica state keeps its five sound regional seeds—chinampas,
maize, cacao, iron-free monumental stone construction, and obsidian blades—and
none of the 54 definite Old World contaminants listed in this part. Iron,
wheels, glass, Mediterranean materials, Old World medicine, writing media,
ship fittings, and textile forms are therefore not silent starting knowledge.

The report's central remaining scope problem is now fixed rather than worked
around: universal human power and draught-animal power are separate capability
nodes. Every civilization explicitly receives `cap_power_human`; the four Old
World starts also retain `cap_power_muscle`, now accurately named and described
as draught-animal power. The Mexica receive human power but no ox, horse, mule,
or comparable traction capability. Treadwheels, capstans, hand pumps, presses,
and other genuinely human-powered mechanisms use the human gate, while horse
gins and animal treadmills retain the animal gate.

The 40 `BASELINE CONTAMINATED` projects in the historical report no longer
inherit their Old World material or technology prerequisites. Some simple
human-powered projects may still be startable because a modern founder could
attempt them with local inputs; that is legitimate availability, not ambient
inheritance. The 24 `GENERIC MISSING GATE` findings are the same graph repairs
covered by the earlier realism suites.

## Regression protection

`sim/tests/test_realism_part05.py` locks all 52 additional English grants, the
paper-access/production distinction, the five Mexica seeds, exclusion of every
definite contaminant in the report, and the human-versus-animal power split.
