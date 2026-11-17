# Distributed BFS with MPI

A C++17 implementation of distributed Breadth-First Search (BFS) using MPI-3. The project evaluates distributed graph traversal using 1D vertex partitioning, local CSR adjacency storage, blocking and nonblocking MPI communication, and graph vertex relabelling.

## Project Contents

- `01_Setup_and_Correctness.ipynb` — Open MPI environment setup, communicator verification, compilation, and distributed BFS correctness checks.
- `02_Pilot_Benchmark.ipynb` — RMAT scale 16 pilot benchmark.
- `03_Full_Experiment_Matrix.ipynb` — SNAP and RMAT benchmark experiments with checkpointed execution.
- `04_Rebuild_Reports.ipynb` — Rebuilds plots, reports, and presentation from the saved validated partial-matrix results.
- `04_Rebuild_Reports_Full_Matrix_Legacy.ipynb` — Older report-generation workflow retained for reference.
- `colab_helpers.py` — Shared Colab setup, validation, checkpoint, and success-only ZIP helpers.
- `Distributed_BFS_MPI/` — C++ source code, shell/Python scripts, tests, and technical documentation.
- `runs/` — Experiment configurations, checkpoints, logs, and aggregated results.
- `exports/` — Generated plots, reports, and presentation.
- `data/snap/` — Downloaded SNAP datasets (excluded from GitHub).

## Implementation

- Language: C++17
- Parallel programming: MPI-3 / Open MPI
- Graph representation: Compressed Sparse Row (CSR)
- Partitioning: 1D contiguous vertex partitioning
- Communication: `MPI_Alltoallv` and `MPI_Ialltoallv`
- Termination detection: `MPI_Allreduce`
- Analysis: Python, Pandas, and Matplotlib
- Execution environment: Google Colab CPU runtime

## Experiment Status

The full experiment matrix was designed to contain:

- 12 graph datasets: 3 SNAP datasets and 9 synthetic RMAT scales.
- 5 MPI process counts: 1, 2, 4, 8, and 16.
- 2 vertex orderings: original and randomized.
- 2 communication modes: blocking and nonblocking.

This gives 240 planned configurations and 3,840 planned BFS traversals.

A total of 234 configurations completed and passed validation, representing 3,744 BFS traversals. Six configurations involving RMAT scale 24 at 8 and 16 MPI ranks were not completed because the Colab runtime terminated during execution.

The saved reports and plots are generated from the 234 validated configurations. The experiment is therefore a validated partial matrix, not a completed 240-configuration matrix.

## Dataset Sources

The real-world graph datasets are from the Stanford Network Analysis Project (SNAP):

- soc-Epinions1
- web-Google
- roadNet-CA

The RMAT graphs are synthetically generated.

The downloaded SNAP graph files are not included in the Git repository. Use the dataset download script and source information in the project to obtain them.

## Execution Platform and Limitations

Experiments were executed on a single Google Colab CPU virtual machine.

All MPI ranks ran on the same VM. This is multi-process MPI benchmarking, not multi-node cluster benchmarking.

The Colab environment used two logical CPUs. Runs with more than two MPI ranks involved CPU oversubscription. Consequently, performance results should be interpreted in the context of the available VM resources.

The results do not establish linear or near-linear multi-node scaling.

## Reproduction

1. Open the notebooks in Google Colab.
2. Execute the setup and correctness notebook first.
3. Execute the pilot benchmark.
4. Execute the full experiment matrix with sufficient runtime resources.
5. Use the report-generation notebook to rebuild reports from validated results.

See `START_HERE.md` and the documentation under `Distributed_BFS_MPI/` for detailed instructions.
