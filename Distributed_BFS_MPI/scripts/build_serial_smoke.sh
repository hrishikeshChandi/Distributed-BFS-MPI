#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/build"
g++ -O2 -std=c++17 -Wall -Wextra -I"$ROOT/mpi_stub" "$ROOT/src/distributed_bfs.cpp" -o "$ROOT/build/distributed_bfs_stub"
echo "Built rank-1 compatibility smoke executable. This is NOT a distributed MPI test."
