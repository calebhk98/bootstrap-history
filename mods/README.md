# mods/

Empty on purpose. This directory is where a third-party mod would go, and
nothing loads it yet.

`TASKS.md` beside this file lists what would have to be true before dropping a
folder in here worked the way dropping a jar into Minecraft's mod folder does.

The short version: **the data side is most of the way there already, and
nobody planned it that way.** The tech tree is merged from 41 files in
`data/branches/`, civilisations are pure data in `data/civilizations/`,
production recipes merge by key from `data/production/`, and the engine
contains no `if Rome:` branches - a civilisation is a JSON file and always has
been. A prehistoric tree, a sci-fi tree or a new civilisation are, in
structure, already just more of those files.

What is missing is not the loading. It is namespacing, load order, and a merge
that says something when two mods disagree instead of silently keeping the
first one it read.
