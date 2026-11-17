#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt

p=argparse.ArgumentParser();p.add_argument('--input-dir',required=True);p.add_argument('--plots-dir',required=True);p.add_argument('--output',required=True);p.add_argument('--environment',default='');a=p.parse_args()
s=pd.read_csv(Path(a.input_dir)/'summary.csv')
if s.empty or not (s.validation == 'PASS').all(): raise SystemExit('summary.csv is empty or contains failed BFS validations')
source_counts=s.groupby(['dataset','ranks','ordering','mode'])['source_index'].nunique()
source_values=sorted(set(int(x) for x in source_counts.tolist()))
source_text=', '.join(str(x) for x in source_values)
rank_text=', '.join(str(int(x)) for x in sorted(s.ranks.unique()))
datasets=sorted(s.dataset.unique())
agg=s.groupby(['dataset','ranks','ordering','mode']).agg(TEPS=('teps','median'),Time_ms=('elapsed_ms','median'),Sources=('source_index','nunique')).reset_index()
# One compact best-observed configuration per graph keeps this report section to two pages.
best=agg.loc[agg.groupby('dataset').TEPS.idxmax()].sort_values('dataset')
d=Document();sec=d.sections[0];sec.top_margin=Inches(.42);sec.bottom_margin=Inches(.42);sec.left_margin=Inches(.52);sec.right_margin=Inches(.52)
d.styles['Normal'].font.size=Pt(8)
d.add_heading('Distributed Breadth-First Search with MPI',0)
d.add_paragraph('Two-page project report section | Multicore Architecture and Programming — Unit III')
d.add_paragraph('Team 10: Gaurav Mishra and Hrishikesh Chandi')
d.add_heading('Problem and method',1)
d.add_paragraph('Breadth-first search (BFS) explores a graph level by level. In distributed memory, each MPI rank owns a contiguous vertex range; a frontier edge reaching a vertex owned by another rank requires communication. This project implements 1D distributed BFS with local CSR storage, remote (vertex,parent) candidate exchange through MPI_Alltoallv, and global termination through MPI_Allreduce.')
d.add_paragraph('Two communication variants are compared. The blocking version completes MPI_Alltoallv before processing local/remote candidates. The non-blocking version initiates MPI_Ialltoallv, processes locally owned candidates while the request is outstanding, waits for completion and then merges received candidates. Original vertex IDs are compared with a deterministic eight-round Feistel pseudorandom bijection (cycle-walked over the vertex domain) that preserves graph topology.')
d.add_heading('Experimental inputs and metrics',1)
d.add_paragraph(f"Observed datasets: {', '.join(datasets)}. MPI ranks present: {rank_text}. BFS source count per configuration: {source_text}. The run compares original and Feistel-relabeled vertex IDs with blocking MPI_Alltoallv and non-blocking MPI_Ialltoallv. TEPS is traversed edges per second; the reported central statistic is median TEPS across the recorded source vertices. Additional metrics include per-level computation and exposed communication phases, payload-request lifetime, edge cut, static edge-load imbalance, frontier imbalance and actual remote candidate-pair traffic.")
d.add_heading('Best measured configuration per dataset',1)
t=d.add_table(rows=1,cols=5);t.style='Light Shading Accent 1'
for c,v in zip(t.rows[0].cells,['Dataset','Ranks','Ordering','Mode','Median TEPS']):c.text=v
for _,r in best.iterrows():
 cells=t.add_row().cells
 for c,v in zip(cells,[str(r['dataset']),str(int(r['ranks'])),str(r['ordering']),str(r['mode']),f"{r['TEPS']:,.0f}"]):c.text=v
# Page 2

d.add_page_break();d.add_heading('Performance analysis and interpretation',0)
d.add_paragraph(f"The run bundle contains {len(s)} validated source/configuration runs over {s.dataset.nunique()} graph datasets. Use the plots below and the raw CSV files to compare rank scaling and per-level communication. A non-blocking variant should only be described as beneficial if its end-to-end median elapsed time is lower for the same graph, source, rank count and ordering.")
for pattern in ['teps_*.png','per_level_*.png']:
 matches=list(Path(a.plots_dir).glob(pattern))
 if matches:
  d.add_picture(str(matches[0]),width=Inches(3.2))
d.add_heading('Correctness, findings and limitations',1)
d.add_paragraph('Every BFS run checks root state, parent-level consistency, existence of parent edges and BFS closure. For graphs up to 2^21 vertices, distributed levels are additionally compared with a sequential queue-based BFS reference. Larger graphs retain distributed structural validation; a full serial reference is skipped to avoid gathering a very large graph on rank 0.')
d.add_paragraph('The timed BFS retains the required global termination reduction; per-level diagnostic reductions are aggregated after the timer stops. Computation includes expansion, local-candidate processing and received-candidate merging. Exposed communication includes packing, count exchange and the blocking payload collective or non-blocking residual wait. The non-blocking request lifetime includes overlapped local work and is shown separately. MPI_Ialltoallv permits overlap but does not guarantee background progress. This is an educational 1D MPI BFS implementation, not a claim of full Graph500 compliance.')
if a.environment and Path(a.environment).exists():
 d.add_heading('Environment',2);d.add_paragraph(Path(a.environment).read_text()[:700])
Path(a.output).parent.mkdir(parents=True,exist_ok=True);d.save(a.output);print(a.output)
