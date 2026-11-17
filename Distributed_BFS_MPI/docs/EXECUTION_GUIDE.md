# Execution guide

1. Install an MPI-3 implementation and Python dependencies (see the root README).
2. Run `scripts/build.sh`.
3. Run the 2-rank scale-10 blocking and non-blocking correctness tests from README.
4. Download SNAP inputs with `scripts/download_snap_graphs.sh`.
5. Run a reduced matrix first: `RUN_SNAP=0 SCALES="16" RANKS="1 2 4" REPETITIONS=2 scripts/run_experiments.sh`.
6. Run the full matrix on suitable hardware: `scripts/run_experiments.sh`.
7. Inspect `results/run_*/csv/summary.csv`, the per-level and rank-metric CSVs, all plots (including request-lifetime and by-rank remote-traffic charts), `report/Two_Page_Report.docx` and `presentation/Distributed_BFS_Results_Presentation.pptx`.
8. Zip the result folder and share it for independent analysis before finalizing conclusions.

The complete matrix can be computationally expensive. Scale 24 with edge factor 8 creates a large graph; ensure adequate RAM, storage and CPU cores. If the machine cannot accommodate the 1-rank largest-scale run, use a documented subset of scales and explain the hardware constraint rather than silently dropping failed runs.
