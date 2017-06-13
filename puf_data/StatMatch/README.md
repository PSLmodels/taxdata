# StatMatch
This repo holds scripts for performing a statistical match
using the March 2014 CPS and 2009 IRS SOI Public Use File (PUF) datasets

## Usage
The entire statistical match can be run by using `python runmatch.py` in the
command line. Three optional arguments can be included as well:

* `-c`, `--cps` takes the path to an already created .CSV version of the CPS.
Including this will allow the program to simply read in the CSV, rather than
converting it from .DAT format.
* `-d`, `--dat` takes the path to the CSV in .DAT format
* `-p`, `--puf` takes the PATH to the (PUF) file in .CSV format

All of the above are necessary only if the CPS and PUF files are not contained
in the same directory as the `runmatch.py` script.

Files are run in the following order:

1. `cpsmar.py`
2. `cps_rets.py`
3. `adj_filst.py`
4. `soi_rets.py`
5. `phase1.py`
6. `phase2.py`
7. `add_cps_vars.py`
8. `add_nonfilers.py`
