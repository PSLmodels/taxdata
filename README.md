About taxdata Repository
========================

This repository prepares data used in the [Tax-Calculator
repository](https://github.com/open-source-economics/Tax-Calculator).

The data produced here, all of which have CSV format, provide
two different sets of data files for Tax-Calculator:

* A set based on a recent **IRS-SOI Public Use File (PUF)**

* A set based on recent **Census Current Population Survey (CPS)** data

Because the PUF data are restricted in their use, the IRS-SOI-supplied
PUF file and the `puf.csv` data file produced here are not part of the
taxdata or the Tax-Calculator repository.

Each of these two sets of data files contains four files:

1. a sample data file containing variables for each tax filing unit;

2. a factors file containing annual variable extrapolation factors;

3. a weights file containing annual weights for each filing unit;

4. a ratios file containing annual adjustment ratios for some variables.

Note that the factors file is the same in both sets of data files
because the variable extrapolation factors are independent of the
sample data being used.  But the weights and ratios files do depend on
the data file, so they are different in the two sets of data files.


Data-Preparation Documentation
------------------------------

**IRS-SOI Public Use File (PUF)** documentation:

1. [PUF-based sample data](puf_data/README.md);

2. [grow factors](stage1/README.md)

3. [PUF-based sample weights](puf_stage2/README.md);

4. [PUF-based adjustment ratios](puf_stage3/README.md).

**Census Current Population Survey (CPS)** documentation is available here:

1. [CPS-based sample data](cps_data/README.md);

2. [grow factors](stage1/README.md)

3. [CPS-based sample weights](cps_stage2/README.md);

4. [CPS-based adjustment ratios](cps_stage3/README.md).


Work-Flow Documentation
-----------------------

The sequence of operations required to make the two sets of data files
is contained in the [`csvmake` bash script](csvmake), which also
automates the preparation work-flow (except on Windows).

The sequence of operations required to install the two sets of data
files in the Tax-Calculator repository is contained in the [`csvcopy`
bash script](csvcopy), which also automates the installation work-flow
(except on Windows).


Contributors
------------
- John O'Hare
- Amy Xu
- Anderson Frailey
- Martin Holmer
