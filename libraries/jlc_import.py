#!/usr/bin/env python3
"""Fetch JLCPCB/EasyEDA parts with JLC2KiCadLib and file them into this library.

Layout (see ../README.md):
    symbols/<LIB>.kicad_symdir/<symbol>.kicad_sym
    footprints/<LIB>.pretty/<footprint>.kicad_mod
    models/<LIB>/<footprint>.step

JLC2KiCadLib is run so that the generated files already carry the right links:
the symbol's Footprint property is "<LIB>:<footprint>" and the footprint's 3D
model path is "${KIPRJMOD}/../../libraries/models/<LIB>/<footprint>.step".

Usage:
    ./jlc_import.py C42411119 RP2350B
    ./jlc_import.py C42411119 C42415655 RP2350B --dry-run
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LIB_ROOT = Path(__file__).resolve().parent
MODEL_BASE = "${KIPRJMOD}/../../libraries/models"


def find_jlc2kicadlib():
    # Prefer the running interpreter's venv, then the .venv next to this script.
    for local in (Path(sys.executable).parent / "JLC2KiCadLib",
                  LIB_ROOT / ".venv" / "bin" / "JLC2KiCadLib"):
        if local.exists():
            return str(local)
    found = shutil.which("JLC2KiCadLib")
    if not found:
        sys.exit("JLC2KiCadLib not found; activate the .venv or install it")
    return found


def fetch(parts, lib, workdir):
    cmd = [
        find_jlc2kicadlib(),
        *parts,
        "-dir", str(workdir),
        "-symbol_lib_dir", "symbol",
        "-footprint_lib", lib,
        "-model_dir", lib,
        "-model_base_variable", MODEL_BASE,
        "-models", "STEP",
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"JLC2KiCadLib failed with exit code {result.returncode}")


def plan_moves(workdir, lib):
    """Map each downloaded file to its destination in the library."""
    dests = {
        ".kicad_sym": LIB_ROOT / "symbols" / f"{lib}.kicad_symdir",
        ".kicad_mod": LIB_ROOT / "footprints" / f"{lib}.pretty",
        ".step": LIB_ROOT / "models" / lib,
    }
    moves = []
    for src in sorted(workdir.rglob("*")):
        if not src.is_file():
            continue
        dest_dir = dests.get(src.suffix)
        if dest_dir is None:
            print(f"  ignoring unexpected file {src.relative_to(workdir)}")
            continue
        moves.append((src, dest_dir / src.name))
    return moves


def main():
    ap = argparse.ArgumentParser(
        description="Fetch JLCPCB parts and file them into symbols/, footprints/, models/.")
    ap.add_argument("parts", nargs="+", metavar="Cxxxxxxx",
                    help="one or more JLCPCB/LCSC part numbers")
    ap.add_argument("lib", help="library name, e.g. RP2350B (created if it doesn't exist)")
    ap.add_argument("-n", "--dry-run", action="store_true",
                    help="download and show where files would go, but change nothing")
    ap.add_argument("-f", "--force", action="store_true",
                    help="overwrite files that already exist in the library")
    args = ap.parse_args()

    for p in args.parts:
        if not (p[:1] in "Cc" and p[1:].isdigit()):
            ap.error(f"{p!r} doesn't look like a JLCPCB part number (Cnnnn)")
    if "/" in args.lib or args.lib.startswith("."):
        ap.error(f"bad library name {args.lib!r}")

    with tempfile.TemporaryDirectory(prefix="jlc_import_") as tmp:
        workdir = Path(tmp)
        fetch(args.parts, args.lib, workdir)
        moves = plan_moves(workdir, args.lib)
        if not moves:
            sys.exit("JLC2KiCadLib produced no files")

        new_dirs = sorted({d.parent for _, d in moves if not d.parent.exists()})
        clashes = [d for _, d in moves if d.exists()]

        print()
        print("Dry run, nothing changed:" if args.dry_run else "Importing:")
        for d in new_dirs:
            print(f"  new dir  {d.relative_to(LIB_ROOT)}/")
        for src, dest in moves:
            tag = "REPLACE" if dest.exists() else "add"
            print(f"  {tag:7}  {dest.relative_to(LIB_ROOT)}")

        if clashes and not args.force:
            print(f"\n{len(clashes)} file(s) already exist; rerun with --force to overwrite.")
            sys.exit(0 if args.dry_run else 1)
        if args.dry_run:
            return

        for d in new_dirs:
            d.mkdir(parents=True)
        for src, dest in moves:
            shutil.move(src, dest)
        print("Done.")


if __name__ == "__main__":
    main()
