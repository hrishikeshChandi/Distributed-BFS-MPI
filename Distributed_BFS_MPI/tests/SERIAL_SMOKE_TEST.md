# Corrected serial smoke-test record

The corrected source was compiled with g++ using the included single-rank MPI shim. The following checks passed:

- Scale-10, edge-factor-4 synthetic graph, three BFS sources each: original/blocking, original/non-blocking, Feistel-random/blocking and Feistel-random/non-blocking. All 12 runs reported `validation=PASS`.
- Small directed SNAP-style edge list with non-dense external IDs, Feistel-random ordering and non-blocking mode: `validation=PASS`.
- Feistel cycle-walking bijection test for power-of-two and non-power-of-two domains from N=2 through N=2,097,152, including non-power-of-two SNAP vertex counts: `PASS` (no collisions or out-of-range IDs).
- The corrected per-level CSV schema includes separate packing, count-exchange, request-lifetime and exposed-wait measurements.

Example permutation test command:

```bash
g++ -O2 -std=c++17 -I mpi_stub tests/permutation_bijection_smoke.cpp -o build/permutation_bijection_smoke
build/permutation_bijection_smoke
```

**Scope limitation:** these tests use one process. They do not validate inter-rank `Alltoallv` exchange, actual MPI request progress/overlap, rank partition boundaries or multi-rank scaling. A real MPI run is still required before claiming the distributed implementation has passed execution verification.
