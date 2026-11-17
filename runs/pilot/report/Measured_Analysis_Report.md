# Distributed BFS with MPI — Measured Results

**Team 10:** Gaurav Mishra and Hrishikesh Chandi

Validated BFS runs: **24** across **1** datasets.

## Median TEPS by dataset and configuration

| dataset   |   ranks | ordering   | mode        |   median_teps |   median_elapsed_ms |   sources |   median_remote_pairs |
|:----------|--------:|:-----------|:------------|--------------:|--------------------:|----------:|----------------------:|
| RMAT_s16  |       1 | original   | blocking    |   1.74542e+07 |             6.84733 |         2 |                     0 |
| RMAT_s16  |       1 | original   | nonblocking |   2.17094e+07 |             5.50785 |         2 |                     0 |
| RMAT_s16  |       1 | random     | blocking    |   1.53094e+07 |             7.80698 |         2 |                     0 |
| RMAT_s16  |       1 | random     | nonblocking |   1.4807e+07  |             8.07637 |         2 |                     0 |
| RMAT_s16  |       2 | original   | blocking    |   3.14833e+06 |            37.991   |         2 |                188023 |
| RMAT_s16  |       2 | original   | nonblocking |   8.62965e+06 |            14.3538  |         2 |                188023 |
| RMAT_s16  |       2 | random     | blocking    |   3.57074e+06 |            35.0795  |         2 |                239054 |
| RMAT_s16  |       2 | random     | nonblocking |   4.52819e+06 |            26.4864  |         2 |                239054 |
| RMAT_s16  |       4 | original   | blocking    |   4.11724e+06 |            30.4449  |         2 |                302153 |
| RMAT_s16  |       4 | original   | nonblocking |   3.40443e+06 |            36.1084  |         2 |                302153 |
| RMAT_s16  |       4 | random     | blocking    |   6.47295e+06 |            18.7094  |         2 |                358205 |
| RMAT_s16  |       4 | random     | nonblocking |   4.3082e+06  |            29.3288  |         2 |                358205 |

## Interpretation guidance

- TEPS is computed from traversed directed arcs (or undirected edges for undirected inputs) divided by measured BFS elapsed time.
- Observed BFS source count per configuration: 2; the table reports median TEPS across the recorded source runs.
- MPI process counts present in this run: 1, 2, 4. These are single-node MPI ranks when executed on Colab.
- Compare blocking and non-blocking only within the same dataset, rank count and vertex ordering. Non-blocking collectives permit overlap but do not guarantee progress or a speedup.
- The timed BFS retains the required global next-frontier termination reduction. Per-level diagnostic reductions are aggregated after the timer stops; graph construction and correctness validation are also outside the timed region.
- Per-level computation is expansion + local-candidate processing + received-candidate merging. Exposed communication is packing + count exchange + blocking payload collective, or packing + count exchange + residual wait for non-blocking mode. The non-blocking request lifetime includes overlapped local work and is therefore shown separately.
- Edge cut and edge-load imbalance are compared for both original and fixed-seed Feistel-relabeled vertex orderings. Remote candidate-pair traffic is shown at each rank count rather than pooled across rank counts.
- For graphs up to 2^21 vertices, levels are additionally compared with a sequential queue-based BFS reference; larger graphs retain distributed structural validation.

## Reproducibility

The raw per-source/per-level CSV files, rank metrics, logs, environment record and plotting scripts accompany this report. No unmeasured values are inserted.

## Environment

```text
MPIEXEC=/usr/bin/mpirun.openmpi
MPIEXEC_FLAGS=--allow-run-as-root --oversubscribe --bind-to none
RANKS=1 2 4
REPETITIONS=2
EDGE_FACTOR=8
SCALES=16
RUNNER_VERSION=mpi-validated-v2-openmpi
SOURCE_FINGERPRINT=622f129fc08cbb2af2d136027d2fe4f92259bbe2b59748192351cdcec4418f24
DATE=2026-11-04T17:00:16+00:00
HOST=1a00880cf773
KERNEL=Linux 1a00880cf773 6.6.159+ #1 SMP Thu Oct 22 03:07:54 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux
--- MPI launcher ---
mpirun.openmpi (OpenRTE) 4.1.6

Report bugs to http://www.open-mpi.org/community/help/
--- compiler ---
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
Copyright (C) 2023 Free Software Foundation, Inc.
--- CPU ---
Model name:                              Intel(R) Xeon(R) CPU @ 2.20GHz
Thread(s) per core:                      2
Core(s) per socket:                      1
Socket(s):                               1
--- memory ---
               total        used        free      shared  buff/cache   available
Mem:            12Gi       1.2Gi       8.8Gi       2.3Mi       2.9Gi        11Gi
Swap:             0B          0B          0B
```