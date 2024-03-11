"""
Transform Stage_I_factors.csv (written by the stage1.py script) and
benefit_growth_rates.csv into growfactors.csv (used by Tax-Calculator).
"""

import pandas as pd
import os

# pylint: disable=invalid-name

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
first_benefit_year = 2014
inben_filename = os.path.join(CUR_PATH, "benefit_growth_rates.csv")
first_data_year = 2011
infac_filename = os.path.join(CUR_PATH, "Stage_I_factors.csv")
output_filename = os.path.join(CUR_PATH, "growfactors.csv")

# --------------------------------------------------------------------------
# read in raw average benefit amounts by year and
# convert into "one plus annual proportion change" factors
bgr_all = pd.read_csv(inben_filename, index_col="YEAR")
bnames = ["mcare", "mcaid", "ssi", "snap", "wic", "housing", "tanf", "vet"]
keep_cols = ["{}_average_benefit".format(bname) for bname in bnames]
bgr_raw = bgr_all[keep_cols]
gf_bnames = ["ABEN{}".format(bname.upper()) for bname in bnames]
bgr_raw.columns = gf_bnames
bgf = 1.0 + bgr_raw.astype("float64").pct_change()

# specify first row values because pct_change() leaves first year undefined
for var in list(bgf):
    bgf[var][first_benefit_year] = 1.0

# add rows of ones for years from first_data_year thru first_benefit_year-1
ones = [1.0] * len(bnames)
for year in range(first_data_year, first_benefit_year):
    row = pd.DataFrame(data=[ones], columns=gf_bnames, index=[year])
    bgf = pd.concat([bgf, row], verify_integrity=True)
bgf.sort_index(inplace=True)

# round converted factors to six decimal digits of accuracy
bgf = bgf.round(6)

# --------------------------------------------------------------------------
# read in blowup factors used internally in taxdata repository
data = pd.read_csv(infac_filename, index_col="YEAR")

# convert some aggregate factors into per-capita factors
elderly_pop = data["APOPSNR"]
data["ASOCSEC"] = data["ASOCSEC"] / elderly_pop
pop = data["APOPN"]
data["AWAGE"] = data["AWAGE"] / pop
data["ATXPY"] = data["ATXPY"] / pop
data["ASCHCI"] = data["ASCHCI"] / pop
data["ASCHCL"] = data["ASCHCL"] / pop
data["ASCHF"] = data["ASCHF"] / pop
data["AINTS"] = data["AINTS"] / pop
data["ADIVS"] = data["ADIVS"] / pop
data["ASCHEI"] = data["ASCHEI"] / pop
data["ASCHEL"] = data["ASCHEL"] / pop
data["ACGNS"] = data["ACGNS"] / pop
data["ABOOK"] = data["ABOOK"] / pop
data["ABENEFITS"] = data["ABENEFITS"] / pop
data.rename(columns={"ABENEFITS": "ABENOTHER"}, inplace=True)

# convert factors into "one plus annual proportion change" format
data = 1.0 + data.pct_change()

# specify first row values because pct_change() leaves first year undefined
for var in list(data):
    data[var][first_data_year] = 1.0

# round converted factors to six decimal digits of accuracy
data = data.round(6)

# --------------------------------------------------------------------------
# combine data and bgf DataFrames
gfdf = pd.concat([data, bgf], axis="columns", verify_integrity=True)

# --------------------------------------------------------------------------
# delete from data the variables not used by Tax-Calculator (TC)
TC_USED_VARS = set(
    [
        "ABOOK",
        "ACGNS",
        "ACPIM",
        "ACPIU",
        "ADIVS",
        "AINTS",
        "AIPD",
        "ASCHCI",
        "ASCHCL",
        "ASCHEI",
        "ASCHEL",
        "ASCHF",
        "ASOCSEC",
        "ATXPY",
        "AUCOMP",
        "AWAGE",
        "ABENOTHER",
    ]
    + gf_bnames
)
ALL_VARS = set(list(gfdf))
TC_UNUSED_VARS = ALL_VARS - TC_USED_VARS
gfdf = gfdf.drop(TC_UNUSED_VARS, axis=1)

# write out grow factors used in blowup logic in Tax-Calculator repository
gfdf.to_csv(output_filename, index_label="YEAR")
