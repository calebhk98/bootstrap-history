# Module 88: Media, Signal and Memory

## Why these hundred have no entry anywhere else

These hundred technologies carry costs and prerequisites in the tree but no build guide, because most are precision mechanics plus organisation, not chemistry or metallurgy, and the guide's other modules walk past them toward furnaces. A furnace is dramatic. A composing stick is not. But the composing stick lets one man outproduce a scriptorium of forty monks, and the punched card lets one clerk do what a hundred clerks did.

Two kinds appear below. The first is Roman-buildable now: papyrus, iron gall ink, the screw press, the crude telegraph relay. The second needs something Rome flatly lacks, usually a hard vacuum, a fine uniform powder, or a specific tropical latex, each flagged with a note on where the missing piece lives.

Read the danger lines. Nothing else in this guide is as likely to get you killed by people rather than physics. A furnace that fails kills you. A press that runs kills the scribal economy's confidence in you, and a frightened elite is worse than a bad furnace, because it thinks.

---

## Part One: the book before the press

### if_papyrus - Papyrus sheet (*papyrus, biblus*)

**What it is.** Rome's standard writing surface, *Cyperus papyrus* pith, Nile Delta and Faiyum. You already have it; it is here so the three things built from misunderstanding it make sense.

**Why you would never guess this.** Papyrus never becomes pulp. Strips of pith, laid crosswise, wetted and pressed, are glued by the plant's own sap as they dry. Beat it like rag pulp and you destroy it.

Also covers: if_parchment, if_rag_paper, if_bookbinding_case.

**Parchment** (*pergamena*): skin unhaired in a lime bath (2-3 weeks, turned daily), scraped, dried under tension, never tanned; too much lime dissolves the collagen, too little leaves hair. Takes knife-scrape correction papyrus cannot survive.

**Rag paper**: China's invention (Cai Lun, c.105 AD), not traded west for centuries; reinvent by fulling linen rag until fibres **fray**, not merely soften (`90_textiles.md`), diluting in a vat, lifting a wire-mesh mould through it, couching, pressing, drying.

**Case binding**: sewn signatures laced into boards survive centuries; glue alone fails in years.

**Prerequisites.** `mat_papyrus`, `mat_parchment`, `mat_paper` plus fulling, `cap_tol_1mm`.

**Cost & labour.** ESTIMATED. A scribe copies 2-3 columns/hour; papyrus roughly a denarius a roll in Egypt; parchment several times that per area.

**Danger.** None. Build these first.

**Confidence: HIGH** for papyrus/parchment; **MEDIUM** for reinvented rag paper.

---

### if_movable_type - Movable type, cast metal (*typi mobiles*)

**What it is.** Casting thousands of identical letters that lock into a page and print thousands of impressions. The highest-leverage node in the tree for outrunning a magistrate's ability to suppress an idea.

**Why you would never guess this.** Every piece of type must be the same height to a fraction of a millimetre or it does not print: tall pieces black, short ones blank. Gutenberg's invention was the **adjustable hand mould**: a punch (steel, letter mirror-reversed) strikes a matrix (copper/brass) leaving a precise negative, which drops into a spring-adjustable mould casting every letter to one fixed body height regardless of width.

Also covers: if_punch_and_matrix, if_type_mould, if_type_metal_alloy, if_linotype_machine.

**Prerequisites.** `cap_tol_100um`, `mat_brass`, `cap_heat_1100`.

**Roman-available inputs.** Lead (*plumbum*), tin (*stannum*, Cornwall), antimony (*stibium*, Anatolia). Lead is too soft, tin hardens, antimony **expands** slightly on cooling, filling the mould. DERIVED ratio: roughly 4:1:1.

**Procedure.** Cut punch mirror-reversed; strike into matrix; true it; cast (~240-300 C, cherry-red to orange), jerk once, eject. A straightedge across ten sorts of one letter should show no rock or light.

**Failure modes.** Uneven height prints patchy. Cold metal gives a short cast; overheated metal etches the matrix.

**Linotype**: matrices fall from a magazine by keystroke, each notched uniquely so a distributor bar sorts it home after use. One operator replaces roughly six compositors (MEASURED); needs interchangeable-parts precision, a tier-4 destination.

**Cost & labour.** ESTIMATED, DERIVED from Gutenberg-scale shops: a full font is 2-3 punchcutter-months plus a caster's month; several thousand denarii.

**Danger.** Physical: molten splash, lead fume, ventilate. Social, and this is the largest danger in the module: a scriptorium's income depends on copying staying scarce, and a press turning a month's work into an afternoon destroys that logic. Read `03_SOCIAL_POLITICS.md` first: this is the technology most likely to get its founder denounced. Still worth doing early, since everything downstream depends on enough literate people to use it. Build under a patron's name and disperse the corpus (`80_information_printing.md#corpus_dispersed`).

**Confidence: HIGH** on the metallurgy; the danger read is inference, not one attested case.

---

### if_printing_ink - Printing ink, oil-based

**What it is.** Ink that sticks to metal type and transfers cleanly under press pressure.

**Why you would never guess this.** Every ink a scribe knows is watery and beads off polished metal. This is a paint problem, not a writing one: a sticky, oil-based varnish that clings to metal without spreading, and it defeated printers for years.

Also covers: if_composing_stick, if_chase_and_forme, if_woodblock_printing.

**Prerequisites.** `cap_heat_1100`, `mat_olive_oil` (or linseed).

**Roman-available inputs.** Linseed/walnut oil, boiled; lampblack (*fuligo*); pine resin (*colophonia*) for tack.

**Procedure.** Boil oil to a varnish stringing between two fingers (~260-300 C, "flows like honey"); stir in resin hot; grind in lampblack until gritless.

**Failure modes.** Under-boiled never sets; over-boiled skins in the pot; too little resin fills letters solid.

**Composing stick**: a width-adjustable gauge holding a justified line upside-down and mirror-reversed. **Chase and forme**: iron frame locking a page with wedges (quoins); wood furniture swells with humidity, metal does not. **Woodblock**: China's method, no type, a page carved in relief from fine plank-cut fruitwood; the bottleneck is cutting fine lines without splintering.

**Cost & labour.** ESTIMATED, a day's work per batch, under 50 denarii.

**Danger.** Physical: boiling oil is a fire risk. Social: as with the type itself.

**Confidence: HIGH** - textbook chemistry, every input Roman-attested.

---

### if_screw_press - Screw press for printing

**What it is.** The machine that squeezes inked type against paper evenly, in one motion.

**Why you would never guess this.** Rome already has this press, the *torcular* for wine and oil. A wine press's slow squeeze is wrong for printing; add a platen, a padded tympan, and a frisket masking the margins, hinged over the locked forme.

Also covers: if_iron_hand_press.

**Prerequisites.** `master_screw`, `cap_tol_1mm`, `mat_wrought_iron`.

**Procedure.** Lock forme; ink; close tympan and frisket over the paper, swing onto the forme; pull hard and fast, release at once.

**Failure modes.** Platen and bed out of parallel print one side dark.

**Iron hand press**: cast iron (Rome's West has none natively) and a toggle-lever giving almost no advantage through most of the pull, then multiplying force enormously at the last degrees.

**Cost & labour.** DERIVED from wine-press carpentry: 3-4 carpenter-weeks, under 1,000 denarii.

**Danger.** Physical: fingers under a closing platen. Social: the visible machine an agent recognises as a press.

**Confidence: HIGH** for the screw press; **MEDIUM** for iron. Han China has cast iron (MEASURED, c. 5th century BC), a genuine import; see `10_metallurgy.md`.

---

### if_cylinder_press - Cylinder press

**What it is.** A rotating cylinder rolls paper over the inked forme instead of a platen slamming down, sharply speeding printing.

**Why you would never guess this.** A platen applies its whole force at once; a cylinder touches only a thin rolling line, so feed can be continuous. Even ink coverage on the curve is the trade-off.

Also covers: if_rotary_press.

**Prerequisites.** `if_iron_hand_press`, `cap_power_steam`, `boring_mill`.

**Procedure.** Locked forme on a reciprocating bed; paper feeds around a large iron cylinder rolling over it; steam or water-mill drive keeps both in step.

**Failure modes.** A cylinder even slightly out of true prints heavier on one side every revolution.

**Rotary press**: curves the type itself as one stereotype plate around the cylinder; register becomes the critical tolerance.

**Cost & labour.** ESTIMATED, several thousand denarii; throughput several times a hand press's ~200 sheets/hour.

**Danger.** Physical: entanglement risk. Social: louder, harder to hide than a hand press.

**Confidence: MEDIUM** - straightforward once steam power and precision boring exist.

---

### if_stereotype - Stereotype plate

**What it is.** Casting a whole locked page as one plate, freeing the type for reuse.

**Why you would never guess this.** Type kept set cannot be reused elsewhere. Take a mould of the forme in wet papier-mache (a "flong"), dry it rigid, then cast one plate from it in a single fast pour.

Also covers: if_electrotype.

**Prerequisites.** `if_movable_type`, `mat_lead`, `cap_heat_1100`.

**Procedure.** Beat pulp into the forme; dry to rigidity; pour molten metal into the flong-lined box in one pour; trim to type-height.

**Failure modes.** A slow pour leaves air pockets printing as white holes.

**Electrotype**: grows a copper shell electrolytically (`50_electricity.md`) over hours, crisper edges, but must be backed with lead or it buckles.

**Cost & labour.** ESTIMATED, a day per plate; electrotype several days, mostly unattended.

**Danger.** Low, hot metal and the usual printing risk.

**Confidence: MEDIUM** - stereotype is simple and attested; electrotype gated on `50_electricity.md`'s zinc chain.

---

### if_lithography - Lithography

**What it is.** Printing from a flat stone with no carving at all, pure surface chemistry.

**Why you would never guess this.** Draw with greasy crayon on porous limestone, dampen the stone (water clings to bare stone, repelled by grease), roll oily ink over it (sticks only to the grease). No relief does any work; it is entirely chemical.

Also covers: if_chromolithography, if_offset_lithography.

**Prerequisites.** `cap_tol_1mm`, `mat_alum`.

**Roman-available inputs.** The historical stone, Solnhofen limestone, lies outside the empire. ESTIMATED: a fine Italian or Anatolian limestone may substitute; test before a run.

**Procedure.** Polish the slab; draw in crayon; etch lightly with nitric acid and gum arabic; sponge with water, roll with ink, press paper.

**Failure modes.** A stone drying mid-run picks up ink everywhere ("scumming").

**Chromolithography**: one stone per colour, registered by hand. **Offset**: a rubber blanket carries stone-to-paper, reading correctly and gentler on the stone.

**Cost & labour.** ESTIMATED, high, a later shop technology.

**Danger.** Low beyond dilute acid; a stone draws less suspicion than a type-filled press.

**Confidence: LOW** on the stone source; **MEDIUM** on the chemistry.

---

### if_halftone_screen - Halftone screen and dot matrix

**What it is.** The trick letting a press reproduce a photograph's full range of grey.

**Why you would never guess this.** You cannot print a grey. Vary dot **size**, not darkness: large dots read dark, small light. The screen is a ruled crossed-line grid, photographed slightly out of focus on purpose, turning sharp lines into graduated dot edges.

Also covers: if_photoengraving.

**Prerequisites.** `cap_tol_10um`, `lens_grinding`.

**Procedure.** Rule two glass plates with fine parallel lines (toward 100-150/inch), cement crossed at 90 degrees; photograph the original through the screen.

**Failure modes.** Uneven ruling or wrong angle gives moire instead of an image; ruling accuracy is the hard limit.

**Photoengraving**: coat metal with light-hardening bichromated gelatin, expose through the halftone negative, wash and acid-etch so dots stand in relief.

**Cost & labour.** ESTIMATED, weeks for a skilled instrument-maker, reused indefinitely.

**Danger.** Low; the acid bath is the main hazard.

**Confidence: MEDIUM** - optics are textbook, ruling fine enough needs precision this guide's early tiers lack.

---

### if_mimeograph - Mimeograph

**What it is.** A cheap, press-free way to run hundreds to thousands of copies from one master.

**Why you would never guess this.** No ink chemistry, no type: a waxed stencil is written on, and the letterform's pressure displaces wax, opening the fibre beneath. Ink forced through prints a fresh sheet; the stencil is a mask, not a mould.

Also covers: if_stencil_duplicator.

**Prerequisites.** `if_typewriter` (or stylus), `mat_nitrocellulose`, `cap_power_muscle`.

**Procedure.** Type onto a waxed stencil; mount on an ink-fed drum; hand-crank paper through.

**Failure modes.** The stencil degrades after roughly 200 (silk-screen) to 2,000 (waxed) copies.

**Cost & labour.** ESTIMATED, minutes per stencil, modest metalworking for the duplicator.

**Danger.** Social: this module's samizdat technology, run from a back room and dismantled in minutes.

**Confidence: MEDIUM** - simple, depends on `mat_nitrocellulose` (`20_chemistry.md`).

---

## Part Two: the hand and the desk

### if_quill - Quill pen (*penna*)

**What it is.** A flexible pen cut from a flight feather, standard once parchment overtakes papyrus.

**Why you would never guess this.** Obvious once you want it: Rome's reed pen (*calamus*) suits papyrus but scratches parchment's tougher grain; a feather glides where a reed digs in. The split holds ink by capillary action but needs re-cutting hourly.

Also covers: if_iron_gall_ink, if_steel_pen_nib.

**Iron gall ink**: tannic acid from oak galls binds chemically to iron from green vitriol, pale at first, oxidising to black-blue that bonds into the fibres rather than sitting on top, unlike carbon ink, which sponges off. Cannot be erased once dry.

**Steel pen nib**: stamped, hardened steel, no re-cutting; harden fully then temper to spring hardness, or it snaps.

**Prerequisites.** Ink: `cap_heat_0700`, `mat_vitriols`. Nib: `mat_blister_steel`, `cap_tol_100um`, interchangeable-parts precision.

**Cost & labour.** ESTIMATED. Quills near-free; ink a day's batch; nibs need stamping-die tooling.

**Danger.** None of weight.

**Confidence: HIGH** for quill and ink; **MEDIUM** for the nib.

---

### if_fountain_pen - Fountain pen

**What it is.** A pen carrying its own ink reservoir.

**Why you would never guess this.** The reservoir is trivial; the feed, a comb of fine cuts, must let air bubble **in** at the same rate ink flows **out**, purely by capillary action. Wrong geometry floods or starves the pen.

Also covers: if_pencil_graphite, if_carbon_paper.

**Prerequisites.** `if_steel_pen_nib`, `mat_celluloid`, `cap_tol_100um`.

**Graphite pencil**: native graphite is scarce and too soft alone; the Conte process grinds it with clay and fires it, the clay:graphite **ratio**, not purity, setting hardness.

**Carbon paper**: an even lampblack coating in a thin wax carrier, transferring by pressure alone.

**Failure modes.** Pen floods or starves; too much clay barely marks; too little snaps.

**Cost & labour.** ESTIMATED, small-batch craft goods.

**Danger.** None of weight.

**Confidence: MEDIUM** - limited by sourcing graphite or celluloid.

---

### if_typewriter - Typewriter

**What it is.** A machine striking a fixed character per keystroke.

**Why you would never guess this.** QWERTY is not for finger speed; it keeps common letter pairs on opposite sides of the basket so bars swing in from different angles and do not jam. Optimised for clearance, not speed.

Also covers: if_shift_key_mechanism.

**Prerequisites.** `if_steel_pen_nib`, `cap_tol_100um`, interchangeable-parts precision.

**Procedure.** Each key swings a bar to strike an inked ribbon; bars must return fast or the next stroke jams.

**Shift key**: the basket shifts one notch so the same bar strikes a different face of a two-character slug; return spring must be precise.

**Failure modes.** Weak springs jam; imprecise shift misprints case.

**Cost & labour.** ESTIMATED, comparable to a good clock.

**Danger.** None directly; an anonymous typed hand is useful for what you cannot trace to a scribe.

**Confidence: MEDIUM** - gated on interchangeable-parts precision.

---

### if_punched_card - Punched card

**What it is.** A card whose hole pattern encodes information, machine-readable and sortable.

**Why you would never guess this.** The ancestor is the loom. Jacquard cards, fed one at a time, lift or block hooks controlling warp threads; a chain of thousands weaves a complex pattern automatically, arguably the birth of the stored program.

Also covers: if_jacquard_chain, if_keypunch.

**Prerequisites.** `cap_tol_1mm`, `mat_paper`.

**Procedure.** Fix a card size and hole grid; every later machine depends on cards matching it exactly.

**Keypunch**: a modified typewriter driving a punch die per keystroke; the card must be held in precise register.

**Failure modes.** Dimensional drift between batches makes cards unreadable together.

**Cost & labour.** ESTIMATED, days per Jacquard chain, cheap per card once a standard is enforced.

**Danger.** Low, mostly organisational.

**Confidence: HIGH** for Jacquard; **MEDIUM** for a Roman-era card standard.

---

### if_card_sorter - Card sorter

**What it is.** A machine routing punched cards by their holes, and counting them.

**Why you would never guess this.** Sensing is bare electrical contact: wire brushes touch a metal drum only where a hole exists, tripping a solenoid gate. Nothing optical.

Also covers: if_hollerith_tabulator.

**Prerequisites.** `if_punched_card`, `electromagnet`.

**Procedure.** Feed cards past a brush bank wired to gate solenoids; a completed circuit fires the matching gate.

**Hollerith tabulator**: adds a counter advancing on every sensed hole. MEASURED: the 1880 US census took roughly eight years by hand; 1890, with Hollerith machines, roughly one.

**Failure modes.** A worn brush misses a hole, undercounting silently.

**Cost & labour.** ESTIMATED, low thousands of denarii once electromagnets exist.

**Danger.** Socially notable: a tabulator hands a magistrate a sharper tool for taxing people.

**Confidence: MEDIUM** - straightforward once electromagnets and punched cards exist.

---

### if_index_card_system - Index card and filing system

**What it is.** A uniform card per record, filed in strict order, letting insertion happen without recopying a ledger.

**Why you would never guess this.** Obvious once you want it, yet nobody assembled it: Rome has alphabetical order already, never combined with uniform size and drawer storage. The invention is procedural discipline, nothing to build.

Also covers: if_dewey_classification.

**Prerequisites.** `mat_paper`, `cap_tol_1mm`.

**Procedure.** Fix a card size; file strictly by one order; never let backlog accumulate.

**Dewey classification**: a hierarchical decimal scheme lets any new subject be inserted without renumbering.

**Failure modes.** The system fails the moment filing discipline lapses.

**Cost & labour.** ESTIMATED, negligible material cost, a disciplined clerk is the real cost.

**Danger.** Low, purely organisational risk.

**Confidence: HIGH** - pure organisation, well demonstrated payoff.

---

### if_adding_machine - Adding machine

**What it is.** A mechanical device adding numbers reliably without a human carrying.

**Why you would never guess this.** The carry is the whole problem: each decade wheel, rolling 9 to 0, must kick the next forward by one, and that kick must itself cascade further. A simple gear train cannot do this; it defeated skilled mechanics for years.

Also covers: if_comptometer, if_cash_register, if_slide_rule.

**Prerequisites.** `cap_tol_1mm`, `crank_conrod`.

**Procedure.** Each wheel carries a spring finger that, only passing 9 to 0, advances the next wheel one tooth.

**Comptometer**: every keystroke adds instantly, faster once mastered. **Cash register**: a social device, forcing a printed receipt and locked drawer to prevent theft. **Slide rule**: multiplication as addition of logarithmic lengths, needing log tables first (`60_mathematics_method.md`; Rome's lack of positional notation makes this real labour), the rule itself simple carpentry once the scale exists.

**Failure modes.** A mistimed finger skips a carry; a warped rule throws readings off.

**Cost & labour.** ESTIMATED, comparable to a mechanical clock.

**Danger.** Low; the cash register reduces its owner's risk.

**Confidence: MEDIUM** - textbook once tolerance and tables exist.

---

## Part Three: capturing sound

### if_phonautograph - Phonautograph

**What it is.** The first device to record a sound wave's shape as a visible trace, without playback.

**Why you would never guess this.** A diaphragm and stiff bristle scratch a wavy line into lamp-blacked paper on a rotating drum. Running it backward to reproduce sound did not occur to its own inventor; the traces were only played back a century and a half later, by modern optical scanning (ATTRIBUTED).

Also covers: if_tin_foil_phonograph, if_wax_cylinder.

**Prerequisites.** `cap_tol_1mm`.

**Tin foil phonograph**: the stylus **indents** soft tin foil; running it back reproduces a faint sound. The foil crinkles after roughly 10-20 plays (MEASURED), a novelty.

**Wax cylinder**: cuts, not indents, a groove into soft wax, durable and erasable, 100+ plays, the basis of the first recording industry.

**Failure modes.** Too stiff a stylus gives faint, distorted playback.

**Cost & labour.** ESTIMATED, comparable to a decent clock.

**Danger.** Low; a stranger's voice with no visible speaker reads as sorcery, demonstrate carefully.

**Confidence: MEDIUM** - attested and simple; the barrier is a sensitive diaphragm.

---

### if_disc_record - Disc record

**What it is.** Sound on a flat disc mass-produced from a single master.

**Why you would never guess this.** A cylinder duplicates slowly; a disc's master groove can be electroplated into a "stamper" pressing thousands of copies in hot shellac in seconds, like a coin die.

Also covers: if_disc_cutting_lathe, if_gramophone_motor, if_acoustic_horn_recording.

**Prerequisites.** `if_wax_cylinder`, `mat_shellac` (Indian lac resin, a reachable Far-East good).

**Disc-cutting lathe**: the stylus feeds at constant pitch while the disc spins at dead-constant speed, or the groove wavers. **Gramophone motor**: a governor (as in a steam engine) and flywheel hold that speed. **Acoustic horn**: a passive amplifier, gain rising only logarithmically with size, and the diaphragm's own stiffness caps how much air it moves, why bass is absent, a physical ceiling.

**Failure modes.** Uneven speed distorts pitch; shellac shatters on impact.

**Cost & labour.** ESTIMATED, minutes per copy once master and stamper exist.

**Danger.** Low; manage reactions to a talking machine.

**Confidence: MEDIUM** - shellac reachable; the stamper depends on `50_electricity.md`'s current chain.

---

### if_carbon_microphone - Carbon microphone

**What it is.** A device converting sound pressure into varying current.

**Why you would never guess this.** Loosely packed carbon granules change **resistance** as sound compresses their packing, modulating a steady current. It needs current already flowing; not passive.

Also covers: if_moving_coil_loudspeaker.

**Prerequisites.** `crude_cell`, `mat_carbon_black`.

**Failure modes.** Granules pack down and lose sensitivity over weeks.

**Moving coil loudspeaker**: the converse, a coil on a paper cone in a magnetic field; cone size caps bass response, a physical limit, not a defect.

**Cost & labour.** ESTIMATED, modest once electromagnets exist.

**Danger.** Low.

**Confidence: MEDIUM** - gated on `50_electricity.md`'s electromagnet chain.

---

### if_magnetic_tape - Magnetic tape recording

**What it is.** Sound recorded as magnetisation on a moving tape, erasable indefinitely.

**Why you would never guess this.** The magnetisation curve is sharply nonlinear near zero current, so a naive recording distorts badly. Adding a strong, inaudible high-frequency "bias" mixed with the audio linearises it, a counterintuitive fix: add a huge signal you will never hear to make the one you want correct.

Also covers: if_recording_bias.

**Prerequisites.** `electromagnet`, `mat_paper`.

**Failure modes.** Without bias, distortion is severe.

**Cost & labour.** ESTIMATED, high; oxide must be extremely fine and uniform.

**Danger.** Low physically.

**Confidence: LOW** - bias is textbook, uniform oxide manufacture is a genuine, late barrier.

---

## Part Four: wires that carry a signal

### if_electric_telegraph - Electric telegraph

**What it is.** Sending messages instantly over long distances by electrical pulses on a wire.

**Why you would never guess this.** A single circuit's range is capped at a few tens of miles. A telegraph crosses a continent because of the **relay**: at each station, the weak incoming current only moves a small local armature, which closes a fresh-battery local circuit retransmitting full strength onward. Nobody guesses the trick is using the weak signal only to trigger a strong one.

Also covers: if_morse_key_and_sounder, if_telegraph_relay.

**Prerequisites.** `electromagnet`, `crude_cell`.

**Procedure.** Space relays by wire resistance and battery strength (a few tens of miles per hop, ESTIMATED); a key pulses short and long (Morse); a sounder clicks them at the far end. Trained operators read the **rhythm**, not by counting.

**Failure modes.** Dirty relay contacts drop the signal.

**Cost & labour.** ESTIMATED, DERIVED from wire resistance, scaling with route length.

**Danger.** Social: an instant long-distance network is exactly the cross-provincial capability the Roman state fears in private hands (`03_SOCIAL_POLITICS.md`).

**Confidence: HIGH** - the relay is textbook, materials Roman-available once `50_electricity.md`'s chain is solved.

---

### if_submarine_cable_gutta_percha - Submarine cable with gutta percha

**What it is.** A telegraph cable surviving on the sea floor without shorting for years.

**Why you would never guess this.** The problem is insulation; bare copper shorts instantly in seawater. Gutta percha, latex of the *Palaquium* tree, native only to Malaya, Sumatra and Borneo, is thermoplastic and inert, and does not rot under pressure. This one tree product is why undersea telegraphy became possible, exactly the case `95_expeditions.md` describes: elsewhere, not unobtainable. `50_electricity.md` says Rome will never have it; true only for passive trade, someone has to sail for it.

Also covers: if_cable_repeater.

**Prerequisites.** `if_electric_telegraph`, `mat_gutta_percha` (`95_expeditions.md#trade_route_extend`).

**Procedure.** Warm gutta percha pliable, wrap thick layers around the conductor; armour with iron wire near shore; pay out slowly under tension.

**Failure modes.** A pinhole shorts the whole line on submersion.

**Cable repeater**: a submerged relay boosting a signal weak after roughly 100-200 km, ESTIMATED; unrepairable once laid.

**Cost & labour.** ESTIMATED, extremely high, among the largest capital commitments in the tree.

**Danger.** Large: expedition risk plus sabotage of a laid cable.

**Confidence: HIGH** on the material science; **LOW** on Roman-era laying logistics.

---

### if_telephone_transmitter - Telephone transmitter

**What it is.** A device converting nearby voice into an electrical signal.

**Why you would never guess this.** The same carbon-granule mechanism as the microphone above, needing constant current at every handset, a real infrastructure burden.

Also covers: if_telephone_receiver, if_loading_coil.

**Prerequisites.** `if_carbon_microphone`.

**Failure modes.** Receiver and transmitter too close causes feedback squeal.

**Telephone receiver**: a small loudspeaker in reverse; the system passes only roughly 300-3400 Hz, why a phone voice sounds thin.

**Loading coil**: an inductor cancelling cable capacitance, extending range from 20 km to 50 km loaded; wrong spacing increases crosstalk.

**Cost & labour.** ESTIMATED, modest once the microphone exists.

**Danger.** Low; see the exchange entry for the sharper risk.

**Confidence: MEDIUM** - textbook once the microphone exists.

---

### if_telephone_exchange - Telephone exchange and switchboard

**What it is.** A central point connecting any subscriber's line to any other's.

**Why you would never guess this.** A manual exchange works by an operator plugging a cord between jacks, meaning that operator hears every call, the largest single social danger here: a standing eavesdropper on every subscriber's business.

Also covers: if_strowger_exchange.

**Prerequisites.** `if_telegraph_relay`, `if_telephone_transmitter`.

**Strowger exchange**: an electromechanical stepping switch moves vertically then rotates, driven by the caller's own dial pulses, removing the operator. A persistent ATTRIBUTED anecdote holds its inventor was an undertaker who suspected the town operator diverted his calls to a rival; true or not, it captures the danger solved.

**Failure modes.** An overwhelmed manual board cannot keep pace at peak.

**Cost & labour.** ESTIMATED, manual scales with operator wages; Strowger trades that for maintenance-heavy capital.

**Danger.** Serious: assume any call through a staffed exchange is not private (`03_SOCIAL_POLITICS.md`).

**Confidence: MEDIUM** for manual; **LOW** for Strowger's precision switches.

---

## Part Five: capturing light

### if_camera_obscura_lens - Camera obscura with lens

**What it is.** A darkened box projecting a real image, bright enough to trace or expose.

**Why you would never guess this.** A pinhole is extremely dim; a modest ground lens (Rome already grinds lenses, `30_glass_optics.md`) gathers far more light, essentially free once lens grinding exists.

Also covers: if_camera_lucida.

**Prerequisites.** `lens_grinding`, `cap_tol_1mm`.

**Camera lucida**: no dark box, a prism at exactly 45 degrees lets the artist see scene and paper superimposed, tracing freehand, no exposure.

**Failure modes.** A poor lens gives a soft image.

**Cost & labour.** ESTIMATED, low, a modest lens-grinding job.

**Danger.** Low; a "ghostly" projected image may unsettle a superstitious observer.

**Confidence: HIGH** - straightforward optics once Roman lens-grinding exists.

---

### if_silver_halide_sensitivity - Silver halide photographic sensitivity

**What it is.** The chemical fact under almost every process here: certain silver salts darken under light.

**Why you would never guess this.** Light breaks a fraction of a halide crystal's ions to metallic silver, a latent image invisible to the eye. This does not stop on its own: unexposed grains keep darkening until the plate goes black. The craft is stopping it in time, dissolving away every unexposed grain (fixing), a step nobody guesses is necessary until a ruined plate teaches them.

Also covers: if_daguerreotype.

**Prerequisites.** `analytical_chemistry`, `mat_silver` (Cartagena mines).

**Roman-available inputs.** Silver chloride, from nitrate plus sea salt, is reachable; bromide and iodide are not.

**Procedure.** Coat with the halide; expose in a camera obscura; develop; fix by dissolving unexposed grain, historically a hyposulfite bath, the step making photography possible at all.

**Failure modes.** Skip fixing and the plate blackens within hours.

**Daguerreotype**: develops by hot mercury vapour amalgamating onto exposed silver, a mirror-bright image on silvered copper, unique, no negative.

**Cost & labour.** ESTIMATED, a chemist's day per plate.

**Danger.** Physical: mercury vapour is a cumulative poison. Social: an exact face reads as image-magic to many Romans.

**Confidence: HIGH** on the chemistry; **MEDIUM** on sourcing beyond chloride.

---

### if_calotype - Calotype paper negative

**What it is.** A negative-positive process letting unlimited copies print from one exposure.

**Why you would never guess this.** A paper negative can be contact-printed repeatedly, the first true reproduction technology, at the cost of visible paper texture in every print.

Also covers: if_wet_collodion_plate, if_dry_gelatin_plate.

**Prerequisites.** `if_silver_halide_sensitivity`, `mat_paper`.

**Wet collodion**: glass coated with collodion (nitrocellulose in ether and alcohol, `20_chemistry.md`) gives a texture-free negative but must be developed within 10-15 minutes of coating, wet, forcing field photographers to carry a portable darkroom.

**Dry gelatin**: gelatin heated permeates evenly with silver salts and, once dried, stays sensitive for months, finally separating preparation from exposure from development, enabling amateur photography.

**Failure modes.** Collodion: any delay past 10-15 minutes ruins the image.

**Cost & labour.** ESTIMATED, moderate; collodion demands ongoing field logistics.

**Danger.** Low; same image-magic suspicion as the daguerreotype, softened by reproducibility.

**Confidence: MEDIUM** - collodion needs a working nitrocellulose supply.

---

### if_celluloid_roll_film - Celluloid roll film

**What it is.** A flexible transparent base manufacturable as a continuous roll.

**Why you would never guess this.** Celluloid (nitrocellulose plasticised with camphor, a Far-East import) with sprocket holes unlocks handheld cameras with dozens of exposures and, with fast pulldown, motion pictures.

Also covers: if_panchromatic_emulsion, if_autochrome_plate.

**Prerequisites.** `if_dry_gelatin_plate`, `mat_celluloid`, `cap_tol_100um`.

**Panchromatic emulsion**: extends sensitivity to red (ordinary emulsion is blind to it), but now even a dim red safelight fogs the plate.

**Autochrome**: starch grains dyed red, green, violet, over a panchromatic emulsion, viewed backlit as a colour transparency; resolution caps near 100 lines/mm.

**Failure modes.** Uneven camphor plasticising cracks the film.

**Cost & labour.** ESTIMATED, high; camphor and dye sensitisers are both real reaches.

**Danger.** Physical: nitrocellulose stock is genuinely flammable, closer to a slow explosive when aged.

**Confidence: MEDIUM** on celluloid; **LOW** on panchromatic and autochrome.

---

### if_flash_powder - Flash powder

**What it is.** A way to produce a bright, near-daylight burst for exposures where lamp light is too dim.

**Why you would never guess this.** Burning magnesium gives blue-white light near daylight's spectrum in under a second, but magnesium metal needs electrolysis, unavailable before the early 1800s, gated behind `50_electricity.md`.

Also covers: if_flashbulb.

**Roman-available inputs.** A real stopgap: dried lycopodium powder (clubmoss spores, MEASURED as a stage-flash material) burns dim and yellow-orange, dramatic, not a real exposure.

**Procedure.** Grind magnesium fine; ignite by spark or flame, clear of anything flammable.

**Failure modes.** Coarse powder burns too slowly; damp powder fails to ignite.

**Flashbulb**: magnesium foil sealed in an oxygen-filled glass bulb, single-use; any seal leak ruins it before firing.

**Cost & labour.** ESTIMATED, high, gated on magnesium.

**Danger.** Physical: fire and burn hazard, ventilate the smoke.

**Confidence: LOW** - magnesium metal is a real late-tier barrier.

---

### if_focal_plane_shutter - Focal plane shutter

**What it is.** A mechanism controlling exposure duration below a fraction of a second.

**Why you would never guess this.** A curtain slit runs across the film plane; narrowing its **width**, not its speed, shortens exposure. Shutter speed here is a width, not a speed.

Also covers: if_leaf_shutter, if_intermittent_film_movement.

**Prerequisites.** `cap_tol_100um`.

**Leaf shutter**: blades at the lens open together, flash-synchronising far more cleanly than a travelling curtain.

**Intermittent film movement**: a Geneva cross or claw-and-cam holds a frame still then advances it in a fraction of a second; imprecise geometry binds the pin, tearing film.

**Failure modes.** An uneven curtain over-exposes one edge.

**Cost & labour.** ESTIMATED, fine clockwork-level precision.

**Danger.** Low.

**Confidence: MEDIUM** - well documented, achievability depends on holding tolerance in production.

---

### if_cine_camera - Cine camera

**What it is.** A camera capturing rapid stills on moving film, the basis of motion pictures.

**Why you would never guess this.** Celluloid roll film plus intermittent movement plus one easy-to-miss requirement: the shutter must **blank the lens during pulldown**, or every frame smears.

Also covers: if_film_projector.

**Prerequisites.** `if_celluloid_roll_film`.

**Film projector**: the same problem in reverse, adding a bright, hot light inches from flammable film; heat dissipation is a life-safety requirement.

**Failure modes.** Incomplete blanking smears the picture; poor heat dissipation can ignite jammed film in seconds.

**Cost & labour.** ESTIMATED, two fine clocks' worth of mechanism in synchrony.

**Danger.** Physical, severe: nitrocellulose fires in enclosed cinemas were a real, repeated hazard (MEASURED). Social: moving images amplify image-magic anxiety.

**Confidence: MEDIUM** on the mechanism; **HIGH** on the fire risk.

---

## Part Six: the air itself

### if_tuned_circuit - Tuned LC circuit

**What it is.** A coil-and-capacitor pair resonating at one frequency, letting a receiver select one signal from the spectrum.

**Why you would never guess this.** How sharply the resonance selects one frequency (its "Q") depends on minimising resistance in the loop, a fussy winding and low-loss-capacitor problem, not an exotic material one.

Also covers: if_antenna_dipole.

**Prerequisites.** `electromagnet`.

**Procedure.** Wind a coil in pure annealed copper; pair with a low-loss variable capacitor; tune until the frequency peaks.

**Dipole antenna**: radiation resistance is very low, so impedance matching matters more than anything, and height above ground matters far more than a good ground connection.

**Failure modes.** A resistive coil gives a broad resonance that cannot separate close stations.

**Cost & labour.** ESTIMATED, modest, the cost is precision winding labour.

**Danger.** Low; invisible signal detection reads as sorcery to most Romans.

**Confidence: MEDIUM** - gated on `50_electricity.md`'s electromagnet chain and winding precision.

---

### if_spark_transmitter - Spark transmitter

**What it is.** The earliest practical way to generate a radio signal detectable at a distance.

**Why you would never guess this.** A spark produces a broadband, damped wave, jamming every nearby transmitter at once, an early instance of the spectrum as a shared commons.

Also covers: if_coherer, if_crystal_detector.

**Prerequisites.** `if_tuned_circuit`.

**Coherer**: metal filings briefly "cohere," dropping resistance, when a radio wave passes; they do not decohere on their own, a spring tapper must bump the tube after every signal.

**Crystal detector**: a "cat's whisker" against galena (lead ore, Spanish/British/Sardinian mines) rectifies with no battery, more reliable than the coherer but temperamental, the sensitive spot found by trial and lost with a bump.

**Failure modes.** An untapped coherer stops responding.

**Cost & labour.** ESTIMATED, low to moderate.

**Danger.** Low; visible sparking worsens sorcery suspicion.

**Confidence: HIGH** for spark and coherer; **MEDIUM** for the crystal detector.

---

### if_triode_oscillator - Triode oscillator

**What it is.** A stable continuous radio wave generator, replacing spark's crude burst.

**Why you would never guess this.** With a hard vacuum tube (`50_electricity.md`, `55_semiconductors.md`), positive feedback sustains oscillation indefinitely, but coupling strength must sit in a narrow window, too little and it will not oscillate, too much and it chirps.

Also covers: if_continuous_wave_transmitter, if_amplitude_modulation, if_frequency_modulation.

**Prerequisites.** `vacuum_tube`, `if_tuned_circuit`.

**Continuous wave**: a steady, cleanly keyed tone using far less bandwidth than spark. **Amplitude modulation**: varies carrier strength with audio, simple, but atmospheric noise is itself amplitude noise. **Frequency modulation**: varies frequency instead, far quieter, at the cost of bandwidth and complexity.

**Failure modes.** Loose feedback fails to oscillate; tight feedback chirps.

**Cost & labour.** ESTIMATED, high, gated on the vacuum tube.

**Danger.** Low physically; continuous broadcast is more visible than a one-off spark demonstration.

**Confidence: LOW** across all four, entirely gated on a working vacuum tube.

---

### if_superheterodyne_receiver - Superheterodyne receiver

**What it is.** A receiver design letting one dial select any station cleanly across a band.

**Why you would never guess this.** Mix the incoming signal with a local oscillator to shift it to one fixed "intermediate frequency," where a single sharp stage filters regardless of station, deliberately using the "wrong" frequency to simplify everything downstream.

Also covers: if_radio_direction_finding, if_facsimile_transmission, if_radar.

**Prerequisites.** `if_triode_oscillator`, `if_amplitude_modulation`.

**Radio direction finding**: a loop antenna's sharp **null** gives a far more precise bearing than its broad maximum; two stations triangulate. **Facsimile**: a rotating drum and photocell scan an image; sender and receiver must synchronise near-perfectly. **Radar**: a timed pulse's echo gives range on a CRT display, a genuine capstone needing everything above at once, essentially the far end of this guide's reconstruction path.

**Failure modes.** A drifting oscillator loses the intermediate lock.

**Cost & labour.** ESTIMATED, high across the cluster.

**Danger.** Low physically; RDF and radar are recognisably military-relevant.

**Confidence: LOW** across the cluster; radar marks the plausible end of reconstruction.

---

### if_cathode_ray_tube - Cathode ray tube

**What it is.** A vacuum tube steering an electron beam to draw an image on a phosphor screen.

**Why you would never guess this.** Deflection coils need genuine symmetry or the picture distorts; phosphor wears out with use, dimming or "burning in" a ghost image.

Also covers: if_iconoscope, if_video_scanning_standard, if_television_mechanical.

**Prerequisites.** `discharge_xray`, `vacuum_tube`.

**Iconoscope**: a mosaic of tiny light-sensitive cells, each capacitively isolated to accumulate its own charge; building this fine, uniform mosaic, not the tube, is the real barrier.

**Video scanning standard**: fixing scan lines and frame rate is a coordination problem, not a technical one, every transmitter and receiver must agree (`03_SOCIAL_POLITICS.md`).

**Mechanical television** (Nipkow disc): a spinning punched disc scans an image mechanically, no vacuum tube at all, a dim, flickering but real stepping stone before the electronic route.

**Failure modes.** Asymmetric coils skew the image.

**Cost & labour.** ESTIMATED, very high for CRT/iconoscope; moderate for mechanical.

**Danger.** Low physically; transmitted moving images amplify image-magic suspicion.

**Confidence: LOW** for CRT and iconoscope; **MEDIUM** for mechanical television.

---

## Sources and confidence

These mechanisms are drawn from well-documented 19th and early 20th century engineering history: Gutenberg's punch-matrix-mould system, drying-oil ink chemistry, wet and dry photographic emulsions, the telegraph relay, gutta percha submarine insulation, and the spark-to-triode radio lineage are all HIGH-confidence, textbook engineering, independent of whether Rome can build them. Where this module flags LOW confidence, the uncertainty is almost always a Roman-era **material or precision** barrier, not the mechanism: vacuum tubes, fine magnetic oxide powders, synthetic dye sensitisers, and sub-millimetre disc ruling are all late, hard destinations in this tree, not myths. Cost and labour figures are marked ESTIMATED or DERIVED, never invented; real historical figures (census tabulation time, tinfoil phonograph play count, gutta percha's origin) are marked MEASURED with the basis given. Two anecdotes, the phonautograph's delayed playback and the Strowger undertaker story, are flagged ATTRIBUTED and not fully verifiable, included because they illustrate the mechanism honestly, not as settled fact.

## Where to go next

- `80_information_printing.md` - the lower-tier print and corpus-survival technologies this module's press cluster builds on, and the social strategy for surviving what you publish.
- `30_glass_optics.md` - lens grinding and mirror-making that the camera obscura, camera lucida and every glass photographic plate depend on.
- `50_electricity.md` - the electromagnet, crude cell and vacuum tube chain almost everything in Parts Four and Six is gated on; read its zinc and gutta percha notes before the telegraph or cable clusters.
- `03_SOCIAL_POLITICS.md` - read before building a press, an exchange, or a telegraph line. Everything here that moves information faster or more privately than a scribe also moves it faster or more privately than a magistrate.
- `95_expeditions.md` - the gutta percha logic, and more broadly "elsewhere, not unobtainable," that the submarine cable cluster depends on directly.
- `20_chemistry.md` - nitrocellulose, distillation and fixing-bath chemistry underlying collodion, celluloid and photographic fixing generally.
- `10_metallurgy.md` - cast iron sourcing (Han China import, or a cupola furnace) for the iron hand press and cylinder press.
