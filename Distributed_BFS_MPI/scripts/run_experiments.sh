#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MPIEXEC="${MPIEXEC:-mpirun}"
EXE="$ROOT/build/distributed_bfs"
command -v "$MPIEXEC" >/dev/null || { echo "MPI launcher '$MPIEXEC' not found" >&2; exit 1; }
[[ -x "$EXE" ]] || "$ROOT/scripts/build.sh"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
OUT="${OUT_DIR:-$ROOT/results/run_$RUN_ID}"
mkdir -p "$OUT/csv" "$OUT/logs" "$OUT/plots" "$OUT/report" "$OUT/presentation"
RANKS="${RANKS:-1 2 4 8 16}"
REPETITIONS="${REPETITIONS:-16}"
EDGE_FACTOR="${EDGE_FACTOR:-8}"
SCALES="${SCALES:-16 17 18 19 20 21 22 23 24}"
RUN_SNAP="${RUN_SNAP:-1}"
RUN_RMAT="${RUN_RMAT:-1}"
CHECKPOINT_DIR="$OUT/checkpoints"
CONFIG_DIR="$OUT/configs"
mkdir -p "$CHECKPOINT_DIR" "$CONFIG_DIR"
RESUME="${RESUME:-1}"

validate_config(){
  local cfg="$1"; local expected_ranks="$2"; local expected_repetitions="$3"
  local expected_dataset="$4"; local expected_ordering="$5"; local expected_mode="$6"
  python3 - "$cfg" "$expected_ranks" "$expected_repetitions" "$expected_dataset" "$expected_ordering" "$expected_mode" <<'PYVALIDATE'
import csv, pathlib, re, sys
cfg=pathlib.Path(sys.argv[1]); p=int(sys.argv[2]); reps=int(sys.argv[3]); dataset,ordering,mode=sys.argv[4:7]
def read(name):
    path=cfg/name
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"{cfg.name}: missing or empty {name}")
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))
summary=read('summary.csv'); levels=read('per_level.csv'); ranks=read('rank_metrics.csv')
if len(summary) != reps: raise SystemExit(f"{cfg.name}: expected {reps} summary rows, got {len(summary)}")
if any(row.get('validation') != 'PASS' for row in summary): raise SystemExit(f"{cfg.name}: summary contains a non-PASS validation")
if any(row.get('dataset') != dataset or row.get('ordering') != ordering or row.get('mode') != mode for row in summary):
    raise SystemExit(f"{cfg.name}: summary identity fields do not match requested configuration")
if sorted(int(row['source_index']) for row in summary) != list(range(reps)):
    raise SystemExit(f"{cfg.name}: summary source indices do not cover exactly 0..{reps-1}")
if {int(row['ranks']) for row in summary} != {p}: raise SystemExit(f"{cfg.name}: requested {p} ranks, summary has {sorted({int(row['ranks']) for row in summary})}")
rank_ids=sorted({int(row['rank']) for row in ranks})
if rank_ids != list(range(p)) or len(ranks) != p or {int(row['ranks']) for row in ranks} != {p}:
    raise SystemExit(f"{cfg.name}: rank metrics mismatch: ids={rank_ids}, rows={len(ranks)}")
if not levels or {int(row['ranks']) for row in levels} != {p}:
    raise SystemExit(f"{cfg.name}: per-level metrics missing or wrong-rank")
if {int(row['source_index']) for row in levels} != set(range(reps)):
    raise SystemExit(f"{cfg.name}: per-level metrics do not cover all source indices")
if any(row.get('dataset') != dataset or row.get('ordering') != ordering or row.get('mode') != mode for row in levels):
    raise SystemExit(f"{cfg.name}: per-level identity fields do not match requested configuration")
if any(row.get('dataset') != dataset or row.get('ordering') != ordering for row in ranks):
    raise SystemExit(f"{cfg.name}: rank metrics identity fields do not match requested configuration")
log=cfg/'run.log'
if not log.is_file(): raise SystemExit(f"{cfg.name}: run.log missing")
text=log.read_text(encoding='utf-8',errors='replace')
found=re.findall(r"Completed dataset=.*?ranks=(\d+).*?validation=PASS",text)
if not found or any(int(x) != p for x in found): raise SystemExit(f"{cfg.name}: output log does not prove ranks={p}: {found}")
print(f"CONFIG_VALIDATION_PASS {cfg.name} ranks={p} sources={len(summary)}")
PYVALIDATE
}

run_one(){
  local dataset="$1"; local ranks="$2"; local ordering="$3"; local mode="$4"; shift 4
  local args=("$@"); local tag="${dataset}_p${ranks}_${ordering}_${mode}"
  local cfg="$CONFIG_DIR/$tag"
  local done="$CHECKPOINT_DIR/$tag.done"
  if [[ "$RESUME" == 1 && -f "$done" ]]; then
    if validate_config "$cfg" "$ranks" "$REPETITIONS" "$dataset" "$ordering" "$mode" >/dev/null 2>&1; then
      echo "[SKIP validated checkpoint] $tag"
      return 0
    fi
    echo "[RETRY invalid checkpoint] $tag"
    rm -f "$done"
  fi
  rm -f "$done"
  rm -rf "$cfg"
  mkdir -p "$cfg"
  echo "[$(date -Is)] START $tag" | tee "$OUT/logs/$tag.log"
  read -r -a mpi_flags <<< "${MPIEXEC_FLAGS:-}"
  "$MPIEXEC" "${mpi_flags[@]}" -np "$ranks" "$EXE" "${args[@]}" \
    --dataset "$dataset" --repetitions "$REPETITIONS" \
    --ordering "$ordering" --mode "$mode" \
    --summary-csv "$cfg/summary.csv" \
    --per-level-csv "$cfg/per_level.csv" \
    --rank-csv "$cfg/rank_metrics.csv" 2>&1 | tee -a "$cfg/run.log" | tee -a "$OUT/logs/$tag.log"
  # Never mark a configuration complete until output CSVs prove the requested
  # communicator size, all ranks, all source validations, and expected row count.
  validate_config "$cfg" "$ranks" "$REPETITIONS" "$dataset" "$ordering" "$mode" | tee -a "$OUT/logs/$tag.log"
  touch "$done"
  echo "[$(date -Is)] DONE $tag" | tee -a "$OUT/logs/$tag.log"
}

merge_config_csvs(){
  python3 - "$CONFIG_DIR" "$CHECKPOINT_DIR" "$OUT/csv" <<'PYMERGE'
import csv, pathlib, sys
src=pathlib.Path(sys.argv[1]); checkpoints=pathlib.Path(sys.argv[2]); dst=pathlib.Path(sys.argv[3]); dst.mkdir(parents=True, exist_ok=True)
completed={p.stem for p in checkpoints.glob('*.done')}
for name in ('summary.csv','per_level.csv','rank_metrics.csv'):
    files=sorted((src/tag/name) for tag in completed if (src/tag/name).is_file())
    if not files: raise SystemExit(f'No validated configuration CSVs found for {name}')
    out=dst/name
    with out.open('w', newline='', encoding='utf-8') as f_out:
        writer=None
        for path in files:
            with path.open(newline='', encoding='utf-8') as f_in:
                reader=csv.reader(f_in)
                try: header=next(reader)
                except StopIteration: raise SystemExit(f'Empty CSV: {path}')
                if writer is None: writer=csv.writer(f_out); writer.writerow(header)
                for row in reader: writer.writerow(row)
PYMERGE
}

if [[ "$RUN_SNAP" == 1 ]]; then
  "$ROOT/scripts/download_snap_graphs.sh"
  for ds in "soc-Epinions1:$ROOT/data/snap/soc-Epinions1.txt:1" "web-Google:$ROOT/data/snap/web-Google.txt:1" "roadNet-CA:$ROOT/data/snap/roadNet-CA.txt:0"; do
    IFS=: read -r name file directed <<< "$ds"
    for p in $RANKS; do for ord in original random; do for mode in blocking nonblocking; do
      run_one "$name" "$p" "$ord" "$mode" --input "$file" --directed "$directed"
    done; done; done
  done
fi
if [[ "$RUN_RMAT" == 1 ]]; then
  for scale in $SCALES; do for p in $RANKS; do for ord in original random; do for mode in blocking nonblocking; do
    run_one "RMAT_s${scale}" "$p" "$ord" "$mode" --scale "$scale" --edge-factor "$EDGE_FACTOR" --graph-seed 12345
  done; done; done; done
fi

# Check the full requested matrix before merging or making deliverables.
read -r -a rank_list <<< "$RANKS"
read -r -a scale_list <<< "$SCALES"
dataset_count=0
[[ "$RUN_SNAP" == 1 ]] && dataset_count=$((dataset_count + 3))
[[ "$RUN_RMAT" == 1 ]] && dataset_count=$((dataset_count + ${#scale_list[@]}))
expected_configs=$((dataset_count * ${#rank_list[@]} * 2 * 2))
done_count=$(find "$CHECKPOINT_DIR" -maxdepth 1 -name '*.done' -type f | wc -l)
if [[ "$dataset_count" -lt 1 || "$done_count" -ne "$expected_configs" ]]; then
  echo "Completion check failed: expected $expected_configs validated configs, found $done_count" >&2
  exit 1
fi
merge_config_csvs
{
  echo "MPIEXEC=$MPIEXEC"; echo "MPIEXEC_FLAGS=${MPIEXEC_FLAGS:-}"; echo "RANKS=$RANKS"; echo "REPETITIONS=$REPETITIONS"; echo "EDGE_FACTOR=$EDGE_FACTOR"; echo "SCALES=$SCALES";
  echo "RUNNER_VERSION=${RUNNER_VERSION:-unknown}"; echo "SOURCE_FINGERPRINT=${SOURCE_FINGERPRINT:-unknown}";
  echo "DATE=$(date -Is)"; echo "HOST=$(hostname)"; echo "KERNEL=$(uname -a)";
  echo "--- MPI launcher ---"; "$MPIEXEC" --version 2>&1 | head -5 || true;
  echo "--- compiler ---"; "${MPICXX:-mpicxx}" --version 2>&1 | head -2 || true;
  echo "--- CPU ---"; lscpu 2>/dev/null | grep -E 'Model name|CPU\\(s\\)|Thread|Core|Socket' || true;
  echo "--- memory ---"; free -h 2>/dev/null || true;
} > "$OUT/environment.txt"

python3 - "$OUT" "$expected_configs" "$REPETITIONS" "$dataset_count" <<'PYCOMPLETE'
import csv, json, pathlib, sys
out=pathlib.Path(sys.argv[1]); expected_configs=int(sys.argv[2]); reps=int(sys.argv[3]); dataset_count=int(sys.argv[4])
summary=out/'csv'/'summary.csv'
with summary.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
expected_rows=expected_configs*reps
if len(rows) != expected_rows: raise SystemExit(f'Expected {expected_rows} summary rows, found {len(rows)}')
if any(r.get('validation') != 'PASS' for r in rows): raise SystemExit('At least one BFS summary row is not validation=PASS')
configs={(r['dataset'],int(r['ranks']),r['ordering'],r['mode']) for r in rows}
if len(configs) != expected_configs: raise SystemExit(f'Expected {expected_configs} unique configs, found {len(configs)}')
if len({r['dataset'] for r in rows}) != dataset_count: raise SystemExit('Unexpected dataset count in summary.csv')
complete={'complete':True,'configurations':expected_configs,'bfs_summary_rows':expected_rows,'repetitions_per_configuration':reps,'datasets':sorted({r['dataset'] for r in rows}),'ranks':sorted({int(r['ranks']) for r in rows}),'orderings':['original','random'],'modes':['blocking','nonblocking'],'all_validations_pass':True,'runner_version':__import__('os').environ.get('RUNNER_VERSION','unknown'),'source_fingerprint':__import__('os').environ.get('SOURCE_FINGERPRINT','unknown')}
(out/'RUN_COMPLETE.json').write_text(json.dumps(complete,indent=2),encoding='utf-8')
print('RUN_COMPLETE:',json.dumps(complete))
PYCOMPLETE

python3 "$ROOT/scripts/analyze_results.py" --input-dir "$OUT/csv" --output-dir "$OUT/plots"
python3 "$ROOT/scripts/generate_report.py" --input-dir "$OUT/csv" --output "$OUT/report/Measured_Analysis_Report.md" --environment "$OUT/environment.txt"
python3 "$ROOT/scripts/generate_report_docx.py" --input-dir "$OUT/csv" --plots-dir "$OUT/plots" --output "$OUT/report/Two_Page_Report.docx" --environment "$OUT/environment.txt"
python3 "$ROOT/scripts/make_presentation.py" --results-dir "$OUT" --output "$OUT/presentation/Distributed_BFS_Results_Presentation.pptx"

echo "ALL EXPERIMENTS COMPLETE: $OUT"
