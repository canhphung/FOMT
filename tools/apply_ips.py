#!/usr/bin/env python3
"""Apply a release IPS to the exact supported local base ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import ips
from fomt_text import FormatError, verified_rom
from text_inserter import atomic_write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom",type=Path)
    parser.add_argument("--patch",type=Path,default=Path("patches/fomt-vi-demo.ips"))
    parser.add_argument("--manifest",type=Path,default=Path("patches/manifest.json"))
    parser.add_argument("--output",type=Path,default=Path("build/fomt-vi-demo.gba"))
    args = parser.parse_args()
    if args.output.resolve() in {args.rom.resolve(),args.patch.resolve(),args.manifest.resolve()}:
        parser.error("output must not overwrite an input")
    try:
        base = verified_rom(args.rom)
        patch = args.patch.read_bytes()
        manifest = json.loads(args.manifest.read_text())
        if hashlib.sha256(patch).hexdigest() != manifest["patch_sha256"]:
            raise FormatError("patch does not match release manifest")
        out = ips.apply(base,patch)
        digest = hashlib.sha256(out).hexdigest()
        if digest != manifest["target_sha256"]:
            raise FormatError("patched ROM does not match release manifest")
        atomic_write(args.output,out)
        print(json.dumps({"output":str(args.output),"size":len(out),"sha256":digest}))
    except (OSError,ValueError) as exc:
        parser.exit(1,f"error: {exc}\n")


if __name__ == "__main__":
    main()
