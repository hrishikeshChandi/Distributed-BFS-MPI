#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/build"
MPICXX="${MPICXX:-mpicxx}"
command -v "$MPICXX" >/dev/null || { echo "MPI compiler '$MPICXX' not found. Install MPICH/Open MPI." >&2; exit 1; }
"$MPICXX" -O3 -std=c++17 -Wall -Wextra -Wpedantic "$ROOT/src/distributed_bfs.cpp" -o "$ROOT/build/distributed_bfs"
echo "Built $ROOT/build/distributed_bfs"
