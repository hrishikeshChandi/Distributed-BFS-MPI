# Two-page report structure

**Team 10:** Gaurav Mishra and Hrishikesh Chandi

1. Problem and motivation: distributed BFS, communication cost, 1D ownership.
2. Method: local CSR, MPI_Alltoallv, required termination MPI_Allreduce, blocking/non-blocking variants, deterministic Feistel relabelling.
3. Inputs: SNAP social/web/road and R-MAT scales 16–24; 16 sources per configuration.
4. Metrics: median TEPS, scaling, per-level computation and exposed communication, request lifetime, edge cut, imbalance and remote-pair traffic.
5. Findings: populate only from generated CSVs. Discuss cases where non-blocking overlaps or fails to improve; relate shuffled IDs to cut and balance.
6. Timing methodology: BFS elapsed time includes required termination collectives; post-run diagnostic reductions and correctness validation are excluded. Non-blocking request lifetime overlaps local-candidate work and must not be added to that computation time.
7. Limitations: hardware and MPI version, root sequential-reference threshold of 2^21 vertices by default, no claim of full Graph500 compliance.
