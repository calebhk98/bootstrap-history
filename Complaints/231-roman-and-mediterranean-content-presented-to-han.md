# Roman and Mediterranean content is presented as local fact and startable in a Han campaign

**Status:** open

Evidence on the current branch (Han, 100 AD, `available` and the node notes):

- Startable at the start: Roman cosmetics (`hom_cosmetics_roman`), Roman masonry arch, Roman fired brick and tile, "Chorobates: Roman water level", "Groma: Roman X-staff", Murex purple dyeing,
  Cursus publicus courier service, Pharos lighthouse, theatre and pantomime, public bath (thermae), a hypocaust. The tester also found tea import and Roman-style `iugerum` land units.
- Notes address Rome: the scientific method says contradicting Aristotle and Galen in public is a social act and their defenders hold the chairs; the semaphore note speaks of the Rhine and an emperor; the
  medical-statistics note lists "software automation"; `rag_paper` says Cai Lun's paper "will not reach the Mediterranean" (true, but advice aimed at another player); corpus dispersal is "Britain to India".
- The kit screen for a Han game names "the equestrian census" and "senatorial fortunes" (`sim/engine/data.py`, `STARTING_KITS`).
- `semaphore_telegraph` requires `patron_senatorial`; a Han player sees an unknown prerequisite they cannot identify (the civ file localises the phrase "Senatorial patronage", not the id).

Design note already in the repo: `data/civilizations/han_china_100ad.json` has a `local_words` table of four phrase pairs and says "Historical notes ABOUT Rome are not rewritten: they are about Rome."
So part of this is deliberate. The complaint is the remainder: nodes that are Roman artefacts offered as Han options, and advice written in the second person that names the wrong place.

What it would take: mark nodes with the civilisations they apply to (or an "import" flag) so a Han game does not offer Roman-only artefacts as if local; widen `local_words` or split notes into a neutral
sentence plus a civ-specific comparison; localise the kit descriptions. Related: 136 (the engine assumes Rome), 132, 126.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 5, 22, 59, 74, 133). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.
