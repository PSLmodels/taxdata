About puf_stage2
================

This directory contains the following script:

* Python script **stage2.py**, which calls a function in the
`solve_lp_for_year.py` file, reads/writes:

  Input files:
    - ../puf_data/cps-matched-puf.csv (not in repo because is restricted)
    - ../stage1/Stage_I_factors_transpose.csv
    - ../stage1/Stage_II_targets.csv

  Output files:
    - puf_weights.csv


Documentation
-------------

For historical documentation on stage1 and stage2 methods and how they
have been used in this project, see:
- [Stage1 and Stage2 Methodology](../doc/Stage1_Stage2_Methodology.pdf)
- [Methods Applied to 2009 PUF](../doc/Stage1_Stage2_2009PUF.pdf)
