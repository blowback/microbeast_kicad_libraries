# Reorganising Kicad 10 libs with git

Goal: one central, git versioned repo of custom symbols, footprints, blocks templates, and reference designs.
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

## Throw away

- `ul_SN74HCT125N/` and its zip. That's an Ultra Librarian import of a stock part: KiCad's own 74xx:74HCT125 symbol and Package_DIP:DIP-14_W7.62mm footprint cover it. Use those unless you had a specific reason for the UL version.
- `rc2014-compat-master-rc2014-template.zip` : already unpacked
- `MicroBeast.bak/`, every `*-backups/`, `fp-info-cache` and `*.kicad_prl`. The `.gitignore` covers all of these going forward.


## Migration

```
cd ~/src/microbeast/PCBs
mkdir -p libraries/{symbols,footprints,models/{MicroBeast,Nintendo},blocks} templates boards

kicad-cli sym upgrade --force MicroBeast.kicad_sym -o libraries/symbols/MicroBeast.kicad_symdir/
kicad-cli sym upgrade --force Nintendo.kicad_sym   -o libraries/symbols/Nintendo.kicad_symdir/
git rm MicroBeast.kicad_sym Nintendo.kicad_sym

git mv MicroBeast.pretty Nintendo.pretty libraries/footprints/
git mv libraries/models/snes_joypad_connector.step libraries/models/Nintendo/
git mv antdotorg_sheet.kicad_wks templates/
git mv microbeast_proto_card boards/
```


Then fix each board's `sym-lib-table` / `fp-lib-table` and the model path in `SNES_Controller_Socket.kicad_mod`. Open each board and run ERC and DRC to check nothing is unresolved.

## .gitignore

The `.gitignore` in here can be used for new Kicad board repos.
