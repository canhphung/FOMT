#!/usr/bin/env bash
# mGBA source/build are external dependencies. This script downloads no ROM.
set -euo pipefail
mgba_root=${1:?Usage: tools/build_mgba_bridge.sh /path/to/built/mgba}
mgba_root=$(cd "$mgba_root" && pwd)
project_root=$(cd "$(dirname "$0")/.." && pwd)
bridge_output=${2:-"$project_root/build/mgba_bridge.so"}
mkdir -p "$project_root/build"
# mGBA 0.10 uses USE_DEBUGGERS, newer mGBA uses ENABLE_DEBUGGERS. Those
# macros change the mCore function-table layout: use the library's exact flags.
flags_file="$mgba_root/build/CMakeFiles/mgba.dir/flags.make"
if [[ ! -r "$flags_file" ]]; then
  echo "Missing mGBA build flags: configure/build with the Unix Makefiles generator." >&2
  exit 1
fi
mapfile -d '' -t bridge_defines < <(python3 - "$flags_file" <<'PY'
import pathlib, shlex, sys
line = next(l for l in pathlib.Path(sys.argv[1]).read_text().splitlines() if l.startswith('C_DEFINES = '))
for flag in shlex.split(line.partition(' = ')[2]):
    sys.stdout.buffer.write(flag.encode()+b'\0')
PY
)
if [[ ${#bridge_defines[@]} -eq 0 ]]; then
  echo "Could not read mGBA compilation defines; refusing an incompatible bridge." >&2
  exit 1
fi
gcc -shared -fPIC -O2 "${bridge_defines[@]}" \
  -I"$mgba_root/include" -I"$mgba_root/build/include" \
  "$project_root/tools/mgba_bridge.c" \
  -L"$mgba_root/build" -lmgba -Wl,-rpath,"$mgba_root/build" \
  -o "$bridge_output"
