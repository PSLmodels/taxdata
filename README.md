# taxdata

- The first component of this taxdata repo is the extrapolation routine of IRS Public Use File. This procedure extrapolates the tax data input from one year, currently 2008 and soon to be 2009, to
all the years on the budget window, using external economic projections. These extrapolated data can be used for federal individual income tax calculations and revenue projections.
    - You can find a brief description of the currently methodology [here](https://github.com/open-source-economics/taxdata/blob/master/docs/info/Extrapolation_description.pdf)
    - Previously, the extrapolation routine was coded in SAS, fortran and Excel. The scripts can be found [here](https://www.dropbox.com/sh/llaisso557ppf3f/AABexU9ELw5BHpNB3fVRuFxEa?dl=0).
    - This routine now has been translated into python.
- The extrapolation includes two stages, Stage I and Stage II. The python scripts for the two stages are respectively in the folders with those names.
    - The stage I script is able to produce two files, Stage I factors and Stage II targets, and save them in the
Stage II folder. You can replicate Stage I by running [Stage I.py](https://github.com/OpenSourcePolicyCenter/taxdata/blob/master/Stage%20I/Stage%20I.py) inside Stage I folder.
All the raw datasets from CBO, IRS and Census are in the same folder. More detailed information on the raw datasets can be found [here](https://github.com/OpenSourcePolicyCenter/taxdata/blob/master/Stage%20II/CLP_solver_16Years.py).
    - The Stage II script, currently for 16 years of extrapolation, takes in the factors and targets from stage I and generates the final weights (WEIGHTS.csv) for Tax-Calculator. Stage II process can
    be replicated by running [CLP_solver_16years.py](https://github.com/OpenSourcePolicyCenter/taxdata/blob/master/Stage%20II/CLP_solver_16Years.py). 

# Contributors
- John O'Hare
- Amy Xu
