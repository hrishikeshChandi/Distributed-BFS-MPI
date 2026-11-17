#!/usr/bin/env python3
"""Aggregate Distributed BFS runs and produce scaling/communication plots."""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--input-dir', required=True)
parser.add_argument('--output-dir', required=True)
args = parser.parse_args()
source = Path(args.input_dir)
out = Path(args.output_dir)
out.mkdir(parents=True, exist_ok=True)

summary_path = source / 'summary.csv'
level_path = source / 'per_level.csv'
rank_path = source / 'rank_metrics.csv'
for path in (summary_path, level_path, rank_path):
    if not path.exists():
        raise SystemExit(f'Missing required input: {path}')

summary = pd.read_csv(summary_path)
levels = pd.read_csv(level_path)
ranks = pd.read_csv(rank_path)
required_level = {
    'dataset', 'ranks', 'ordering', 'mode', 'level', 'expansion_ms',
    'packing_ms', 'count_exchange_ms', 'collective_request_ms',
    'local_candidate_ms', 'residual_wait_ms', 'received_merge_ms',
    'level_wall_ms', 'remote_pairs_sent', 'frontier_imbalance',
}
missing = sorted(required_level - set(levels.columns))
if missing:
    raise SystemExit(
        'per_level.csv uses an old/incomplete schema. Missing columns: '
        + ', '.join(missing)
        + '. Regenerate the CSVs using the corrected distributed_bfs.cpp.'
    )

summary = summary[summary.validation == 'PASS'].copy()
if summary.empty:
    raise SystemExit('No validation=PASS rows found in summary.csv')
summary['ranks'] = summary.ranks.astype(int)
levels['ranks'] = levels.ranks.astype(int)
ranks['ranks'] = ranks.ranks.astype(int)

# Median across the independent BFS source runs for each fixed configuration.
agg = summary.groupby(
    ['dataset', 'ordering', 'mode', 'ranks'], as_index=False
).agg(
    median_teps=('teps', 'median'),
    median_elapsed_ms=('elapsed_ms', 'median'),
    median_remote_pairs=('remote_pairs_sent', 'median'),
    median_reachable=('reachable_vertices', 'median'),
    sources=('source_index', 'nunique'),
)
agg['speedup'] = float('nan')
agg['efficiency'] = float('nan')
for (_, _, _), group in agg.groupby(['dataset', 'ordering', 'mode']):
    baseline = group.loc[group.ranks == 1, 'median_elapsed_ms']
    if not baseline.empty and float(baseline.iloc[0]) > 0:
        base = float(baseline.iloc[0])
        agg.loc[group.index, 'speedup'] = base / agg.loc[group.index, 'median_elapsed_ms']
        agg.loc[group.index, 'efficiency'] = (
            agg.loc[group.index, 'speedup'] / agg.loc[group.index, 'ranks'] * 100
        )
agg.to_csv(out / 'summary_aggregated.csv', index=False)

# End-to-end TEPS and strong-scaling results.
for dataset, group in agg.groupby('dataset'):
    fig, ax = plt.subplots(figsize=(8, 5))
    for (ordering, mode), config in group.groupby(['ordering', 'mode']):
        config = config.sort_values('ranks')
        ax.plot(config.ranks, config.median_teps, marker='o',
                label=f'{ordering}/{mode}')
    ax.set(title=f'TEPS scaling — {dataset}', xlabel='MPI ranks', ylabel='Median TEPS')
    ax.set_xticks(sorted(group.ranks.unique()))
    ax.grid(True, alpha=.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / f'teps_{dataset}.png', dpi=170)
    plt.close(fig)

# Convert raw phase measurements into meaningful, non-double-counted views.
levels = levels.copy()
levels['computation_ms'] = (
    levels.expansion_ms + levels.local_candidate_ms + levels.received_merge_ms
)
# Packing and count exchange are exposed setup/communication costs in both modes.
levels['communication_setup_ms'] = levels.packing_ms + levels.count_exchange_ms
# The non-blocking request lifetime overlaps local-candidate computation. For an
# additive phase view, count only the wait that remains exposed after local work.
levels['payload_exposed_ms'] = levels.collective_request_ms.where(
    levels['mode'] == 'blocking', levels.residual_wait_ms
)
levels['exposed_communication_ms'] = (
    levels.communication_setup_ms + levels.payload_exposed_ms
)
levels.to_csv(out / 'per_level_derived.csv', index=False)

for dataset, group in levels.groupby('dataset'):
    max_ranks = int(group.ranks.max())
    group = group[group.ranks == max_ranks]
    fig, ax = plt.subplots(figsize=(11, 5.8))
    configs = list(group.groupby(['ordering', 'mode']))
    width = min(.18, .68 / max(len(configs), 1))
    for index, ((ordering, mode), config) in enumerate(configs):
        median = config.groupby('level')[
            ['computation_ms', 'exposed_communication_ms', 'level_wall_ms']
        ].median().reset_index()
        offset = (index - (len(configs) - 1) / 2) * width
        x = median.level.to_numpy() + offset
        ax.bar(x, median.computation_ms, width=width,
               label=f'{ordering}/{mode} computation')
        ax.bar(x, median.exposed_communication_ms, width=width,
               bottom=median.computation_ms,
               label=f'{ordering}/{mode} exposed communication')
        ax.plot(x, median.level_wall_ms, marker='.', linewidth=1.1,
                label=f'{ordering}/{mode} level wall')
    ax.set(
        title=f'Per-level computation and exposed communication — {dataset}, P={max_ranks}',
        xlabel='BFS level (bars offset by configuration)', ylabel='Median time (ms)',
    )
    ax.grid(axis='y', alpha=.25)
    ax.legend(fontsize=7, ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.17))
    fig.tight_layout()
    fig.savefig(out / f'per_level_{dataset}.png', dpi=170)
    plt.close(fig)

    # The request lifetime is deliberately shown separately: in non-blocking
    # mode it includes time overlapping with local-candidate computation.
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for (ordering, mode), config in group.groupby(['ordering', 'mode']):
        med = config.groupby('level').collective_request_ms.median().reset_index()
        ax.plot(med.level, med.collective_request_ms, marker='o',
                label=f'{ordering}/{mode}')
    ax.set(
        title=f'Payload collective / request lifetime — {dataset}, P={max_ranks}',
        xlabel='BFS level', ylabel='Median duration (ms)',
    )
    ax.grid(True, alpha=.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / f'collective_request_{dataset}.png', dpi=170)
    plt.close(fig)

# Static edge-cut and edge-load metrics are compared for BOTH vertex orderings.
rank_static = ranks.groupby(['dataset', 'ordering', 'ranks']).agg(
    max_edges=('local_adjacency_entries', 'max'),
    min_edges=('local_adjacency_entries', 'min'),
    total_cut=('local_cut_edges', 'sum'),
    total_adj=('local_adjacency_entries', 'sum'),
).reset_index()
rank_static['edge_load_imbalance'] = (
    rank_static.max_edges / rank_static.min_edges.clip(lower=1)
)
rank_static['cut_fraction'] = rank_static.total_cut / rank_static.total_adj.clip(lower=1)

for dataset, group in agg.groupby('dataset'):
    blocking = group[group['mode'] == 'blocking']
    compare = blocking.merge(
        rank_static, on=['dataset', 'ordering', 'ranks'], how='left', validate='one_to_one'
    )
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    markers = {'original': 'o', 'random': '^'}
    scatter = None
    for ordering, config in compare.groupby('ordering'):
        scatter = ax.scatter(
            config.cut_fraction, config.median_teps,
            c=config.edge_load_imbalance, s=55 + config.ranks * 8,
            marker=markers.get(ordering, 's'), label=ordering,
        )
        for _, row in config.iterrows():
            ax.annotate(f"{ordering[:1].upper()} P={int(row.ranks)}",
                        (row.cut_fraction, row.median_teps), fontsize=7)
    ax.set(
        title=f'Edge cut and edge-load imbalance vs TEPS — {dataset}',
        xlabel='Directed cut fraction (rank-local CSR arcs)', ylabel='Median TEPS',
    )
    ax.grid(True, alpha=.3)
    ax.legend(title='Vertex ordering')
    if scatter is not None:
        fig.colorbar(scatter, ax=ax, label='Static edge-load max/min')
    fig.tight_layout()
    fig.savefig(out / f'cut_imbalance_{dataset}.png', dpi=170)
    plt.close(fig)

    # Preserve rank-count resolution instead of collapsing all P values into
    # one median per ordering. Traffic is shown for each matching rank count.
    traffic = blocking.groupby(['ordering', 'ranks']).median_remote_pairs.median().reset_index()
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for ordering, config in traffic.groupby('ordering'):
        config = config.sort_values('ranks')
        ax.plot(config.ranks, config.median_remote_pairs, marker='o', label=ordering)
    ax.set(
        title=f'Remote candidate traffic by rank count — {dataset}',
        xlabel='MPI ranks', ylabel='Median remote candidate pairs per BFS',
    )
    ax.set_xticks(sorted(blocking.ranks.unique()))
    ax.grid(True, alpha=.3)
    ax.legend(title='Vertex ordering')
    fig.tight_layout()
    fig.savefig(out / f'remote_pairs_by_rank_{dataset}.png', dpi=170)
    plt.close(fig)

print(
    f'Analyzed {len(summary)} validated BFS runs across '
    f'{summary.dataset.nunique()} datasets. Aggregates and plots: {out}'
)
