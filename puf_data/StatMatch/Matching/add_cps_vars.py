"""
Put together the final Production File
Note: filers only
Input file: cpsrets14.csv, puf2009.sas7bdat, match.csv
Output file: cpsrets.csv
"""

import pandas as pd


def add_cps(cps_recs, match, puffile):
    cpsfile = cps_recs.filter(
        regex=r"jcps\d{1,2}$|icps\d{1}$|"
        + "jcps100|cpsseq|"
        + r"nu\d{1,2}|nu18_dep|n1820|n21|"
        + "elderly_dependent|wasp|wass|xstate"
    )

    puffile = puffile[
        (puffile["recid"] != 999999)
        & (puffile["recid"] != 999998)
        & (puffile["recid"] != 999997)
        & (puffile["recid"] != 999996)
    ]
    puffile["filer"] = 1
    puffile["wt"] = puffile["s006"] / 100.0
    puffile["soiseq"] = puffile.index + 1

    match.sort_values(["cpsseq"], inplace=True, kind="mergesort")
    merge_1 = pd.merge(match, cpsfile, how="left", on=["cpsseq"])
    merge_1.sort_values(["soiseq"], inplace=True, kind="mergesort")
    merge_2 = pd.merge(merge_1, puffile, how="left", on=["soiseq"])

    merge_2["prodseq"] = merge_2.index + 1
    merge_2.rename(columns={"cwt": "cweight"}, inplace=True)
    merge_2["matched_weight"] = merge_2["cweight"]
    merge_2["cweight"] = merge_2["wt"]

    return merge_2
