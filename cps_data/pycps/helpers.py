import numpy as np
from pathlib import Path
from paramtools.parameters import Parameters


CUR_PATH = Path().resolve()
PUF_YEAR = 2011
CPS_YEAR = 2013
# variables we're taking the log of for the imputation regressions
LOG_VARS = ["tot_inc", "interest", "divs", "E01500"]
# X variables used in most of the imputation regressions
X_VARS = ["lntot_inc", "joint_filer", "fam_size", "agede", "constant"]


class FilingParams(Parameters):
    defaults = Path(CUR_PATH, "filing_rules.json").open("r").read()
    label_to_extend = "year"
    array_first = True


FILINGPARAMS = FilingParams()
# this index is used to access the filing parameter values for the correct year
PUF_YR_IDX = PUF_YEAR - FILINGPARAMS.label_grid["year"][0]
CPS_YR_IDX = CPS_YEAR - FILINGPARAMS.label_grid["year"][0]


def log(data, var):
    """
    Find and return the log of var
    """
    return np.log(1. + np.maximum(0., data[var]))
