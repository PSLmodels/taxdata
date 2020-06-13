import pandas as pd
from functools import reduce
from pathlib import Path


def merge_benefits(cps, year, data_path, export=True):
    """
    Merge the benefit variables onto the CPS files. TaxData use the
    following variables imputed by C-TAM:
    Medicaid: MedicaidX
    Medicare: MedicareX
    Veterans Benefits: vb_impute
    SNAP: SNAP_Imputation
    SSI: ssi_impute
    Social Security: ss_val (renamed to ss_impute)
    Housing assistance: housing_impute
    TANF: tanf_impute
    Unemployment Insurance: UI_impute
    WIC: (women, children, infants): wic_impute (renamed wic_women,
        wic_children, and wic_infants)
    """
    def read_ben(path_prefix, usecols):
        path = Path(data_path, path_prefix + str(year) + ".csv")
        return pd.read_csv(path, usecols=usecols)

    start_len = len(cps)
    # read in benefit imputations
    mcaid = read_ben("medicaid", ["MedicaidX", "peridnum"])
    mcare = read_ben("medicare", ["MedicareX", "peridnum"])
    vb = read_ben("VB_Imputation", ["vb_impute", "peridnum"])
    snap = read_ben("SNAP_Imputation_", ["h_seq", "snap_impute"])
    ssi = read_ben("SSI_Imputation", ["ssi_impute", "peridnum"])
    ss = read_ben(
        "SS_augmentation_", ["ss_val", "peridnum"]
    ).rename(columns={"ss_val": "ss_impute"})
    housing = read_ben("Housing_Imputation_logreg_",
                       ["fh_seq", "ffpos", "housing_impute"])
    tanf = read_ben("TANF_Imputation_", ["peridnum", "tanf_impute"])
    # drop duplicated people in tanf
    tanf.drop_duplicates("peridnum", inplace=True)
    ui = read_ben("UI_imputation_logreg_", ["peridnum", "UI_impute"])

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
    wic = reduce(lambda left, right: pd.merge(left, right, on="peridnum"),
                 [wic_children, wic_infants, wic_women])
    wic["wic_impute"] = wic[
        ["wic_women", "wic_infants", "wic_children"]
    ].sum(axis=1)

    # merge housing and snap
    cps_merged = cps.merge(housing, on=["fh_seq", "ffpos"], how="left")
    cps_merged = cps_merged.merge(snap, on="h_seq", how="left")
    # merge other variables
    peridnum_dfs = [cps_merged, vb, ssi, ss, tanf, ui, wic, mcaid, mcare]
    cps_merged = reduce(lambda left, right: pd.merge(left, right,
                                                     on="peridnum",
                                                     how="left"),
                        peridnum_dfs).fillna(0.)

    if export:
        print("Saving {} Data".format(year))
        cps_merged.to_csv(Path(data_path, f"cpsmar{year}_ben.csv"),
                          index=False)

    del mcaid, mcare, vb, ssi, ss, tanf, ui, wic, housing, snap
    # assert that no additional rows have been introduced by bad merges
    assert start_len == len(cps_merged)

    return cps_merged


def distribute_benefits(data, other_ben):
    """
    There are a number of benefit programs that are not imputed by C-TAM, but
    whose costs are still important to have in our dataset. A list of these
    programs and their costs can be found in tables 3.2 adn 11.2 here
    https://obamawhitehouse.archives.gov/omb/budget/Historicals

    We base the distribution of these variables on the distribution of
    Medicare, SSI, and SNAP.
    Distribute benefits from non-models benefit programs and create total
    benefits variable.
    """
    other_ben["2014_cost"] *= 1e6

    # adjust medicare and medicaid totals
    weighted_mcare_count = (data["mcare_count"] * data["s006"]).sum()
    weighted_mcaid_count = (data["mcaid_count"] * data["s006"]).sum()
    weighted_mcare = (data["mcare_ben"] * data["s006"]).sum()
    weighted_mcaid = (data["mcaid_ben"] * data["s006"]).sum()
    mcare_amt = weighted_mcare / weighted_mcare_count
    mcaid_amt = weighted_mcaid / weighted_mcaid_count
    data["mcaid_ben"] = data["mcaid_count"] * mcaid_amt
    data["mcare_ben"] = data["mcare_count"] * mcare_amt

    # Distribute other benefits
    data["dist_ben"] = data[["mcaid_ben", "ssi_ben", "snap_ben"]].sum(axis=1)
    data["ratio"] = (data["dist_ben"] * data["s006"] /
                     (data["dist_ben"] * data["s006"]).sum())
    # ... remove TANF and WIC from other_ben total
    tanf_total = (data["tanf_ben"] * data["s006"]).sum()
    wic_total = (data["wic_ben"] * data["s006"]).sum()
    other_ben_total = other_ben["2014_cost"].sum() - tanf_total - wic_total
    # ... divide by the weight to account for weighting in Tax-Calculator
    data["other_ben"] = (data["ratio"] * other_ben_total / data["s006"])

    data["housing_ben"] *= 12

    return data
