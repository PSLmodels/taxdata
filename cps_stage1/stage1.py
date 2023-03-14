import pandas as pd
import os

CUR_PATH = os.path.abspath(os.path.dirname(__file__))


def main(syr=2014):
    SYR = str(syr)  # Start year of CPS
    EYR = 2033  # Last year in our extrapolation

    # Read in state SOI estimates
    soi_estimates = pd.read_csv(
        os.path.join(CUR_PATH, "SOI_estimates.csv"), index_col=0
    )
    stage2_path = os.path.join(CUR_PATH, "../puf_stage1/Stage_II_targets.csv")
    stage_2_targets = pd.read_csv(stage2_path, index_col=0)
    stage_2_targets.drop(["2011", "2012", "2013"], inplace=True, axis=1)
    factors_path = os.path.join(CUR_PATH, "../puf_stage1/Stage_I_factors.csv")
    factors = pd.read_csv(factors_path, index_col=0)

    for year in range(int(SYR) + 1, EYR + 1):
        single = soi_estimates[SYR]["Single"] * factors["ARETS"][year]
        joint = soi_estimates[SYR]["Joint"] * factors["ARETS"][year]
        hh = soi_estimates[SYR]["HH"] * factors["ARETS"][year]
        ss_return = soi_estimates[SYR]["SS_return"] * factors["APOPSNR"][year]
        dep_return = soi_estimates[SYR]["Dep_return"] * factors["APOPN"][year]
        ints = soi_estimates[SYR]["INTS"] * factors["AINTS"][year]
        divs = soi_estimates[SYR]["DIVS"] * factors["ADIVS"][year]
        schci = soi_estimates[SYR]["SCHCI"] * factors["ASCHCI"][year]
        schcl = soi_estimates[SYR]["SCHCL"] * factors["ASCHCL"][year]
        cgns = soi_estimates[SYR]["CGNS"] * factors["ACGNS"][year]
        pension = soi_estimates[SYR]["Pension"] * factors["ATXPY"][year]
        schei = soi_estimates[SYR]["SCHEI"] * factors["ASCHEI"][year]
        schel = soi_estimates[SYR]["SCHEL"] * factors["ASCHEL"][year]
        ss = soi_estimates[SYR]["SS"] * factors["ASOCSEC"][year]
        ucomp = soi_estimates[SYR]["UCOMP"] * factors["AUCOMP"][year]
        wage1 = soi_estimates[SYR]["wage1"] * factors["AWAGE"][year]
        wage2 = soi_estimates[SYR]["wage2"] * factors["AWAGE"][year]
        wage3 = soi_estimates[SYR]["wage3"] * factors["AWAGE"][year]
        wage4 = soi_estimates[SYR]["wage4"] * factors["AWAGE"][year]
        wage5 = soi_estimates[SYR]["wage5"] * factors["AWAGE"][year]
        wage6 = soi_estimates[SYR]["wage6"] * factors["AWAGE"][year]
        wage7 = soi_estimates[SYR]["wage7"] * factors["AWAGE"][year]
        wage8 = soi_estimates[SYR]["wage8"] * factors["AWAGE"][year]

        current_year = pd.Series(
            [
                single,
                joint,
                hh,
                ss_return,
                dep_return,
                ints,
                divs,
                schci,
                schcl,
                cgns,
                pension,
                schei,
                schel,
                ss,
                ucomp,
                wage1,
                wage2,
                wage3,
                wage4,
                wage5,
                wage6,
                wage7,
                wage8,
            ],
            index=soi_estimates.index,
        )
        soi_estimates[year] = current_year

    soi_estimates.to_csv(
        os.path.join(CUR_PATH, "stage_2_targets.csv"), float_format="%.0f"
    )


if __name__ == "__main__":
    main()
