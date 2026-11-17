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
