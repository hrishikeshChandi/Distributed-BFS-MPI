#!/usr/bin/env python3
"""Generate a measured Markdown report from experiment CSVs."""
import argparse
from pathlib import Path
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--input-dir', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--environment', default='')
args = parser.parse_args()
source = Path(args.input_dir)
summary_all = pd.read_csv(source / 'summary.csv')
if summary_all.empty:
    raise SystemExit('summary.csv contains no BFS rows')
if not (summary_all.validation == 'PASS').all():
    raise SystemExit('summary.csv contains one or more BFS rows that are not validation=PASS')
summary = summary_all.copy()
aggregated = summary.groupby(
    ['dataset', 'ranks', 'ordering', 'mode'], as_index=False
).agg(
    median_teps=('teps', 'median'),
    median_elapsed_ms=('elapsed_ms', 'median'),
    sources=('source_index', 'nunique'),
    median_remote_pairs=('remote_pairs_sent', 'median'),
)

source_counts = summary.groupby(['dataset', 'ranks', 'ordering', 'mode'])['source_index'].nunique()
source_count_values = sorted(set(int(x) for x in source_counts.tolist()))
source_count_text = ', '.join(str(x) for x in source_count_values)
rank_values = ', '.join(str(int(x)) for x in sorted(summary.ranks.unique()))
lines = [
    '# Distributed BFS with MPI — Measured Results',
    '',
    '**Team 10:** Gaurav Mishra and Hrishikesh Chandi',
    '',
    f"Validated BFS runs: **{len(summary)}** across **{summary.dataset.nunique()}** datasets.",
    '',
    '## Median TEPS by dataset and configuration',
    '',
    aggregated.to_markdown(index=False),
    '',
    '## Interpretation guidance',
    '',
    '- TEPS is computed from traversed directed arcs (or undirected edges for undirected inputs) divided by measured BFS elapsed time.',
    f'- Observed BFS source count per configuration: {source_count_text}; the table reports median TEPS across the recorded source runs.',
    f'- MPI process counts present in this run: {rank_values}. These are single-node MPI ranks when executed on Colab.',
    '- Compare blocking and non-blocking only within the same dataset, rank count and vertex ordering. Non-blocking collectives permit overlap but do not guarantee progress or a speedup.',
    '- The timed BFS retains the required global next-frontier termination reduction. Per-level diagnostic reductions are aggregated after the timer stops; graph construction and correctness validation are also outside the timed region.',
    '- Per-level computation is expansion + local-candidate processing + received-candidate merging. Exposed communication is packing + count exchange + blocking payload collective, or packing + count exchange + residual wait for non-blocking mode. The non-blocking request lifetime includes overlapped local work and is therefore shown separately.',
    '- Edge cut and edge-load imbalance are compared for both original and fixed-seed Feistel-relabeled vertex orderings. Remote candidate-pair traffic is shown at each rank count rather than pooled across rank counts.',
    '- For graphs up to 2^21 vertices, levels are additionally compared with a sequential queue-based BFS reference; larger graphs retain distributed structural validation.',
    '',
    '## Reproducibility',
    '',
    'The raw per-source/per-level CSV files, rank metrics, logs, environment record and plotting scripts accompany this report. No unmeasured values are inserted.',
]
if args.environment and Path(args.environment).exists():
    lines += ['', '## Environment', '', '```text', Path(args.environment).read_text().strip(), '```']
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text('\n'.join(lines))
print(output)
