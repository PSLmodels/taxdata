About stage1
============

This directory contains the following scripts:

* Python script **stage1.py**, which reads/writes:

  Input files:
    - NP2014_D1.csv
    - NC-EST2014-AGESEX-RES.csv
    - US-EST00INT-ALLDATA.csv
    - CBO_baseline.csv
    - IRS_return_projection.csv
    - SOI_estimates.csv

  Output files:
    - Stage_I_factors.csv
    - Stage_II_targets.csv
    - Stage_I_factors_transpose.csv

* Python script **factor_finalprep.py**, which reads/writes:

  Input file:
    - Stage_I_factors.csv

  Output file:
    - growfactors.csv


Documentation
-------------

**all documentation files go in a `doc` subdirectory of this directory**

For information on the source of the input file data, see:
- [Stage 1 Growth Rate Sources](docs/Stage1_Growth_Rate_Sources.csv)
- [Stage 2 Base Year Sources](docs/Stage2_Base_Year_Sources.csv)

For information on updating input data, see:
- [CBO Baseline Updating Instructions](CBO_Baseline_Updating_Instructions.txt)
- [SOI Estimates Updating Instructions](SOI_Estimates_Updating_Instrutions.txt)