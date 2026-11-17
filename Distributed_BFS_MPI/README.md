# Distributed Breadth-First Search with MPI

**Course:** Multicore Architecture and Programming — Unit III (message passing, MPI collectives)  
**Team:** Team 10 — Gaurav Mishra and Hrishikesh Chandi  
**Implementation:** C++17 + MPI-3; Python 3 for analysis, plots and presentation.  
**Algorithm:** Level-synchronous 1D vertex-partitioned distributed BFS using local CSR storage.

## What is implemented

- Contiguous 1D vertex ownership across MPI ranks.
- Distributed graph construction: each rank generates its assigned R-MAT edge-ID range, or rank 0 reads a SNAP edge list; edges are routed to the owner of their source vertex and stored as local CSR rows.
- Per-level remote `(vertex,parent)` discovery exchange using `MPI_Alltoallv`.
- Global termination using `MPI_Allreduce` on the next-frontier size.
- Blocking `MPI_Alltoallv` and non-blocking `MPI_Ialltoallv` variants. The non-blocking variant processes local candidates while the exchange is outstanding, then waits and merges received candidates.
- Original and fixed-seed bijective eight-round Feistel pseudorandom vertex relabelling (cycle-walked over the actual vertex domain). The topology is preserved; only IDs/partition ownership change.
- Sixteen deterministic random BFS source vertices per graph/configuration by default; median TEPS is computed across the source runs.
- Per-level expansion, packing, count-exchange, payload-request, exposed-wait and merge timings. Diagnostic reductions are performed after the BFS timer stops; only the required global-termination reduction remains inside the timed level loop.
- Static edge cut and per-rank edge-load metrics.
- Parent/level and BFS-closure validation on every run. For graphs up to 2^21 vertices, exact level arrays are also checked against a sequential queue-based BFS reference. Above that threshold, the implementation uses distributed structural validation to avoid gathering a very large graph on rank 0.

## Project layout

```text
Distributed_BFS_MPI/
├── src/distributed_bfs.cpp
├── scripts/
│   ├── build.sh
│   ├── build_serial_smoke.sh
│   ├── download_snap_graphs.sh
│   ├── run_experiments.sh
│   ├── analyze_results.py
│   ├── generate_report.py
│   ├── generate_report_docx.py
│   └── make_presentation.py
├── mpi_stub/mpi.h                 # single-rank smoke-test shim only
├── docs/                          # algorithm, metrics, execution and result schema
├── data/snap/                      # downloaded SNAP files (not bundled)
├── presentation/                   # presentation outline/template
├── report/                         # report outline
├── tests/                           # smoke-test record and checks
├── build/                           # generated executable
└── results/                         # generated CSVs, logs, plots and reports
```

## 1. Requirements and installation

Use Linux (Ubuntu 22.04/24.04 recommended), a C++17 compiler and an MPI-3 implementation. MPICH or Open MPI are both suitable.

```bash
sudo apt update
sudo apt install -y build-essential mpich libmpich-dev python3 python3-pip python3-venv curl gzip
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas matplotlib python-pptx python-docx tabulate
```

If you use Open MPI instead, install `openmpi-bin libopenmpi-dev`. Ensure `mpicxx` and `mpirun` are on `PATH`.

**Colab-specific note:** do not mix MPICH and Open MPI wrappers in the same runtime. The included Colab notebooks install/select Open MPI using the explicit paths `/usr/bin/mpicxx.openmpi` and `/usr/bin/mpirun.openmpi`, probe actual `MPI_COMM_WORLD` sizes, and build with the same compiler wrapper. Follow the root-level `START_HERE.md`; the manual MPICH command above is for a separate native Ubuntu setup only.

## 2. Build

From the project root:

```bash
chmod +x scripts/*.sh
scripts/build.sh
```

This creates `build/distributed_bfs`. Check options with:

```bash
mpirun -np 1 build/distributed_bfs --help
```

## 3. Quick real-MPI correctness test (start here)

Run a small graph with two ranks before downloading the full data or starting the scale sweep:

```bash
mkdir -p results/manual/csv
mpirun -np 2 build/distributed_bfs \
  --scale 10 --edge-factor 4 --repetitions 2 \
  --ordering original --mode blocking \
  --summary-csv results/manual/csv/summary.csv \
  --per-level-csv results/manual/csv/per_level.csv \
  --rank-csv results/manual/csv/rank_metrics.csv

mpirun -np 2 build/distributed_bfs \
  --scale 10 --edge-factor 4 --repetitions 2 \
  --ordering original --mode nonblocking \
  --summary-csv results/manual/csv/summary.csv \
  --per-level-csv results/manual/csv/per_level.csv \
  --rank-csv results/manual/csv/rank_metrics.csv
```

Both should end with `validation=PASS`. Try random ordering too. This test is for correctness only, not a reportable performance result.

## 4. SNAP real-world graph inputs

The download script fetches three representative SNAP datasets:

| Dataset | Type | Directed? | Source |
|---|---|---:|---|
| `soc-Epinions1` | Social trust network | Yes | Stanford SNAP |
| `web-Google` | Web hyperlinks | Yes | Stanford SNAP |
| `roadNet-CA` | California road network | No (symmetrized) | Stanford SNAP |

Download and decompress:

```bash
scripts/download_snap_graphs.sh
```

Files are kept in `data/snap/`; they are not included in the source ZIP because they are third-party datasets and can be several hundred MB. The project reads the standard two-column SNAP edge-list format, skips comment/header lines and maps the observed ID interval to zero-based contiguous IDs. Directed graphs preserve direction. For the undirected road graph, reverse arcs are added and duplicate adjacency entries are removed during CSR construction.

## 5. Full assigned experiment matrix

Default full run:

```bash
scripts/run_experiments.sh
```

By default this runs:

- SNAP: social, web and road datasets above.
- Synthetic R-MAT: scales 16 through 24 (N = 2^scale), edge factor 8.
- MPI ranks: 1, 2, 4, 8 and 16.
- Vertex orderings: original and fixed-seed random relabelling.
- Communication modes: blocking and non-blocking.
- BFS sources: 16 deterministic random sources per configuration.

This is a large experiment matrix. Start with a reduced trial, then run the full matrix on a multi-core Linux machine or MPI cluster:

```bash
# Short functional run
RUN_SNAP=0 SCALES="16" RANKS="1 2 4" REPETITIONS=2 scripts/run_experiments.sh

# Full run (default)
RUN_SNAP=1 RUN_RMAT=1 SCALES="16 17 18 19 20 21 22 23 24" \
RANKS="1 2 4 8 16" REPETITIONS=16 scripts/run_experiments.sh
```

The runner creates `results/run_YYYYMMDD_HHMMSS/` containing CSVs, logs, plots, environment metadata, a measured report and a results-filled PowerPoint. It stops on the first failed run and retains partial output for debugging.

**Important:** do not interpret timings from an oversubscribed 16-rank run as ideal scaling. Use a host with enough CPU cores for the requested rank count, or clearly label oversubscription and CPU binding. For example, set `MPIEXEC_FLAGS="--bind-to core"` for Open MPI when appropriate. MPI implementations differ in their launcher flags.

## 6. Outputs and metrics

- `csv/summary.csv`: one row per graph/source/rank/order/mode. Contains elapsed time, traversed-edge count, TEPS, reachable vertices, actual remote candidate pairs, estimated payload bytes and validation status.
- `csv/per_level.csv`: per-level frontier, expansion, packing, count-exchange, payload collective/request lifetime, local-candidate processing, residual wait, received-candidate merge, level wall time, remote pairs/bytes and frontier imbalance.
- `csv/rank_metrics.csv`: per-rank local CSR adjacency count and cut-arc count, tagged by dataset and ordering.
- `plots/teps_*.png`: TEPS versus rank count.
- `plots/per_level_<dataset>.png`: computation versus exposed communication by BFS level, with actual level-wall overlay.
- `plots/collective_request_<dataset>.png`: payload collective/request lifetime, shown separately because non-blocking lifetime overlaps local computation.
- `plots/cut_imbalance_<dataset>.png`: edge-cut and static edge-load metrics versus TEPS for both vertex orderings.
- `plots/remote_pairs_by_rank_<dataset>.png`: remote candidate-pair traffic at each rank count for both orderings.
- `plots/summary_aggregated.csv`: median TEPS/time across source vertices, speedup and parallel efficiency.
- `plots/per_level_derived.csv`: per-level computation, communication setup and exposed communication derived from the raw phase columns.
- `report/Two_Page_Report.docx`: generated two-page report section.
- `presentation/Distributed_BFS_Results_Presentation.pptx`: presentation with measured charts where available.

### Metric definitions

- **TEPS:** number of traversed edges/arcs divided by end-to-end BFS elapsed time. Undirected inputs count each undirected edge once; directed inputs count traversed arcs.
- **Speedup:** median P=1 elapsed time / median P-rank elapsed time, matched by dataset, ordering and communication mode.
- **Efficiency:** speedup / P × 100%.
- **Edge cut:** number of directed CSR arcs whose destination is owned by a different rank, divided by all directed CSR arcs for the cut fraction. For undirected inputs, each crossing undirected edge appears as two cut arcs; the fraction is unchanged.
- **Static edge-load imbalance:** maximum rank-local adjacency entries / minimum rank-local adjacency entries.
- **Frontier imbalance:** maximum local next-frontier size / average local next-frontier size at that level.
- **Remote candidate traffic:** actual `(vertex,parent)` pairs sent to remote owners. Estimated payload bytes = pair count × 16; excludes MPI protocol and collective metadata.
- **Computation:** expansion + local-candidate processing + received-candidate merge. **Exposed communication:** packing + count exchange + blocking payload collective, or packing + count exchange + residual wait for non-blocking mode.
- **Non-blocking overlap:** `collective_request_ms` is the full request lifetime and includes local-candidate work performed while the request is outstanding. It is plotted separately and must not be added to local-candidate time. The exposed-communication chart counts only the residual wait after local work. Compare end-to-end elapsed time between modes to decide whether overlap helped.

## 7. Rank-1 smoke test when MPI is unavailable

A compatibility shim is included only to test graph generation, local CSR, BFS, CSV output and sequential-reference validation on one process:

```bash
scripts/build_serial_smoke.sh
mkdir -p results/smoke
build/distributed_bfs_stub --scale 10 --edge-factor 4 --repetitions 3 \
  --ordering original --mode blocking \
  --summary-csv results/smoke/summary.csv \
  --per-level-csv results/smoke/per_level.csv \
  --rank-csv results/smoke/rank_metrics.csv
```

**This is not MPI and cannot validate inter-rank exchange, communication overlap or distributed scaling. Do not submit stub timings as distributed MPI results.**

## 8. Accuracy, limitations and reproducibility

- R-MAT edge generation is deterministic for a given scale, edge factor and graph seed. Each rank generates a disjoint edge-ID interval; graph generation is distributed rather than replicated.
- Original and shuffled runs use the same underlying graph and fixed permutation seed. The mapping is a deterministic eight-round Feistel pseudorandom bijection, not a new random graph sample.
- BFS source vertices are generated deterministically from the source seed and repeated identically across rank/mode comparisons.
- CSR rows are sorted and duplicate adjacency entries removed.
- Graph construction and CSR distribution are excluded from BFS timing. The timed region includes BFS-level packing/exchange work and the required termination `MPI_Allreduce`, but excludes post-BFS per-level metric aggregation and correctness validation.
- Exact sequential queue-based level comparison is enabled by default up to 2^21 vertices to avoid gathering very large graphs on rank 0. All graph sizes still receive distributed parent/level and BFS-closure checks. The threshold can be changed with `--reference-max-vertices` only after considering root memory requirements.
- MPI non-blocking collectives permit but do not guarantee asynchronous progress. Results depend on MPI library, CPU binding and hardware.
- This educational R-MAT implementation is not a full Graph500 generator or benchmark submission. Graph500 uses a more specific generator, validation and timing rules.

## 9. References

1. A. Buluç and K. Madduri, “Parallel Breadth-First Search on Distributed Memory Systems,” SC 2011. [Paper PDF](https://people.eecs.berkeley.edu/~aydin/sc11_bfs.pdf) · [arXiv](https://arxiv.org/abs/1104.4518).
2. MPI Forum, *MPI Standard*, including collective and non-blocking collective semantics. [MPI standards](https://www.mpi-forum.org/docs/).
3. Stanford Large Network Dataset Collection (SNAP). [Dataset catalogue](https://snap.stanford.edu/data/).
4. D. Chakrabarti, Y. Zhan and C. Faloutsos, “R-MAT: A Recursive Model for Graph Mining,” SIAM SDM 2004. [DOI](https://doi.org/10.1137/1.9781611972740.43).
5. Graph500 Benchmark Specification — TEPS definition and BFS reporting. [Specification](https://graph500.org/?page_id=12).


## Google Colab workflow

A Colab automation bundle is provided separately. It includes notebooks for setup/two-rank correctness, pilot benchmarking, the full checkpointed experiment matrix, and report regeneration. The notebooks mount Drive and persist the project source, SNAP dataset cache, per-configuration checkpoints, CSVs, logs, plots, reports and PowerPoint under `MyDrive/Distributed_BFS_MPI_Colab/`. Compile and run from the Colab VM's local disk; do not use the serial MPI shim for submitted performance results. See `START_HERE.md` at the root of the Colab bundle. The Colab notebooks explicitly use Open MPI and verify `MPI_COMM_WORLD` size before starting BFS.
