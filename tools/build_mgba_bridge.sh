#!/usr/bin/env bash
# mGBA source/build are external dependencies. This script downloads no ROM.
set -euo pipefail
mgba_root=${1:?Usage: tools/build_mgba_bridge.sh /path/to/built/mgba}
mgba_root=$(cd "$mgba_root" && pwd)
project_root=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$project_root/build"
gcc -shared -fPIC -O2 -D_GNU_SOURCE \
  -DENABLE_DEBUGGERS -DENABLE_DIRECTORIES -DENABLE_GDB_STUB \
  -DENABLE_SCRIPTING -DENABLE_VFS -DENABLE_VFS_FD -DM_CORE_GBA -DM_CORE_GB \
  -I"$mgba_root/include" -I"$mgba_root/build/include" \
  "$project_root/tools/mgba_bridge.c" \
  -L"$mgba_root/build" -lmgba -Wl,-rpath,"$mgba_root/build" \
  -o "$project_root/build/mgba_bridge.so"
