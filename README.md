# Reorganising Kicad 10 libs with git

**Goal**: one central, git versioned repo of custom symbols, footprints, blocks templates, and reference designs.
Previously: a mess of per-project stuff, global stuff, and no version control

## Re-org approach

Organise by type at the top level, but to use the same library names in all of them. Then MicroBeast:Expansion_Connector means the same part whether you're in the symbol, footprint or model tree.

```
PCBs/
├── libraries/
│   ├── symbols/
│   │   ├── MicroBeast.kicad_symdir/
│   │   └── Nintendo.kicad_symdir/
│   ├── footprints/
│   │   ├── MicroBeast.pretty/
│   │   └── Nintendo.pretty/
│   ├── models/
│   │   ├── MicroBeast/
│   │   └── Nintendo/
│   │       └── snes_joypad_connector.step
│   └── blocks/
│       └── MicroBeast.kicad_blocks/
├── templates/
│   ├── antdotorg_sheet.kicad_wks
│   ├── Dimension-Template/
│   └── rc2014-template/
└── boards/
    ├── microbeast_proto_card/
    └── rp2350-rc2014/
```


## Library tables

With every board at the same depth, each board's tables use one fixed prefix, and nothing absolute survives:

```
(uri "${KIPRJMOD}/../../libraries/footprints/MicroBeast.pretty")
```

The same goes for 3D model paths inside the footprints: `${KIPRJMOD}/../../libraries/models/Nintendo/snes_joypad_connector.step`. 
This needs no configuration on the Mac, WSL or in CI. 
The one rule is that **boards always live exactly at `boards/<name>/` **. A path variable would remove that constraint, but then every machine and the CI job has to define it.

Keep the nicknames. Schematics and PCBs refer to parts as MicroBeast:Foo and Nintendo:Bar. Existing boards only need their tables fixed; nothing inside the designs changes.

## Templates

rc2014-template already has the `meta/` folder, so it's a proper KiCad project template. Point Preferences → Configure Paths → KICAD_USER_TEMPLATE_DIR at `PCBs/templates` and it shows up in File → New Project from Template. That's a nicer way to start new cards than copying the folder around.


## .gitignore

The `.gitignore` in here can be used for new Kicad board repos.

# Bootstrapping a new project

1. Create a repo for it.
2. Create a working dir for it.
3. Copy this dir's .gitnore into the new working copy.
4. add this repo as a submodule:

```
git submodule add git@github.com:blowback/microbeast_kicad_libraries.git lib
git commit -m "Add KiCad library as submodule"
```

(If the board is in a subfolder, the path is `blah/pcb/lib` instead of `lib`. It should still be next to the `.kicad_pro`.)

5. clone:

```
git clone --recurse-submodules ...

# OR, after a plain clone: 

git submodule update --init
```

# Editing stuff in the library

```
cd lib
git switch main          # get off the detached HEAD first
# ...edit the footprint in KiCad...
git commit -am "Fix SNES socket model path"
git push
cd ..
git commit -am "Bump lib"   # records the new library commit in the board repo
```

Slightly complex, because `lib/` checks out a **specific commit**. Forget the `git switch main` and your changes are left on a detached HEAD. Forget the final `git commit` the board's repo still points at the old version.

# Pulling library updates into a board

```
git submodule update --remote lib
```
