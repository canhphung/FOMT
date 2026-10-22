#!/usr/bin/env python3
"""Extract verified pointer tables and SCR strings; no heuristic matches are importable."""
import argparse
import json
import sys
from pathlib import Path
from fomt_text import FormatError, extract, verified_rom


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--output", type=Path, default=Path("localization/en/catalog.json"))
    args = parser.parse_args()
    try:
        catalog = extract(verified_rom(args.rom))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"records": len(catalog["records"]), "groups": catalog["statistics"],
                          "output": str(args.output)}, ensure_ascii=False))
    except (OSError, FormatError) as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    main()
