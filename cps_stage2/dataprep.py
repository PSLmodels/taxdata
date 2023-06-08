import numpy as np
import pandas as pd


def dataprep(data, factors, targets, year, weights=None):
    """
    Parameters
    ----------
    data: CPS data
    factors: growth factors
    targets: aggregate targets
    year: year LP is being solved for
    """

    def target(target_val, pop, factor, value):
        return target_val * pop / factor * 1000 - value

    print(f"Preparing Coefficient Matrix for {year}")
    if not isinstance(weights, pd.Series):
        weights = data["s006"]
    # only use the blow up factors if we're not solving for 2014 weights
    s006 = np.where(
        data["e02400"] > 0,
        weights * factors["APOPSNR"][year],
        weights * factors["ARETS"][year],
    )
    single_returns = np.where((data["mars"] == 1) & (data["filer"] == 1), s006, 0)
    joint_returns = np.where((data["mars"] == 2) & (data["filer"] == 1), s006, 0)
    hh_returns = np.where((data["mars"] == 4) & (data["filer"] == 1), s006, 0)
    returns_w_ss = np.where((data["e02400"] > 0) & (data["filer"] == 1), s006, 0)
    dep_exemptions = (
        np.where(data["mars"] == 2, data["XTOT"] - 2, data["XTOT"] - 1) * s006
    )
    interest = data["interest"] * s006
    dividend = data["divs"] * s006
    biz_income = np.where(data["e00900"] > 0, data["e00900"], 0) * s006
    biz_loss = np.where(data["e00900"] < 0, -data["e00900"], 0) * s006
    cap_gain = np.where(data["CGAGIX"] > 0, data["CGAGIX"], 0) * s006
    pension = data["e01500"] * s006
    sch_e_income = np.where(data["rents"] > 0, data["rents"], 0) * s006
    sch_e_loss = np.where(data["rents"] < 0, -data["rents"], 0) * s006
    ss_income = np.where(data["filer"] == 1, data["e02400"], 0) * s006
    ucomp = data["e02300"] * s006

    # wage distribution
    wage1 = np.where(data["agi"] <= 10000, data["e00200"], 0) * s006
    wage2 = (
        np.where((data["agi"] > 10000) & (data["agi"] <= 20000), data["e00200"], 0)
        * s006
    )
    wage3 = (
        np.where((data["agi"] > 20000) & (data["agi"] <= 30000), data["e00200"], 0)
        * s006
    )
    wage4 = (
        np.where((data["agi"] > 30000) & (data["agi"] <= 40000), data["e00200"], 0)
        * s006
    )
    wage5 = (
        np.where((data["agi"] > 40000) & (data["agi"] <= 50000), data["e00200"], 0)
        * s006
    )
    wage6 = (
        np.where((data["agi"] > 50000) & (data["agi"] <= 75000), data["e00200"], 0)
        * s006
    )
    wage7 = (
        np.where((data["agi"] > 75000) & (data["agi"] <= 100_000), data["e00200"], 0)
        * s006
    )
    wage8 = np.where(data["agi"] > 100_000, data["e00200"], 0) * s006
    lhs_vars = {}
    lhs_vars["single_returns"] = single_returns
    lhs_vars["joint_returns"] = joint_returns
    lhs_vars["hh_returns"] = hh_returns
    lhs_vars["returns_w_ss"] = returns_w_ss
    lhs_vars["dep_exemptions"] = dep_exemptions
    lhs_vars["interest"] = interest
    lhs_vars["dividend"] = dividend
    lhs_vars["biz_income"] = biz_income
    lhs_vars["biz_loss"] = biz_loss
    lhs_vars["cap_gain"] = cap_gain
    lhs_vars["pension"] = pension
    lhs_vars["sch_e_income"] = sch_e_income
    lhs_vars["sch_e_loss"] = sch_e_loss
    lhs_vars["ss_income"] = ss_income
    lhs_vars["ucomp"] = ucomp
    lhs_vars["wage1"] = wage1
    lhs_vars["wage2"] = wage2
    lhs_vars["wage3"] = wage3
    lhs_vars["wage4"] = wage4
    lhs_vars["wage5"] = wage5
    lhs_vars["wage6"] = wage6
    lhs_vars["wage7"] = wage7
    lhs_vars["wage8"] = wage8

    print(f"Preparing Targets for {year}")
    apopn = factors["APOPN"][year]
    aints = factors["AINTS"][year]
    adivs = factors["ADIVS"][year]
    aschci = factors["ASCHCI"][year]
    aschcl = factors["ASCHCL"][year]
    acgns = factors["ACGNS"][year]
    atxpy = factors["ATXPY"][year]
    aschei = factors["ASCHEI"][year]
    aschel = factors["ASCHEL"][year]
    asocsec = factors["ASOCSEC"][year]
    apopsnr = factors["APOPSNR"][year]
    aucomp = factors["AUCOMP"][year]
    awage = factors["AWAGE"][year]

    year = str(year)
    rhs_vars = {}

    rhs_vars["single_returns"] = targets[year]["Single"] - single_returns.sum()
    rhs_vars["joint_returns"] = targets[year]["Joint"] - joint_returns.sum()
    rhs_vars["hh_returns"] = targets[year]["HH"] - hh_returns.sum()
    target_name = "SS_return"
    rhs_vars["returns_w_ss"] = targets[year][target_name] - returns_w_ss.sum()
    target_name = "Dep_return"
    rhs_vars["dep_exemptions"] = targets[year][target_name] - dep_exemptions.sum()
    rhs_vars["interest"] = target(targets[year]["INTS"], apopn, aints, interest.sum())
    rhs_vars["dividend"] = target(targets[year]["DIVS"], apopn, adivs, dividend.sum())
    rhs_vars["biz_income"] = target(
        targets[year]["SCHCI"], apopn, aschci, biz_income.sum()
    )
    rhs_vars["biz_loss"] = target(targets[year]["SCHCL"], apopn, aschcl, biz_loss.sum())
    rhs_vars["cap_gain"] = target(targets[year]["CGNS"], apopn, acgns, cap_gain.sum())
    rhs_vars["pension"] = target(targets[year]["Pension"], apopn, atxpy, pension.sum())
    rhs_vars["sch_e_income"] = target(
        targets[year]["SCHEI"], apopn, aschei, sch_e_income.sum()
    )
    rhs_vars["sch_e_loss"] = target(
        targets[year]["SCHEL"], apopn, aschel, sch_e_loss.sum()
    )
    rhs_vars["ss_income"] = target(
        targets[year]["SS"], apopsnr, asocsec, ss_income.sum()
    )
    rhs_vars["ucomp"] = target(targets[year]["UCOMP"], apopn, aucomp, ucomp.sum())
    rhs_vars["wage1"] = target(targets[year]["wage1"], apopn, awage, wage1.sum())
    rhs_vars["wage2"] = target(targets[year]["wage2"], apopn, awage, wage2.sum())
    rhs_vars["wage3"] = target(targets[year]["wage3"], apopn, awage, wage3.sum())
    rhs_vars["wage4"] = target(targets[year]["wage4"], apopn, awage, wage4.sum())
    rhs_vars["wage5"] = target(targets[year]["wage5"], apopn, awage, wage5.sum())
    rhs_vars["wage6"] = target(targets[year]["wage6"], apopn, awage, wage6.sum())
    rhs_vars["wage7"] = target(targets[year]["wage7"], apopn, awage, wage7.sum())
    rhs_vars["wage8"] = target(targets[year]["wage8"], apopn, awage, wage8.sum())

    model_vars = [
        "single_returns",
        "joint_returns",
        "returns_w_ss",
        "dep_exemptions",
        "interest",
        "biz_income",
        "pension",
        "ss_income",
        "wage1",
        "wage2",
        "wage3",
        "wage4",
        "wage5",
        "wage6",
        "wage7",
        "wage8",
    ]

    vstack_vars = []
    b = []  # list to hold the targets
    for var in model_vars:
        vstack_vars.append(lhs_vars[var])
        t = rhs_vars[var]
        b.append(t)

    vstack_vars = tuple(vstack_vars)
    one_half_lhs = np.vstack(vstack_vars)

    # coefficients for r and s
    A1 = np.array(one_half_lhs)
    A2 = np.array(-one_half_lhs)

    # save arrays as .npz files
    np.savez(str(str(year) + "_input.npz"), A1=A1, A2=A2, b=b)
