# Result schema

## summary.csv

One row per BFS source/configuration: dataset, vertex count, edge count, ranks, ordering, communication mode, source index and ID, elapsed milliseconds, traversed-edge count, TEPS, reachable vertices, remote candidate pairs, estimated payload bytes, validation status, graph seed and permutation seed.

## per_level.csv

One row per source and BFS level. Columns:

- Identity: `dataset`, `vertices`, `ranks`, `ordering`, `mode`, `source_index`, `level`.
- Frontier: `next_frontier`, `frontier_imbalance`.
- Timings: `expansion_ms`, `packing_ms`, `count_exchange_ms`, `collective_request_ms`, `local_candidate_ms`, `residual_wait_ms`, `received_merge_ms`, `level_wall_ms`.
- Traffic: `remote_pairs_sent`, `remote_payload_bytes`.

`collective_request_ms` means the blocking payload collective duration for blocking mode, or the full non-blocking request lifetime through `MPI_Wait` for non-blocking mode. In non-blocking mode it includes local-candidate work that overlaps the request; do not add it to `local_candidate_ms`.

## rank_metrics.csv

One row per rank and dataset/ordering: local adjacency-entry count and cut-arc count. Aggregate across ranks to calculate edge-load imbalance and edge-cut fraction.

## Analysis outputs

- `summary_aggregated.csv`: median TEPS and elapsed time, source count, speedup and efficiency by dataset/order/mode/rank count.
- `per_level_derived.csv`: raw per-level values plus derived computation, communication setup and exposed communication fields.
- `teps_<dataset>.png`: TEPS versus rank count.
- `per_level_<dataset>.png`: computation versus exposed communication with measured level-wall overlay.
- `collective_request_<dataset>.png`: payload collective/request lifetime, shown separately because it overlaps local computation in non-blocking mode.
- `cut_imbalance_<dataset>.png`: edge cut and edge-load imbalance versus TEPS for both vertex orderings.
- `remote_pairs_by_rank_<dataset>.png`: remote candidate-pair volume at each rank count for both orderings.
