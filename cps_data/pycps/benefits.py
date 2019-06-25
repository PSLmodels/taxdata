import pandas as pd
import numpy as np
from pathlib import Path


def mergebenefits(cps, year, data_path, export=True):
    """
    Merge the benefit variables onto the CPS files.
    """
    start_len = len(cps)
    # read in benefit imputations
    mcaid_path = Path(data_path, f"medicaid{year}.csv")
    mcaid = pd.read_csv(mcaid_path, usecols=["MedicaidX", "peridnum"])

    mcare_path = Path(data_path, f"medicare{year}.csv")
    mcare = pd.read_csv(mcare_path, usecols=["MedicareX", "peridnum"])

    vb_path = Path(data_path, f"VB_Imputation{year}.csv")
    vb = pd.read_csv(vb_path, usecols=["vb_impute", "peridnum"])

    snap_path = Path(data_path, f"SNAP_Imputation_{year}.csv")
    snap = pd.read_csv(snap_path, usecols=["h_seq", "snap_impute"])

    ssi_path = Path(data_path, f"SSI_Imputation{year}.csv")
    ssi = pd.read_csv(ssi_path, usecols=["ssi_impute", "peridnum"])

    ss_path = Path(data_path, f"SS_augmentation_{year}.csv")
    ss = pd.read_csv(ss_path, usecols=["ss_val", "peridnum"])
    ss = ss.rename(columns={"ss_val": "ss_impute"})

    housing_path = Path(data_path, f"Housing_Imputation_logreg_{year}.csv")
    housing = pd.read_csv(housing_path,
                          usecols=["fh_seq", "ffpos", "housing_impute"])

    tanf_path = Path(data_path, f"TANF_Imputation_{year}.csv")
    tanf = pd.read_csv(tanf_path, usecols=["peridnum", "tanf_impute"])
    # drop duplicated people in tanf
    tanf = tanf.drop_duplicates("peridnum")

    ui_path = Path(data_path, f"UI_imputation_logreg_{year}.csv")
    ui = pd.read_csv(ui_path, usecols=["peridnum", "UI_impute"])

    wic_str = "WIC_imputation_{}_logreg_{}.csv"
    wic_path = Path(data_path, wic_str.format("children", year))
    wic_children = pd.read_csv(wic_path,
                               usecols=["peridnum", "WIC_impute"])
    wic_children = wic_children.rename(columns={"WIC_impute": "wic_children"})
    wic_path = Path(data_path, wic_str.format("infants", year))
    wic_infants = pd.read_csv(wic_path,
                              usecols=["peridnum", "WIC_impute"])
    wic_infants = wic_infants.rename(columns={"WIC_impute": "wic_infants"})
    wic_path = Path(data_path, wic_str.format("women", year))
    wic_women = pd.read_csv(wic_path,
                            usecols=["peridnum", "WIC_impute"])
    wic_women = wic_women.rename(columns={"WIC_impute": "wic_women"})
    wic = wic_children.merge(wic_infants, on="peridnum")
    wic = wic.merge(wic_women, on="peridnum")
    wic["wic_impute"] = wic[
        ["wic_children", "wic_infants", "wic_children"]
    ].sum(axis=1)

    # merge housing and snap
    cps_merged = cps.merge(housing, on=["fh_seq", "ffpos"], how="left")
    cps_merged = cps_merged.merge(snap, on="h_seq", how="left")
    # merge other variables
    peridnum_dfs = [vb, ssi, ss, tanf, ui, wic, mcaid, mcare]
    for i, df in enumerate(peridnum_dfs):
        cps_merged = cps_merged.merge(df, on="peridnum", how="left")
        print(i, len(cps_merged))
    cps_merged = cps_merged.fillna(0.)

    if export:
        print("Saving {} Data".format(year))
        cps_merged.to_csv(Path(data_path, f"cpsmar{year}_ben.csv"),
                          index=False)

    # del mcaid, mcare, vb, ssi, ss, tanf, ui, wic, housing, snap
    # assert start_len == len(cps_merged)
    if start_len != len(cps_merged):
        import pdb
        pdb.set_trace()
    return cps_merged


def distributebenefits(data, other_ben):
    """
    Distribute benefits from non-models benefit programs and create total
    benefits variable.
    Replaces Medicare and Medicaid values with set amounts
    """
    other_ben["2014_cost"] *= 1e6

    # Distribute other benefits
    data["dist_ben"] = (data["mcaid_ben"] + data["ssi_ben"] +
                        data["snap_ben"])
    data["ratio"] = (data["dist_ben"] * data["s006"] /
                     (data["dist_ben"] * data["s006"]).sum())
    # ... remove TANF and WIC from other_ben total
    tanf = (data["tanf_ben"] * data["s006"]).sum()
    wic = (data["wic_ben"] * data["s006"]).sum()
    other_ben_total = other_ben["2014_cost"].sum() - tanf - wic
    # ... divide by the weight to account for weighting in Tax-Calculator
    data["other_ben"] = (data["ratio"] * other_ben_total / data["s006"])

    # Convert benefit data to integers
    data["mcaid_ben"] = data["mcaid_ben"].astype(np.int32)
    data["mcare_ben"] = data["mcare_ben"].astype(np.int32)
    data["ssi_ben"] = data["ssi_ben"].astype(np.int32)
    data["snap_ben"] = data["snap_ben"].astype(np.int32)
    data["vet_ben"] = data["vet_ben"].astype(np.int32)
    data["tanf_ben"] = data["tanf_ben"].astype(np.int32)
    data["wic_ben"] = data["wic_ben"].astype(np.int32)
    data["housing_ben"] *= 12
    data["housing_ben"] = data["housing_ben"].astype(np.int32)
    data["e02400"] = data["e02400"].astype(np.int32)
    data["e02300"] = data["e02300"].astype(np.int32)
    data["other_ben"] = data["other_ben"].astype(np.int32)

    return data
