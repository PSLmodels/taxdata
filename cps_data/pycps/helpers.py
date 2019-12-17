import pandas as pd
import numpy as np
from pathlib import Path
from functools import reduce
from paramtools.parameters import Parameters


CUR_PATH = Path().resolve()
DATA_PATH = Path(CUR_PATH, "data")
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


def read_benefits(year):
    """
    Read in all C-TAM imputed benefits. Convert them to dictionaries for
    faster lookups
    """
    def read_ben(path_prefix, usecols, index_col=None):
        path = Path(DATA_PATH, path_prefix + str(year) + ".csv")
        return pd.read_csv(path, usecols=usecols, index_col=index_col)

    # Set global variables so they can be accested later
    global MCAID, MCARE, VB, SNAP, SSI, SS, HOUSING, TANF, UI, WIC
    # read in benefit imputations
    MCAID = read_ben(
        "medicaid", ["MedicaidX", "peridnum"], "peridnum"
    ).to_dict("index")
    MCARE = read_ben(
        "medicare", ["MedicareX", "peridnum"], "peridnum"
    ).to_dict("index")
    VB = read_ben(
        "VB_Imputation", ["vb_impute", "peridnum"], "peridnum"
    ).to_dict("index")
    SNAP = read_ben(
        "SNAP_Imputation_", ["h_seq", "snap_impute"], "h_seq"
    ).to_dict("index")
    SSI = read_ben(
        "SSI_Imputation", ["ssi_impute", "peridnum"], "peridnum"
    ).to_dict("index")
    SS = read_ben(
        "SS_augmentation_", ["ss_val", "peridnum"], "peridnum"
    ).rename(columns={"ss_val": "ss_impute"}).to_dict("index")
    HOUSING = read_ben(
        "Housing_Imputation_logreg_",
        ["fh_seq", "ffpos", "housing_impute"], None
    )
    # make a unique index from fh_seq and ffpos
    HOUSING["index"] = (HOUSING["fh_seq"].astype(str) +
                        HOUSING["ffpos"].astype(str))
    HOUSING.set_index("index", inplace=True)
    HOUSING = HOUSING.to_dict("index")
    # TODO: Look up how to drop duplicated index
    TANF = read_ben(
        "TANF_Imputation_", ["peridnum", "tanf_impute"], "peridnum"
    )
    # drop duplicated people in tanf
    TANF = TANF.loc[~TANF.index.duplicated(keep="first")]
    TANF = TANF.to_dict("index")
    UI = read_ben(
        "UI_imputation_logreg_", ["peridnum", "UI_impute"], "peridnum"
    ).to_dict("index")

    WIC_STR = "WIC_imputation_{}_logreg_"
    wic_children = read_ben(
        WIC_STR.format("children"), ["peridnum", "WIC_impute"]
    ).rename(columns={"WIC_impute": "wic_children"})
    wic_infants = read_ben(
        WIC_STR.format("infants"), ["peridnum", "WIC_impute"]
    ).rename(columns={"WIC_impute": "wic_infants"})
    wic_women = read_ben(
        WIC_STR.format("women"), ["peridnum", "WIC_impute"]
    ).rename(columns={"WIC_impute": "wic_women"})

    # combine all WIC imputation into one variable
    WIC = reduce(lambda left, right: pd.merge(left, right, on="peridnum"),
                 [wic_children, wic_infants, wic_women])
    WIC["wic_impute"] = WIC[
        ["wic_women", "wic_infants", "wic_children"]
    ].sum(axis=1)
    # Set index to pernumid
    WIC.set_index("peridnum")
    WIC = WIC.to_dict("index")

    return MCAID, MCARE, VB, SNAP, SSI, SS, HOUSING, TANF, UI, WIC
