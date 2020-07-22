About taxdata Repository
========================

This repository prepares data used in the [Tax-Calculator
repository](https://github.com/open-source-economics/Tax-Calculator).

The data files produced here, all of which have CSV format, provide
two different sets of data files for Tax-Calculator:

- A set based on a recent **IRS-SOI Public Use File (PUF)**

- A set based on recent **Census Current Population Survey (CPS)** data

Because the PUF data are restricted in their use, the IRS-SOI-supplied
PUF file and the `puf.csv` data file produced here are not part of the
taxdata repository or the Tax-Calculator repository.

Each of these two sets of data files contains several types of files:

0. a sample data file containing variables for each tax filing unit;

1. a factors file containing annual variable extrapolation factors;

2. a weights file containing annual weights for each filing unit;

3. a ratios file containing annual adjustment ratios for some variables
   (currently only the PUF data set includes a ratios file);

4. a benefits file containing extrapolated benefits for each filing unit
   (currently only the CPS data set includes a benefits file).

Note that the factors file is the same in both sets of data files
because the variable extrapolation factors are independent of the
sample data being used.  But the weights, ratios, and benefits files
do depend on the data file, so they are different in the two sets of
data files.

Installation
-----------

Currently, the only way to install `taxdata` currently is to clone the git
repo locally.
```
git clone https://github.com/PSLmodels/taxdata.git
```
Next navigate to the directory and install the `taxdata-dev` conda environment
```
cd taxdata
conda env create -f environment.yml
```
To run the scripts that produce `puf.csv` and `cps.csv.gz`, activate the
`taxdata-dev` conda environment and follow the workflow laid out below.

Data-Preparation Documentation and Workflow
-------------------------------------------

The best documentation of the data-preparation workflow is the
[taxdata Makefile](Makefile).  The Makefile shows the input files and
the Python script that generates each made file.  The files made in
early stages of the workflow serve as input files in later stages,
which means there is a cascading effect of changes in the scripts
and/or input files.  The Makefile automates this complex workflow in
an economical way because it executes scripts to make new versions of
made files only when necessary.  Start exploring the Makefile by
running the `make help` command.  If you want more background on the
make utility and makefiles, search for Internet links with the
keywords `makefile` and `automate`.

Note that the stage2 linear program that generates the weights file for the PUF
is very long-running, taking five or more hours depending on your
computer's CPU speed.  We are considering options for speeding up this
stage2 work, but for the time being you can execute `make puf-files`
and `make cps-files` in separate terminal windows to have the two
stage2 linear programs run in parallel.  (If you try this parallel
execution approach, be sure to wait for the `make puf-files` job to
begin stage2 work before executing the `make cps-files` command in
the other terminal window.  This is necessary because the CPS stage1
work depends on output from PUF stage1.)  If you are generating the
taxdata made files in an overnight run, then simply execute the `make
all` command.

You can copy the made files to your local Tax-Calculator directory
tree using the [`csvcopy.sh`](csvcopy.sh) bash script.  Use the `dryrun`
option to see which files would be copied (because they are newer than
the corresponding files in the Tax-Calculator directory tree) without
actually doing the file copies.  At the terminal command-prompt in the
top-level taxdata directory, execute `./csvcopy.sh` to get help.

### Example

To create `cps.csv.gz`, run
```
conda activate taxdata-dev
make cps-files
```


Contributing to taxdata Repository
----------------------------------

Before creating a GitHub pull request, on your development branch in
the top-level directory of the taxdata repository, run `make cstest`
to make sure your proposed code is consistent with the repository's
coding style and then run `make pytest` to ensure that all the tests
pass.

Disclaimer
----------

`taxdata` is under continuous development. As such, results will change as the
underlying data and logic improves.


Contributors
------------

A full list of contributors on GitHub can be found 
here](https://github.com/PSLmodels/taxdata/graphs/contributors). John O'Hare
of Quantria Strategies has also made significant contributions to the
development of `taxdata`.