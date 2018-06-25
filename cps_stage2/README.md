About cps_stage2
================

This directory contains the following script:

* Python script `stage2.py`, which reads/writes:

  Input files:
    - `../cps_data/cps_raw.csv.gz`
    - `../puf_stage1/Stage_I_factors.csv`
    - `../cps_stage1/stage_2_factors.csv`

  Output files:
    - `cps_weights.csv.gz`


Documentation
-------------

Our extrapolation and weighting methodology for the CPS file is almost identical to the methods used for the PUF.

We begin by extrapolating individual data points using the same [growth rates](https://github.com/open-source-economics/taxdata/blob/master/stage1/growfactors.csv) that we use for the PUF. We then apply a linear programming model to adjust the weights on the CPS to ensure that certain aggregate targets are hit. The CPS weighting process uses these aggregate targets:

* Single Returns
* Joint Returns
* Returns Claiming Social Security
* Number of Dependent Exemptions
* Interest Income (both taxable and not)
* Ordinary Dividends
* Business Income
* Pensions
* Social Security Income
* Unemployment Compensation
* Wages for those with AGI less than or equal to $10,000
