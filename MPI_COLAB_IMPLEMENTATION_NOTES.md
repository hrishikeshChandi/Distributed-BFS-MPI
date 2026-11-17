# MPI and Colab implementation notes

## Why Open MPI is selected explicitly

The previous Colab run used MPICH/Hydra. Although two processes were launched, the observed program output reported `rank=0,size=1` twice. This is not a two-rank `MPI_COMM_WORLD`; it means the earlier result cannot be used as evidence of distributed execution.

The revised notebooks use Debian/Ubuntu's Open MPI packages (`openmpi-bin`, `libopenmpi-dev`) and versioned entry points:

- Compiler wrapper: `/usr/bin/mpicxx.openmpi`
- Process launcher: `/usr/bin/mpirun.openmpi`

Ubuntu package file lists include these versioned executables. The wrapper and launcher are selected by absolute path rather than whichever generic alternatives happen to appear first on `PATH`.

## Independent MPI probe

Before BFS execution, the helper compiles a small C++ MPI executable using the Open MPI wrapper. Each process calls:

1. `MPI_Init`;
2. `MPI_Comm_rank(MPI_COMM_WORLD, &rank)`;
3. `MPI_Comm_size(MPI_COMM_WORLD, &size)`;
4. `MPI_Get_library_version`;
5. `MPI_Finalize`.

For a requested process count `P`, the probe must print exactly one line for every rank in `[0, P-1]`, every line must report `size=P`, and the reported MPI library must identify itself as Open MPI. A return code of zero alone is insufficient. For Notebook 01, the required two-rank proof is exactly rank 0 and rank 1, each with communicator size 2.

The BFS binary is built with that same compiler wrapper. The helper records `ldd` output and rejects a binary that does not link against `libmpi.so` or that shows MPICH linkage. Notebooks 02 and 03 repeat the process probe for their entire requested rank sets before beginning expensive experiments.

## Open MPI launcher flags

The launcher prefix is:

```bash
mpirun.openmpi --allow-run-as-root --oversubscribe --bind-to none -np P PROGRAM
```

- `--allow-run-as-root` is present because managed Colab kernels may run inside a root-owned runtime. Open MPI documents this override for container-like environments while strongly discouraging root execution generally; it is not a general-purpose recommendation for a normal user workstation.
- `--oversubscribe` allows the process-count experiment to launch even when Colab reports fewer CPU slots than the requested ranks. The notebook records logical CPU count and warns that these runs are oversubscribed; they must not be described as multi-node scaling.
- `--bind-to none` avoids pinning each rank to an individual core in this constrained, single-VM environment.

Open MPI's documented `mpirun -n X` behavior is to launch X program copies in the runtime environment (on localhost when no multi-node resource manager/hostfile is supplied). The MPI communicator probe independently checks that the launched processes really joined one `MPI_COMM_WORLD` of the requested size.

## Environment hygiene

The helper strips inherited MPI/PMI/PMIx/MPICH/Hydra/PRRTE environment prefixes from the subprocess environment and removes MPICH/Hydra-specific library/include path entries. The launcher and compiler remain explicit absolute paths. The helper rejects generic-wrapper fallbacks.

## ZIP creation is a success-only transaction

Each notebook:

1. Removes its previous result archive at startup so a stale ZIP cannot be mistaken for the new run.
2. Runs each required operation and validation.
3. Writes a `SUCCESS.json` only after the required outputs have passed.
4. Calls one ZIP helper at the final success point.
5. The helper creates a temporary archive, verifies ZIP integrity and the embedded success manifest, persists a copy in Drive, and invokes Colab's browser-download function.
6. If ZIP creation or download invocation raises, the helper removes local and Drive ZIP files, and the notebook removes its success marker.

Failure/diagnostic JSON and logs remain in Drive, but are never packaged as a successful results ZIP. If Colab terminates the VM abruptly, Python cleanup cannot run; the successful archive is not created until the final cell reaches the packaging function. Notebook 02 and 03 retain validated per-configuration checkpoints to allow resume.

## Storage model

- `/content/Distributed_BFS_MPI`: temporary local source/build/execution copy.
- `/content/drive/MyDrive/Distributed_BFS_MPI_Colab`: persistent source, data cache, checkpoints, raw outputs and generated ZIPs.

Colab's managed VMs may be idle-terminated and have maximum lifetimes. The notebooks therefore do not rely on `/content` for persistent state.

## Honest verification boundary

Local verification in the authoring environment checked notebook structure/syntax, helper logic, shell/Python scripts, serial-compatibility smoke tests, result validation, report generation, ZIP success guards and rejection of fake launchers that ignore `-np`. It did **not** execute a live Open MPI process group in Google Colab. The first real Open MPI probe in Notebook 01 is therefore still a required runtime validation, not a pre-claimed pass.

## Official implementation references

- Open MPI `mpirun` documentation: https://docs.open-mpi.org/en/main/man-openmpi/man1/mpirun.1.html
- Ubuntu `openmpi-bin` package file list (versioned wrappers): https://packages.ubuntu.com/jammy/all/openmpi-bin/filelist
- MPI Forum standard: https://www.mpi-forum.org/docs/
- Google Colab FAQ (VM lifetime and resource variability): https://research.google.com/colaboratory/faq.html
