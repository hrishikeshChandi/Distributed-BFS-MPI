# Audit findings and corrections

The following items were checked against the uploaded project ZIP and corrected where confirmed.

| Audit finding | Verification against ZIP | Correction |
|---|---|---|
| Too many MPI reductions inside timed BFS | Confirmed. The previous traversal performed nine diagnostic reductions per BFS level in addition to the required next-frontier termination reduction. | Removed the per-level diagnostic reductions from the timed loop. Local per-level metrics are buffered and aggregated after `elapsed` is stopped. The required global next-frontier `MPI_Allreduce` remains inside the loop. |
| Incomplete computation-versus-communication plot | Confirmed. The old plot used expansion and a combined communication phase while omitting local-candidate and received-merge computation, and it obscured overlap in non-blocking mode. | Added distinct packing, count-exchange, request-lifetime, local-candidate, residual-wait and received-merge columns. The main plot compares computation against exposed communication, overlays level wall time, and shows request lifetime separately. |
| Random relabelling comparison incomplete | Confirmed. The old relabelling was affine and the edge-cut chart selected only original ordering; the remote-pair plot collapsed rank counts into one aggregate. | Replaced the affine family with an eight-round Feistel pseudorandom permutation using cycle-walking over `[0,N)`. Edge-cut/imbalance plots include original and random orderings. Remote-pair plots preserve each rank count for both orderings. Added a direct bijection smoke test. |
| Sequential validation threshold mismatch | Confirmed. C++ and most documentation used `2^21`; presentation slide 8 said `2^22`. | Corrected the slide and regenerated the presentation template. Documentation consistently states the default threshold is `2^21`. |
| Team attribution absent | Confirmed in the report and presentation generators. | Added Team 10 and the supplied member names, Gaurav Mishra and Hrishikesh Chandi, to README, generated report and presentation. |

## Verification performed after the corrections

- C++17 compile using the bundled single-rank MPI compatibility shim.
- Twelve scale-10 synthetic BFS smoke runs across original/random ordering and blocking/non-blocking modes; all reported `validation=PASS`.
- Small directed edge-list smoke run with non-dense source IDs; `validation=PASS`.
- Feistel bijection test across power-of-two and non-power-of-two domains, including 875,713, 1,965,206 and 2,097,152 vertices; `PASS`.
- Analysis script produced aggregated CSVs and the revised TEPS, per-level, request-lifetime, edge-cut and per-rank remote-traffic plots from smoke CSVs.
- Markdown report, two-page DOCX and presentation generation passed on smoke CSVs. The DOCX rendered to two pages; the results presentation contained 17 slides.
- Shell/Python syntax checks and ZIP integrity check passed.

## Still unverified

No `mpicxx` or `mpirun` is installed in the current execution environment. The bundled MPI shim simulates only rank 0 with one process. Therefore, actual 2/4/8/16-rank collectives, non-blocking MPI progress, distributed correctness and scaling performance have **not** been verified. The project intentionally contains no fabricated distributed benchmark results. Run the documented two-rank correctness matrix with a real MPI implementation before launching the full experiment sweep.


## Colab notebook audit (2026-11-04)

A second audit covered all four notebook files and their shared execution helpers.

| Finding | Correction |
|---|---|
| The previous MPICH run launched two singleton jobs (`rank=0,size=1` twice). | Replaced the notebook MPI path with explicit Open MPI package wrappers. Added an independent probe that validates every rank and the communicator size before BFS. |
| Other notebooks could independently pick generic MPICH/alternate wrappers. | All experiment notebooks use the shared helper and explicit Open MPI compiler/launcher paths. They repeat communicator-size probes for their requested process counts. Notebook 04 is report-only and does not alter MPI. |
| Result ZIPs were created from failure/cleanup paths in earlier notebook versions. | ZIP generation is called only after successful validation and is not placed in `finally`. The previous archive is removed at notebook start. A failed run removes any newly-created archive and its success marker. |
| A previous success manifest could survive a rerun that failed before the new archive completed. | Prerequisite checks now require the Drive ZIP, verify its integrity and confirm the embedded success manifest as well as the JSON/CSV results. |
| Benchmark runs did not uniformly prove requested MPI rank count. | Per-configuration validation now checks `ranks` in summary/per-level CSVs, exact rank IDs in rank metrics, all repetitions, configuration identity and the completion log before a checkpoint can be marked `.done`. |
| The full matrix's SNAP input cache was not consistently reused. | Notebook 03 restores datasets from Drive, downloads only missing graphs, validates non-empty files, copies downloaded files back to Drive and records their SHA-256 hashes in the run configuration. |
| Report rebuilding could be mistaken for a benchmark run. | Notebook 04 is explicitly report-only: it validates a completed CSV matrix and rebuilds plots/documents without reinstalling MPI or compiling/running BFS. |

### Notebook verification performed locally

- All four notebooks parsed as nbformat 4 documents; every code cell passed Python syntax compilation.
- Shared helper and all project Python scripts passed `py_compile`; project shell scripts passed `bash -n`.
- Helper tests verified the ZIP success guard, archive integrity check and the behavior when no success manifest exists.
- A test runner using the serial compatibility shim completed a reduced one-rank matrix through CSV analysis, plots, Markdown, DOCX and PPTX generation. This verifies pipeline integration only.
- A deliberately faulty launcher that ignored `-np 2` was rejected by rank-count validation before a completion checkpoint was written.

### Still to be verified in Colab

No live Open MPI multi-rank group has been run in this authoring environment. Notebook 01 must prove `rank=0,size=2` and `rank=1,size=2` in Colab, and all four two-rank BFS configurations must pass before Notebook 02 is allowed to proceed. The serial MPI shim is not accepted as distributed execution evidence.
