# Algorithm and measurement methodology

## Distributed BFS

The graph is partitioned into contiguous vertex-ID ranges. Each MPI rank stores CSR adjacency rows only for vertices it owns. BFS is level-synchronous: a rank expands its local frontier, keeps local discoveries, and sends remote `(vertex,parent)` candidates to the destination owners. The blocking version uses `MPI_Alltoallv`; the non-blocking version uses `MPI_Ialltoallv` while processing locally owned candidates. A required `MPI_Allreduce` of the next-frontier size detects global termination.

The original mapping is compared with a deterministic, fixed-seed eight-round Feistel pseudorandom permutation. Cycle-walking restricts the permutation to the exact vertex domain `[0,N)`, including non-power-of-two SNAP vertex counts. The mapping is bijective, so graph topology is preserved while IDs and contiguous rank ownership change.

## Correctness validation

Every BFS run checks root state, parent-level consistency, existence of parent edges and BFS closure. For `N <= 2^21`, all distributed levels and adjacency rows are gathered to rank 0 and the levels are compared against an independent sequential queue-based BFS. Above the configured threshold, the serial reference is skipped to avoid gathering the full graph on rank 0; distributed structural checks still run. Use `--reference-max-vertices` only after considering rank-0 memory requirements.

## Timed region and TEPS

`elapsed_ms` is the maximum rank's elapsed time for the BFS traversal. The timed region begins after a start barrier and includes local traversal work, per-level packing/exchange, and the `MPI_Allreduce` required to determine whether the next frontier is empty. It excludes graph construction, CSR construction, parent/level validation, the sequential reference check and the post-BFS reductions used to aggregate diagnostic measurements.

Only the required next-frontier termination reduction remains inside the BFS loop. Timing/traffic/frontier diagnostics are saved locally for each level and aggregated after the BFS timer stops. This removes the previous nine per-level instrumentation reductions from the timed path. Local `MPI_Wtime` calls remain for phase measurements.

`TEPS` is traversed edges/arcs divided by `elapsed_ms` in seconds. For undirected inputs, the symmetric CSR arcs are divided by two so each undirected edge is counted once; directed inputs count traversed arcs.

## Per-level timing columns

`per_level.csv` records the maximum rank-local duration for each timed phase (except remote-pair and frontier counts, which are globally aggregated):

- `expansion_ms`: frontier traversal and local/remote candidate creation.
- `packing_ms`: local message-count preparation, buffer allocation, packing and byte-displacement preparation, excluding the count collective itself.
- `count_exchange_ms`: the `MPI_Alltoall` exchanging per-rank payload counts.
- `collective_request_ms`: blocking `MPI_Alltoallv` duration in blocking mode; in non-blocking mode, time from `MPI_Ialltoallv` initiation through completion of `MPI_Wait`. The non-blocking value includes local-candidate work performed while the request is outstanding and is therefore an overlap diagnostic, not an additive communication duration.
- `local_candidate_ms`: processing candidates owned by the local rank.
- `residual_wait_ms`: time spent in `MPI_Wait` after local-candidate processing in non-blocking mode (zero for blocking mode).
- `received_merge_ms`: processing candidates received from other ranks.
- `level_wall_ms`: local level duration including the required termination reduction; CSV stores the maximum across ranks.
- `remote_pairs_sent` and `remote_payload_bytes`: globally summed remote `(vertex,parent)` pairs and estimated pair payload bytes (16 bytes per pair).
- `frontier_imbalance`: maximum rank-local next-frontier size divided by the average next-frontier size.

The analysis script derives `computation_ms = expansion_ms + local_candidate_ms + received_merge_ms`. It derives exposed communication as `packing_ms + count_exchange_ms + collective_request_ms` for blocking mode and `packing_ms + count_exchange_ms + residual_wait_ms` for non-blocking mode. This deliberately counts only the communication wait exposed after overlapped local work. The request lifetime is plotted separately for context. The stacked computation/exposed-communication plot is an explanatory phase view, not an assertion that all components must sum exactly to `level_wall_ms`; collective synchronization, allocations and overlap can cause differences.

## Scaling and graph-structure metrics

- `speedup`: median P=1 elapsed time divided by median P-rank elapsed time for the same dataset, ordering and mode.
- `efficiency`: speedup divided by P, multiplied by 100%.
- `edge_cut_fraction`: rank-local CSR arcs whose destination belongs to a different rank divided by all local CSR arcs.
- `edge_load_imbalance`: maximum rank-local CSR adjacency entries divided by the minimum.
- `frontier_imbalance`: maximum local next-frontier size divided by the mean local next-frontier size for that level.
- `remote_pairs_sent`: actual remote candidate-pair volume; it is distinct from static edge cut.

Original and random orderings are compared at matched rank counts. Remote-pair plots retain rank-count resolution rather than collapsing across P. Blocking/non-blocking comparisons use end-to-end elapsed time for a fixed dataset, rank count and ordering; non-blocking collectives do not guarantee asynchronous progress or speedup.

## Instrumentation caveat

The traversal timer still includes the required per-level termination collective and all algorithmic message preparation/exchange work. It excludes the diagnostic array reductions performed after traversal. The timing fields are phase diagnostics; their aggregation uses per-level maximums across ranks, which need not be attained by the same rank for every field.
