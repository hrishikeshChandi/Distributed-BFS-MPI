#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
p=argparse.ArgumentParser();p.add_argument('--results-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args();root=Path(a.results_dir);csv=root/'csv';plots=root/'plots'
prs=Presentation();prs.slide_width= Inches(13.333);prs.slide_height= Inches(7.5)
summary_path=csv/'summary.csv'
if not summary_path.is_file(): raise SystemExit(f'Missing measured summary CSV: {summary_path}')
measured=pd.read_csv(summary_path)
if measured.empty or not (measured.validation == 'PASS').all():
 raise SystemExit('summary.csv is empty or contains BFS rows that are not validation=PASS')
datasets=sorted(measured.dataset.astype(str).unique())
ranks_present=', '.join(str(int(x)) for x in sorted(measured.ranks.unique()))
source_counts=measured.groupby(['dataset','ranks','ordering','mode']).source_index.nunique()
source_counts_text=', '.join(str(int(x)) for x in sorted(set(source_counts.tolist())))
NAVY=RGBColor(18,35,61);BLUE=RGBColor(35,105,175);GRAY=RGBColor(85,98,115)
def slide(title, bullets=None, image=None, subtitle=None):
 s=prs.slides.add_slide(prs.slide_layouts[6]);bg=s.background.fill;bg.solid();bg.fore_color.rgb=RGBColor(247,249,252)
 sh=s.shapes.add_shape(1,0,0,prs.slide_width, Inches(.88));sh.fill.solid();sh.fill.fore_color.rgb=NAVY;sh.line.fill.background()
 tf=s.shapes.add_textbox(Inches(.55), Inches(.14), Inches(12.2), Inches(.55)).text_frame;tf.text=title;tf.paragraphs[0].font.size=Pt(25);tf.paragraphs[0].font.bold=True;tf.paragraphs[0].font.color.rgb=RGBColor(255,255,255)
 if subtitle:
  box=s.shapes.add_textbox(Inches(.7), Inches(1.1), Inches(12), Inches(.45));p0=box.text_frame.paragraphs[0];p0.text=subtitle;p0.font.size=Pt(15);p0.font.color.rgb=GRAY
 if bullets:
  box=s.shapes.add_textbox(Inches(.85), Inches(1.65 if subtitle else 1.35), Inches(11.7), Inches(5.3));tf=box.text_frame;tf.word_wrap=True
  for i,b in enumerate(bullets):
   q=tf.paragraphs[0] if i==0 else tf.add_paragraph();q.text=b;q.level=0;q.font.size=Pt(21);q.font.color.rgb=NAVY;q.space_after=Pt(16)
 if image and Path(image).exists():s.shapes.add_picture(str(image), Inches(.9), Inches(1.35), width=Inches(11.5), height=Inches(5.65))
 return s
slide('Distributed Breadth-First Search with MPI',['Multicore Architecture and Programming — Unit III','Team 10: Gaurav Mishra and Hrishikesh Chandi','1D vertex partitioning, collective communication and distributed graph traversal'],subtitle='Project presentation')
slide('Problem statement',['BFS explores a graph level by level.','In distributed memory, each MPI rank owns only a subset of vertices.','Frontier discoveries targeting another rank require communication.','Goal: measure the trade-off between local computation, communication and scaling.'])
slide('Why distributed BFS?',['Large graph traversals exceed the useful capacity of a single process.','The graph is partitioned by contiguous vertex-ID ranges.','Communication volume and load balance can dominate as rank count grows.','TEPS (traversed edges per second) provides a graph-traversal throughput metric.'])
slide('1D partitioning and data layout',['Each rank owns a contiguous vertex interval.','Only the owner stores the CSR adjacency rows for its vertices.','Outgoing edges are routed to source-vertex owners during graph construction.','SNAP edge lists and synthetic R-MAT inputs are converted to local CSR.'])
slide('Level-synchronous BFS algorithm',['Expand the current local frontier.','Create (vertex,parent) pairs for discoveries owned by other ranks.','Exchange counts and candidate pairs with MPI_Alltoallv.','Owners deduplicate candidates and set parent/level.','MPI_Allreduce sums the next-frontier size to detect termination.'])
slide('Blocking vs non-blocking communication',['Blocking variant: MPI_Alltoallv completes before local candidates are merged.','Non-blocking variant: MPI_Ialltoallv starts the exchange; local candidates are processed before MPI_Wait.','Non-blocking permits overlap; it does not guarantee asynchronous progress.','Compare end-to-end BFS elapsed time, not only request duration.'])
slide('Inputs and experiment matrix',[f'Datasets in this run: {", ".join(datasets)}',f'MPI ranks in this run: {ranks_present}',f'BFS sources per configuration: {source_counts_text}','Original IDs versus fixed-seed Feistel pseudorandom relabelling.','Colab experiments use multiple MPI processes on one VM, not multiple nodes.'])
slide('Correctness and validation',['Parent of every reached non-root vertex is a real predecessor.','Parent level must be exactly one less than child level.','Every edge from a reached vertex must lead to a reached vertex with distance at most one greater.','For graphs up to 2^21 vertices, compare all levels with sequential queue-based BFS.','Larger graphs use distributed structural validation to avoid root-memory blow-up.'])
slide('Performance metrics',['TEPS = traversed edges / timed BFS elapsed time.','Median TEPS across the recorded BFS source vertices.','Strong-scaling speedup and parallel efficiency relative to P=1.','Per-level expansion, packing, count exchange, local-candidate and received-candidate work, request lifetime and exposed wait.','Edge cut, edge-load imbalance, frontier imbalance and actual remote candidate-pair traffic.'])
# This generator is used only after a complete, validated run. Missing plots are errors,
# not a reason to produce a presentation containing placeholder result slides.
plot_patterns = {
 'TEPS scaling': 'teps_*.png',
 'per-level decomposition': 'per_level_*.png',
 'collective request': 'collective_request_*.png',
 'edge cut / imbalance': 'cut_imbalance_*.png',
 'remote traffic by rank': 'remote_pairs_by_rank_*.png',
}
selected_plots = {}
for label, pattern in plot_patterns.items():
 matches = sorted(plots.glob(pattern))
 if not matches or any(not f.is_file() or f.stat().st_size == 0 for f in matches):
  raise SystemExit(f'Missing or empty required plot family ({label}): {pattern}')
 selected_plots[label] = matches[0]
slide('Measured TEPS scaling',image=selected_plots['TEPS scaling'],subtitle=f"Validated BFS runs: {len(measured)} | datasets: {measured.dataset.nunique()}")
slide('Computation vs exposed communication by BFS level',image=selected_plots['per-level decomposition'])
slide('Payload collective and request lifetime',image=selected_plots['collective request'])
slide('Edge cut, imbalance and throughput',image=selected_plots['edge cut / imbalance'])
slide('Relabelling and communication volume',image=selected_plots['remote traffic by rank'])
slide('Measured results: discussion',['Use measured medians from summary_aggregated.csv.','Explain whether communication grows with rank count.','Compare original and shuffled mappings using edge cut, imbalance and remote pairs.','Report overlap gain only if non-blocking median elapsed time is lower.'])
slide('Conclusion and limitations',['The implementation tests how graph structure and vertex ordering affect communication.','MPI_Ialltoallv may or may not improve end-to-end time, depending on MPI progress and available local work.','Large-graph serial-reference validation is skipped above the configured threshold; structural validation remains active.','This is an educational 1D distributed BFS implementation, not full Graph500 compliance.'])
slide('References',['A. Buluç and K. Madduri, “Parallel Breadth-First Search on Distributed Memory Systems,” SC 2011.','MPI Forum, MPI Standard — collective communication and non-blocking collectives.','Stanford SNAP Large Network Dataset Collection.','Graph500 Benchmark Specification — TEPS definition.','R-MAT: Recursive MATrix graph model, Chakrabarti, Zhan and Faloutsos.'])
Path(a.output).parent.mkdir(parents=True,exist_ok=True);prs.save(a.output);print(f'Created {a.output} ({len(prs.slides)} slides)')
