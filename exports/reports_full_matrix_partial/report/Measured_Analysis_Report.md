# Distributed BFS with MPI — Measured Results

**Team 10:** Gaurav Mishra and Hrishikesh Chandi

Validated BFS runs: **3744** across **12** datasets.

## Median TEPS by dataset and configuration

| dataset       |   ranks | ordering   | mode        |   median_teps |   median_elapsed_ms |   sources |   median_remote_pairs |
|:--------------|--------:|:-----------|:------------|--------------:|--------------------:|----------:|----------------------:|
| RMAT_s16      |       1 | original   | blocking    |   1.74803e+07 |           5.17713   |        16 |           0           |
| RMAT_s16      |       1 | original   | nonblocking |   1.44724e+07 |           5.4505    |        16 |           0           |
| RMAT_s16      |       1 | random     | blocking    |   1.32842e+07 |           5.92643   |        16 |           0           |
| RMAT_s16      |       1 | random     | nonblocking |   1.1066e+07  |           6.17221   |        16 |           0           |
| RMAT_s16      |       2 | original   | blocking    |   5.58565e+06 |          16.6943    |        16 |      188023           |
| RMAT_s16      |       2 | original   | nonblocking |   6.1968e+06  |          10.2958    |        16 |      188023           |
| RMAT_s16      |       2 | random     | blocking    |   3.91702e+06 |          13.7991    |        16 |      239054           |
| RMAT_s16      |       2 | random     | nonblocking |   7.9292e+06  |          14.4585    |        16 |      239054           |
| RMAT_s16      |       4 | original   | blocking    |   5.8321e+06  |          15.6192    |        16 |      302153           |
| RMAT_s16      |       4 | original   | nonblocking |   4.34674e+06 |          22.1373    |        16 |      302153           |
| RMAT_s16      |       4 | random     | blocking    |   2.94728e+06 |          17.4612    |        16 |      358205           |
| RMAT_s16      |       4 | random     | nonblocking |   5.9159e+06  |          15.8589    |        16 |      358205           |
| RMAT_s16      |       8 | original   | blocking    |   3.89624e+06 |          19.5101    |        16 |      372017           |
| RMAT_s16      |       8 | original   | nonblocking |   4.18686e+06 |          18.661     |        16 |      372017           |
| RMAT_s16      |       8 | random     | blocking    |   2.57224e+06 |          29.9287    |        16 |      418057           |
| RMAT_s16      |       8 | random     | nonblocking |   3.22426e+06 |          18.915     |        16 |      418057           |
| RMAT_s16      |      16 | original   | blocking    |   3.38573e+06 |          25.0252    |        16 |      414474           |
| RMAT_s16      |      16 | original   | nonblocking |   3.01654e+06 |          22.0671    |        16 |      414474           |
| RMAT_s16      |      16 | random     | blocking    |   2.70666e+06 |          33.8094    |        16 |      447761           |
| RMAT_s16      |      16 | random     | nonblocking |   2.34202e+06 |          25.0173    |        16 |      447761           |
| RMAT_s17      |       1 | original   | blocking    |   0           |           0.0164605 |        16 |           0           |
| RMAT_s17      |       1 | original   | nonblocking |   0           |           0.025602  |        16 |           0           |
| RMAT_s17      |       1 | random     | blocking    |   0           |           0.0123625 |        16 |           0           |
| RMAT_s17      |       1 | random     | nonblocking |   0           |           0.0208945 |        16 |           0           |
| RMAT_s17      |       2 | original   | blocking    |   0           |           0.706915  |        16 |           0           |
| RMAT_s17      |       2 | original   | nonblocking |   0           |           0.872436  |        16 |           0           |
| RMAT_s17      |       2 | random     | blocking    |   0           |           2.52578   |        16 |           0           |
| RMAT_s17      |       2 | random     | nonblocking |   0           |           0.381541  |        16 |           0           |
| RMAT_s17      |       4 | original   | blocking    |   0           |           2.0446    |        16 |           0           |
| RMAT_s17      |       4 | original   | nonblocking |   0           |           1.67732   |        16 |           0           |
| RMAT_s17      |       4 | random     | blocking    |   0           |           2.36206   |        16 |           0           |
| RMAT_s17      |       4 | random     | nonblocking |   0           |           2.86619   |        16 |           0           |
| RMAT_s17      |       8 | original   | blocking    |   0           |           2.14489   |        16 |           0           |
| RMAT_s17      |       8 | original   | nonblocking |   0           |           2.4066    |        16 |           0           |
| RMAT_s17      |       8 | random     | blocking    |   0           |           5.85243   |        16 |           0           |
| RMAT_s17      |       8 | random     | nonblocking |   0           |           1.89272   |        16 |           0           |
| RMAT_s17      |      16 | original   | blocking    |   0           |           2.53784   |        16 |           0           |
| RMAT_s17      |      16 | original   | nonblocking |   0           |           5.23577   |        16 |           0           |
| RMAT_s17      |      16 | random     | blocking    |   0           |           5.3616    |        16 |           0           |
| RMAT_s17      |      16 | random     | nonblocking |   0           |           2.44902   |        16 |           0           |
| RMAT_s18      |       1 | original   | blocking    |   0           |           0.0127815 |        16 |           0           |
| RMAT_s18      |       1 | original   | nonblocking |   0           |           0.0229775 |        16 |           0           |
| RMAT_s18      |       1 | random     | blocking    |   0           |           0.012937  |        16 |           0           |
| RMAT_s18      |       1 | random     | nonblocking |   0           |           0.0189165 |        16 |           0           |
| RMAT_s18      |       2 | original   | blocking    |   0           |           1.57225   |        16 |           0           |
| RMAT_s18      |       2 | original   | nonblocking |   0           |           0.416658  |        16 |           0           |
| RMAT_s18      |       2 | random     | blocking    |   0           |           0.565749  |        16 |           0           |
| RMAT_s18      |       2 | random     | nonblocking |   0           |           0.291303  |        16 |           0           |
| RMAT_s18      |       4 | original   | blocking    |   0           |           2.20563   |        16 |           0           |
| RMAT_s18      |       4 | original   | nonblocking |   0           |           1.5113    |        16 |           0           |
| RMAT_s18      |       4 | random     | blocking    |   0           |           1.23283   |        16 |           0           |
| RMAT_s18      |       4 | random     | nonblocking |   0           |           1.8493    |        16 |           0           |
| RMAT_s18      |       8 | original   | blocking    |   0           |           4.06187   |        16 |           0           |
| RMAT_s18      |       8 | original   | nonblocking |   0           |           2.09934   |        16 |           0           |
| RMAT_s18      |       8 | random     | blocking    |   0           |           2.51169   |        16 |           0           |
| RMAT_s18      |       8 | random     | nonblocking |   0           |           1.60155   |        16 |           0           |
| RMAT_s18      |      16 | original   | blocking    |   0           |           3.6852    |        16 |           0           |
| RMAT_s18      |      16 | original   | nonblocking |   0           |           2.92392   |        16 |           0           |
| RMAT_s18      |      16 | random     | blocking    |   0           |           8.90928   |        16 |           0           |
| RMAT_s18      |      16 | random     | nonblocking |   0           |           2.39857   |        16 |           0           |
| RMAT_s19      |       1 | original   | blocking    |   0           |           0.0154995 |        16 |           0           |
| RMAT_s19      |       1 | original   | nonblocking |   0           |           0.0234145 |        16 |           0           |
| RMAT_s19      |       1 | random     | blocking    |   0           |           0.015369  |        16 |           0           |
| RMAT_s19      |       1 | random     | nonblocking |   0           |           0.0212365 |        16 |           0           |
| RMAT_s19      |       2 | original   | blocking    |   0           |           1.00175   |        16 |           0           |
| RMAT_s19      |       2 | original   | nonblocking |   0           |           0.874787  |        16 |           0           |
| RMAT_s19      |       2 | random     | blocking    |   0           |           0.585884  |        16 |           0           |
| RMAT_s19      |       2 | random     | nonblocking |   0           |           0.422358  |        16 |           0           |
| RMAT_s19      |       4 | original   | blocking    |   0           |           2.54694   |        16 |           0           |
| RMAT_s19      |       4 | original   | nonblocking |   0           |           1.5894    |        16 |           0           |
| RMAT_s19      |       4 | random     | blocking    |   0           |           1.81997   |        16 |           0           |
| RMAT_s19      |       4 | random     | nonblocking |   0           |           2.55733   |        16 |           0           |
| RMAT_s19      |       8 | original   | blocking    |   0           |           2.90419   |        16 |           0           |
| RMAT_s19      |       8 | original   | nonblocking |   0           |           3.2935    |        16 |           0           |
| RMAT_s19      |       8 | random     | blocking    |   0           |           2.90864   |        16 |           0           |
| RMAT_s19      |       8 | random     | nonblocking |   0           |           2.70415   |        16 |           0           |
| RMAT_s19      |      16 | original   | blocking    |   0           |           3.22788   |        16 |           0           |
| RMAT_s19      |      16 | original   | nonblocking |   0           |           3.82441   |        16 |           0           |
| RMAT_s19      |      16 | random     | blocking    |   0           |           5.31732   |        16 |           0           |
| RMAT_s19      |      16 | random     | nonblocking |   0           |           3.91578   |        16 |           0           |
| RMAT_s20      |       1 | original   | blocking    |   0           |           0.013602  |        16 |           0           |
| RMAT_s20      |       1 | original   | nonblocking |   0           |           0.0250415 |        16 |           0           |
| RMAT_s20      |       1 | random     | blocking    |   0           |           0.0124205 |        16 |           0           |
| RMAT_s20      |       1 | random     | nonblocking |   0           |           0.022932  |        16 |           0           |
| RMAT_s20      |       2 | original   | blocking    |   0           |           0.895398  |        16 |           0           |
| RMAT_s20      |       2 | original   | nonblocking |   0           |           0.749602  |        16 |           0           |
| RMAT_s20      |       2 | random     | blocking    |   0           |           1.06456   |        16 |           0           |
| RMAT_s20      |       2 | random     | nonblocking |   0           |           0.721715  |        16 |           0           |
| RMAT_s20      |       4 | original   | blocking    |   0           |           1.60776   |        16 |           0           |
| RMAT_s20      |       4 | original   | nonblocking |   0           |           1.46473   |        16 |           0           |
| RMAT_s20      |       4 | random     | blocking    |   0           |           2.33213   |        16 |           0           |
| RMAT_s20      |       4 | random     | nonblocking |   0           |           1.61601   |        16 |           0           |
| RMAT_s20      |       8 | original   | blocking    |   0           |           2.48846   |        16 |           0           |
| RMAT_s20      |       8 | original   | nonblocking |   0           |           2.28778   |        16 |           0           |
| RMAT_s20      |       8 | random     | blocking    |   0           |           2.09107   |        16 |           0           |
| RMAT_s20      |       8 | random     | nonblocking |   0           |           2.1866    |        16 |           0           |
| RMAT_s20      |      16 | original   | blocking    |   0           |           2.79232   |        16 |           0           |
| RMAT_s20      |      16 | original   | nonblocking |   0           |           3.77003   |        16 |           0           |
| RMAT_s20      |      16 | random     | blocking    |   0           |           3.55795   |        16 |           0           |
| RMAT_s20      |      16 | random     | nonblocking |   0           |           5.62346   |        16 |           0           |
| RMAT_s21      |       1 | original   | blocking    |   0           |           0.017462  |        16 |           0           |
| RMAT_s21      |       1 | original   | nonblocking |   0           |           0.0234865 |        16 |           0           |
| RMAT_s21      |       1 | random     | blocking    |   0           |           0.013518  |        16 |           0           |
| RMAT_s21      |       1 | random     | nonblocking |   0           |           0.0222905 |        16 |           0           |
| RMAT_s21      |       2 | original   | blocking    |   0           |           0.365019  |        16 |           0           |
| RMAT_s21      |       2 | original   | nonblocking |   0           |           1.11065   |        16 |           0           |
| RMAT_s21      |       2 | random     | blocking    |   0           |           0.24831   |        16 |           0           |
| RMAT_s21      |       2 | random     | nonblocking |   0           |           1.89122   |        16 |           0           |
| RMAT_s21      |       4 | original   | blocking    |   0           |           2.28666   |        16 |           0           |
| RMAT_s21      |       4 | original   | nonblocking |   0           |           1.34278   |        16 |           0           |
| RMAT_s21      |       4 | random     | blocking    |   0           |           2.10956   |        16 |           0           |
| RMAT_s21      |       4 | random     | nonblocking |   0           |           2.30597   |        16 |           0           |
| RMAT_s21      |       8 | original   | blocking    |   0           |           1.93899   |        16 |           0           |
| RMAT_s21      |       8 | original   | nonblocking |   0           |           3.42591   |        16 |           0           |
| RMAT_s21      |       8 | random     | blocking    |   0           |           2.40718   |        16 |           0           |
| RMAT_s21      |       8 | random     | nonblocking |   0           |           2.07322   |        16 |           0           |
| RMAT_s21      |      16 | original   | blocking    |   0           |           6.39605   |        16 |           0           |
| RMAT_s21      |      16 | original   | nonblocking |   0           |           3.30122   |        16 |           0           |
| RMAT_s21      |      16 | random     | blocking    |   0           |           3.45458   |        16 |           0           |
| RMAT_s21      |      16 | random     | nonblocking |   0           |           4.27051   |        16 |           0           |
| RMAT_s22      |       1 | original   | blocking    |   0           |           0.012513  |        16 |           0           |
| RMAT_s22      |       1 | original   | nonblocking |   0           |           0.020971  |        16 |           0           |
| RMAT_s22      |       1 | random     | blocking    |   0           |           0.0135035 |        16 |           0           |
| RMAT_s22      |       1 | random     | nonblocking |   0           |           0.0207645 |        16 |           0           |
| RMAT_s22      |       2 | original   | blocking    |   0           |           0.0450585 |        16 |           0           |
| RMAT_s22      |       2 | original   | nonblocking |   0           |           0.079513  |        16 |           0           |
| RMAT_s22      |       2 | random     | blocking    |   0           |           0.066977  |        16 |           0           |
| RMAT_s22      |       2 | random     | nonblocking |   0           |           0.037137  |        16 |           0           |
| RMAT_s22      |       4 | original   | blocking    |   0           |           0.885536  |        16 |           0           |
| RMAT_s22      |       4 | original   | nonblocking |   0           |           1.04848   |        16 |           0           |
| RMAT_s22      |       4 | random     | blocking    |   0           |           1.48381   |        16 |           0           |
| RMAT_s22      |       4 | random     | nonblocking |   0           |           0.861735  |        16 |           0           |
| RMAT_s22      |       8 | original   | blocking    |   0           |           2.03363   |        16 |           0           |
| RMAT_s22      |       8 | original   | nonblocking |   0           |           2.80085   |        16 |           0           |
| RMAT_s22      |       8 | random     | blocking    |   0           |           2.3932    |        16 |           0           |
| RMAT_s22      |       8 | random     | nonblocking |   0           |           2.28613   |        16 |           0           |
| RMAT_s22      |      16 | original   | blocking    |   0           |           5.32015   |        16 |           0           |
| RMAT_s22      |      16 | original   | nonblocking |   0           |           3.82317   |        16 |           0           |
| RMAT_s22      |      16 | random     | blocking    |   0           |           3.42217   |        16 |           0           |
| RMAT_s22      |      16 | random     | nonblocking |   0           |           2.95847   |        16 |           0           |
| RMAT_s23      |       1 | original   | blocking    |   0           |           0.0117105 |        16 |           0           |
| RMAT_s23      |       1 | original   | nonblocking |   0           |           0.018031  |        16 |           0           |
| RMAT_s23      |       1 | random     | blocking    |   0           |           0.0130415 |        16 |           0           |
| RMAT_s23      |       1 | random     | nonblocking |   0           |           0.0187015 |        16 |           0           |
| RMAT_s23      |       2 | original   | blocking    |   0           |           0.038409  |        16 |           0           |
| RMAT_s23      |       2 | original   | nonblocking |   0           |           0.0356795 |        16 |           0           |
| RMAT_s23      |       2 | random     | blocking    |   0           |           0.071985  |        16 |           0           |
| RMAT_s23      |       2 | random     | nonblocking |   0           |           0.0398265 |        16 |           0           |
| RMAT_s23      |       4 | original   | blocking    |   0           |           0.408679  |        16 |           0           |
| RMAT_s23      |       4 | original   | nonblocking |   0           |           0.114723  |        16 |           0           |
| RMAT_s23      |       4 | random     | blocking    |   0           |           0.13707   |        16 |           0           |
| RMAT_s23      |       4 | random     | nonblocking |   0           |           0.229411  |        16 |           0           |
| RMAT_s23      |       8 | original   | blocking    |   0           |           1.48007   |        16 |           0           |
| RMAT_s23      |       8 | original   | nonblocking |   0           |           1.68193   |        16 |           0           |
| RMAT_s23      |       8 | random     | blocking    |   0           |           1.65249   |        16 |           0           |
| RMAT_s23      |       8 | random     | nonblocking |   0           |           1.73977   |        16 |           0           |
| RMAT_s23      |      16 | original   | blocking    |   0           |           3.56975   |        16 |           0           |
| RMAT_s23      |      16 | original   | nonblocking |   0           |           3.66282   |        16 |           0           |
| RMAT_s23      |      16 | random     | blocking    |   0           |           2.84764   |        16 |           0           |
| RMAT_s23      |      16 | random     | nonblocking |   0           |           3.01938   |        16 |           0           |
| RMAT_s24      |       1 | original   | blocking    |   0           |           0.012953  |        16 |           0           |
| RMAT_s24      |       1 | original   | nonblocking |   0           |           0.019944  |        16 |           0           |
| RMAT_s24      |       1 | random     | blocking    |   0           |           0.0127695 |        16 |           0           |
| RMAT_s24      |       1 | random     | nonblocking |   0           |           0.0202575 |        16 |           0           |
| RMAT_s24      |       2 | original   | blocking    |   0           |           0.0306925 |        16 |           0           |
| RMAT_s24      |       2 | original   | nonblocking |   0           |           0.0365455 |        16 |           0           |
| RMAT_s24      |       2 | random     | blocking    |   0           |           0.031818  |        16 |           0           |
| RMAT_s24      |       2 | random     | nonblocking |   0           |           0.045518  |        16 |           0           |
| RMAT_s24      |       4 | original   | blocking    |   0           |           0.0953045 |        16 |           0           |
| RMAT_s24      |       4 | original   | nonblocking |   0           |           0.110819  |        16 |           0           |
| RMAT_s24      |       4 | random     | blocking    |   0           |           0.0813875 |        16 |           0           |
| RMAT_s24      |       4 | random     | nonblocking |   0           |           0.149427  |        16 |           0           |
| RMAT_s24      |       8 | original   | blocking    |   0           |           0.326854  |        16 |           0           |
| RMAT_s24      |       8 | original   | nonblocking |   0           |           0.764263  |        16 |           0           |
| roadNet-CA    |       1 | original   | blocking    |   1.41137e+07 |         195.583     |        16 |           0           |
| roadNet-CA    |       1 | original   | nonblocking |   1.34852e+07 |         204.727     |        16 |           0           |
| roadNet-CA    |       1 | random     | blocking    |   5.4155e+06  |         510.98      |        16 |           0           |
| roadNet-CA    |       1 | random     | nonblocking |   5.67816e+06 |         486.388     |        16 |           0           |
| roadNet-CA    |       2 | original   | blocking    |   1.38691e+07 |         199.049     |        16 |       17834           |
| roadNet-CA    |       2 | original   | nonblocking |   1.54116e+07 |         179.132     |        16 |       17834           |
| roadNet-CA    |       2 | random     | blocking    |   4.72743e+06 |         583.924     |        16 |           2.76336e+06 |
| roadNet-CA    |       2 | random     | nonblocking |   4.64747e+06 |         594.165     |        16 |           2.76336e+06 |
| roadNet-CA    |       4 | original   | blocking    |   1.03568e+07 |         266.724     |        16 |       23712           |
| roadNet-CA    |       4 | original   | nonblocking |   1.0613e+07  |         260.12      |        16 |       23712           |
| roadNet-CA    |       4 | random     | blocking    |   3.3354e+06  |         836.849     |        16 |           4.1418e+06  |
| roadNet-CA    |       4 | random     | nonblocking |   3.65526e+06 |         755.264     |        16 |           4.1418e+06  |
| roadNet-CA    |       8 | original   | blocking    |   8.9213e+06  |         309.793     |        16 |       42020           |
| roadNet-CA    |       8 | original   | nonblocking |   8.49202e+06 |         325.126     |        16 |       42020           |
| roadNet-CA    |       8 | random     | blocking    |   3.28346e+06 |         840.698     |        16 |           4.83119e+06 |
| roadNet-CA    |       8 | random     | nonblocking |   2.95718e+06 |         933.489     |        16 |           4.83119e+06 |
| roadNet-CA    |      16 | original   | blocking    |   4.67236e+06 |         590.846     |        16 |      105374           |
| roadNet-CA    |      16 | original   | nonblocking |   4.8425e+06  |         570.063     |        16 |      105374           |
| roadNet-CA    |      16 | random     | blocking    |   1.75293e+06 |        1574.86      |        16 |           5.17631e+06 |
| roadNet-CA    |      16 | random     | nonblocking |   1.66669e+06 |        1656.26      |        16 |           5.17631e+06 |
| soc-Epinions1 |       1 | original   | blocking    |   3.65508e+07 |           7.18627   |        16 |           0           |
| soc-Epinions1 |       1 | original   | nonblocking |   4.9397e+07  |           6.9293    |        16 |           0           |
| soc-Epinions1 |       1 | random     | blocking    |   3.9929e+07  |           8.51865   |        16 |           0           |
| soc-Epinions1 |       1 | random     | nonblocking |   4.61403e+07 |           8.64325   |        16 |           0           |
| soc-Epinions1 |       2 | original   | blocking    |   2.21562e+07 |          12.7511    |        16 |       41293           |
| soc-Epinions1 |       2 | original   | nonblocking |   2.25116e+07 |          11.3634    |        16 |       41293           |
| soc-Epinions1 |       2 | random     | blocking    |   2.045e+07   |          12.498     |        16 |      233685           |
| soc-Epinions1 |       2 | random     | nonblocking |   3.00592e+07 |          12.5694    |        16 |      233685           |
| soc-Epinions1 |       4 | original   | blocking    |   2.52966e+07 |          11.1037    |        16 |      109012           |
| soc-Epinions1 |       4 | original   | nonblocking |   1.37932e+07 |          16.7772    |        16 |      109012           |
| soc-Epinions1 |       4 | random     | blocking    |   9.63934e+06 |          17.9698    |        16 |      350684           |
| soc-Epinions1 |       4 | random     | nonblocking |   2.07496e+07 |          16.9502    |        16 |      350684           |
| soc-Epinions1 |       8 | original   | blocking    |   2.46683e+07 |          14.7333    |        16 |      181991           |
| soc-Epinions1 |       8 | original   | nonblocking |   2.32182e+07 |          16.0373    |        16 |      181991           |
| soc-Epinions1 |       8 | random     | blocking    |   9.98226e+06 |          34.7565    |        16 |      409225           |
| soc-Epinions1 |       8 | random     | nonblocking |   1.12594e+07 |          19.3228    |        16 |      409225           |
| soc-Epinions1 |      16 | original   | blocking    |   1.41926e+07 |          22.6361    |        16 |      265117           |
| soc-Epinions1 |      16 | original   | nonblocking |   1.21626e+07 |          21.3607    |        16 |      265117           |
| soc-Epinions1 |      16 | random     | blocking    |   6.14741e+06 |          60.0329    |        16 |      438314           |
| soc-Epinions1 |      16 | random     | nonblocking |   7.02334e+06 |          33.931     |        16 |      438314           |
| web-Google    |       1 | original   | blocking    |   2.47323e+07 |         143.983     |        16 |           0           |
| web-Google    |       1 | original   | nonblocking |   2.4877e+07  |         145.522     |        16 |           0           |
| web-Google    |       1 | random     | blocking    |   2.14844e+07 |         148.114     |        16 |           0           |
| web-Google    |       1 | random     | nonblocking |   2.41426e+07 |         147.046     |        16 |           0           |
| web-Google    |       2 | original   | blocking    |   1.06037e+07 |         235.591     |        16 |           1.93343e+06 |
| web-Google    |       2 | original   | nonblocking |   1.20542e+07 |         216.103     |        16 |           1.93343e+06 |
| web-Google    |       2 | random     | blocking    |   1.75694e+07 |         189.18      |        16 |           1.93762e+06 |
| web-Google    |       2 | random     | nonblocking |   1.34183e+07 |         207.585     |        16 |           1.93762e+06 |
| web-Google    |       4 | original   | blocking    |   1.40146e+07 |         227.97      |        16 |           2.90217e+06 |
| web-Google    |       4 | original   | nonblocking |   1.42112e+07 |         237.223     |        16 |           2.90217e+06 |
| web-Google    |       4 | random     | blocking    |   1.04034e+07 |         259.89      |        16 |           2.90658e+06 |
| web-Google    |       4 | random     | nonblocking |   1.39687e+07 |         251.279     |        16 |           2.90658e+06 |
| web-Google    |       8 | original   | blocking    |   1.07208e+07 |         243.781     |        16 |           3.38647e+06 |
| web-Google    |       8 | original   | nonblocking |   9.96026e+06 |         282.143     |        16 |           3.38647e+06 |
| web-Google    |       8 | random     | blocking    |   1.23297e+07 |         246.029     |        16 |           3.38977e+06 |
| web-Google    |       8 | random     | nonblocking |   1.31672e+07 |         257.439     |        16 |           3.38977e+06 |
| web-Google    |      16 | original   | blocking    |   8.06266e+06 |         303.061     |        16 |           3.63053e+06 |
| web-Google    |      16 | original   | nonblocking |   8.50376e+06 |         299.454     |        16 |           3.63053e+06 |
| web-Google    |      16 | random     | blocking    |   1.22441e+07 |         275.666     |        16 |           3.63226e+06 |
| web-Google    |      16 | random     | nonblocking |   1.20746e+07 |         292.99      |        16 |           3.63226e+06 |

## Interpretation guidance

- TEPS is computed from traversed directed arcs (or undirected edges for undirected inputs) divided by measured BFS elapsed time.
- Observed BFS source count per configuration: 16; the table reports median TEPS across the recorded source runs.
- MPI process counts present in this run: 1, 2, 4, 8, 16. These are single-node MPI ranks when executed on Colab.
- Compare blocking and non-blocking only within the same dataset, rank count and vertex ordering. Non-blocking collectives permit overlap but do not guarantee progress or a speedup.
- The timed BFS retains the required global next-frontier termination reduction. Per-level diagnostic reductions are aggregated after the timer stops; graph construction and correctness validation are also outside the timed region.
- Per-level computation is expansion + local-candidate processing + received-candidate merging. Exposed communication is packing + count exchange + blocking payload collective, or packing + count exchange + residual wait for non-blocking mode. The non-blocking request lifetime includes overlapped local work and is therefore shown separately.
- Edge cut and edge-load imbalance are compared for both original and fixed-seed Feistel-relabeled vertex orderings. Remote candidate-pair traffic is shown at each rank count rather than pooled across rank counts.
- For graphs up to 2^21 vertices, levels are additionally compared with a sequential queue-based BFS reference; larger graphs retain distributed structural validation.

## Reproducibility

The raw per-source/per-level CSV files, rank metrics, logs, environment record and plotting scripts accompany this report. No unmeasured values are inserted.

## Environment

```text
MPI implementation: Open MPI
Compiler: /usr/bin/mpicxx.openmpi
Compiler version: /usr/bin/mpicxx.openmpi: Open MPI 4.1.6 (Language: C++)
Launcher: /usr/bin/mpirun.openmpi
Launcher version: mpirun.openmpi (OpenRTE) 4.1.6

Report bugs to http://www.open-mpi.org/community/help/
Available logical CPUs recorded by Notebook 03: 2
Platform: single Google Colab VM; MPI ranks are not distributed across multiple nodes.
Interpretation: rank counts greater than the available logical CPU count are oversubscribed.
```

## Partial-matrix coverage and interpretation limits

- **Coverage:** 234/240 planned configurations validated (97.5%), representing 3,744 validated BFS source runs across 12 datasets.
- **Unfinished configurations:** `RMAT_s24_p16_original_blocking`; `RMAT_s24_p16_original_nonblocking`; `RMAT_s24_p16_random_blocking`; `RMAT_s24_p16_random_nonblocking`; `RMAT_s24_p8_random_blocking`; `RMAT_s24_p8_random_nonblocking`. These six cases are excluded; no values are estimated or imputed.
- **Zero-work measurements:** 2,102/3,744 recorded runs (56.1%) traversed zero edges. The fixed-seed source sample is not degree-stratified.
- **R-MAT interpretation:** RMAT_s17 through RMAT_s24 have zero median TEPS when all 16 sampled sources are included. `summary_aggregated.csv` also contains active-only median TEPS/elapsed time and the active-source count. Those active-only figures are based on small samples and are exploratory; they do not replace the all-source median.
- **Execution environment:** Notebook 03 recorded 2 logical CPUs on one Colab VM. Runs with more MPI ranks than available logical CPUs are oversubscribed; do not interpret them as dedicated-core or multi-node scaling results.
- **Per-level plot coverage:** each comparison uses the highest rank count common to all four ordering/communication combinations. For RMAT_s24, the common comparison is P=4 because higher-rank configurations are incomplete.

### Fixed-seed source sample outcomes

| Dataset | Sampled sources | Zero-work sources | Active sources | Zero-work share |
|---|---:|---:|---:|---:|
| RMAT_s16 | 16 | 8 | 8 | 50.0% |
| RMAT_s17 | 16 | 10 | 6 | 62.5% |
| RMAT_s18 | 16 | 11 | 5 | 68.8% |
| RMAT_s19 | 16 | 11 | 5 | 68.8% |
| RMAT_s20 | 16 | 11 | 5 | 68.8% |
| RMAT_s21 | 16 | 11 | 5 | 68.8% |
| RMAT_s22 | 16 | 11 | 5 | 68.8% |
| RMAT_s23 | 16 | 13 | 3 | 81.2% |
| RMAT_s24 | 16 | 13 | 3 | 81.2% |
| roadNet-CA | 16 | 0 | 16 | 0.0% |
| soc-Epinions1 | 16 | 6 | 10 | 37.5% |
| web-Google | 16 | 4 | 12 | 25.0% |

*The main median-TEPS table includes zero-work measurements. `source_sampling_audit.csv` counts each fixed-seed source once per dataset; `summary_aggregated.csv` reports per-configuration zero-work counts and active-only derived statistics.*
