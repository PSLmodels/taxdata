import os
import copy
import numpy as np
import pandas as pd


CUR_PATH = os.path.abspath(os.path.dirname(__file__))
start_year = 2011
end_year = 2033


def adjustment(agi, var, var_name, target, weights, blowup):
    """
    Parameters
    ----------
    agi: AGI provided in PUF
    var: variable being adjusted
    var_name: three letter code to identify variable being adjusted
    target: target bin levels
    weights: integer*100 weights dataframe
    blowup: blowup factors created in Stage 1 of the extrapolation process

    Returns
    -------
    DataFrame of adjustment ratios for each year for that variable
    """

    # Make a copy of the variable and use to create target totals
    var_copy = copy.copy(var)
    goal_total = pd.DataFrame()
    for year in range(start_year, end_year + 1):
        wt_year = "WT{}".format(year)
        s006 = weights[wt_year] * 0.01
        var_copy *= blowup[year]
        total = (var_copy * s006).sum()
        goal_total[year] = [total]

    # Create DataFrame with the goal distribution for each year
    distribution = pd.DataFrame()
    for year in range(start_year, 2015):
        distribution[year] = target[str(year)] / target[str(year)].sum()
    # Use 2014 distribution for all future years
    for year in range(2015, end_year + 1):
        distribution[year] = distribution[2014]

    # Advance variable to 2011 level
    var *= blowup[start_year]

    # In each year find the ratios to get the correct distribution
    ratios_df = pd.DataFrame()
    for year in range(start_year, end_year + 1):
        goal_amts = goal_total[year][0] * distribution[year]

        wt_year = "WT{}".format(year)
        s006 = weights[wt_year] * 0.01
        var = var * blowup[year]
        # Find current total in each bin
        bin_0 = np.where(agi < 0, var * s006, 0).sum()
        bin_1 = np.where((agi >= 0) & (agi < 5000), var * s006, 0).sum()
        bin_2 = np.where((agi >= 5000) & (agi < 10000), var * s006, 0).sum()
        bin_3 = np.where((agi >= 10000) & (agi < 15000), var * s006, 0).sum()
        bin_4 = np.where((agi >= 15000) & (agi < 20000), var * s006, 0).sum()
        bin_5 = np.where((agi >= 20000) & (agi < 25000), var * s006, 0).sum()
        bin_6 = np.where((agi >= 25000) & (agi < 30000), var * s006, 0).sum()
        bin_7 = np.where((agi >= 30000) & (agi < 40000), var * s006, 0).sum()
        bin_8 = np.where((agi >= 40000) & (agi < 50000), var * s006, 0).sum()
        bin_9 = np.where((agi >= 50000) & (agi < 75000), var * s006, 0).sum()
        bin_10 = np.where((agi >= 75000) & (agi < 100000), var * s006, 0).sum()
        bin_11 = np.where((agi >= 100000) & (agi < 200000), var * s006, 0).sum()
        bin_12 = np.where((agi >= 200000) & (agi < 500000), var * s006, 0).sum()
        bin_13 = np.where((agi >= 500000) & (agi < 1e6), var * s006, 0).sum()
        bin_14 = np.where((agi >= 1e6) & (agi < 1.5e6), var * s006, 0).sum()
        bin_15 = np.where((agi >= 1.5e6) & (agi < 2e6), var * s006, 0).sum()
        bin_16 = np.where((agi >= 2e6) & (agi < 5e6), var * s006, 0).sum()
        bin_17 = np.where((agi >= 5e6) & (agi < 1e7), var * s006, 0).sum()
        bin_18 = np.where((agi >= 1e7), var * s006, 0).sum()
        # Create series holding each of the current totals
        actual_amts = pd.Series(
            [
                bin_0,
                bin_1,
                bin_2,
                bin_3,
                bin_4,
                bin_5,
                bin_6,
                bin_7,
                bin_8,
                bin_9,
                bin_10,
                bin_11,
                bin_12,
                bin_13,
                bin_14,
                bin_15,
                bin_16,
                bin_17,
                bin_18,
            ],
            index=goal_amts.index,
        )

        ratios_index = [num for num in range(0, 19)]

        # Find ratios for each AGI bin
        ratios = pd.Series(goal_amts / actual_amts)
        ratios.index = ratios_index

        var[agi < 0] *= ratios[0]
        var[(agi >= 0) & (agi < 5000)] *= ratios[1]
        var[(agi >= 5000) & (agi < 10000)] *= ratios[2]
        var[(agi >= 10000) & (agi < 15000)] *= ratios[3]
        var[(agi >= 15000) & (agi < 20000)] *= ratios[4]
        var[(agi >= 20000) & (agi < 25000)] *= ratios[5]
        var[(agi >= 25000) & (agi < 30000)] *= ratios[6]
        var[(agi >= 30000) & (agi < 40000)] *= ratios[7]
        var[(agi >= 40000) & (agi < 50000)] *= ratios[8]
        var[(agi >= 50000) & (agi < 75000)] *= ratios[9]
        var[(agi >= 75000) & (agi < 100000)] *= ratios[10]
        var[(agi >= 100000) & (agi < 200000)] *= ratios[11]
        var[(agi >= 200000) & (agi < 500000)] *= ratios[12]
        var[(agi >= 500000) & (agi < 1e6)] *= ratios[13]
        var[(agi >= 1e6) & (agi < 1.5e6)] *= ratios[14]
        var[(agi >= 1.5e6) & (agi < 2e6)] *= ratios[15]
        var[(agi >= 2e6) & (agi < 5e6)] *= ratios[16]
        var[(agi >= 5e6) & (agi < 1e7)] *= ratios[17]
        var[(agi >= 1e7)] *= ratios[18]

        ratios_df["{}{}".format(var_name, year)] = ratios

    return ratios_df


# Read all necessary files
puf = pd.read_csv(os.path.join(CUR_PATH, "../data/cps-matched-puf.csv"))
targets = pd.read_csv(os.path.join(CUR_PATH, "stage3_targets.csv"), index_col=0)
wght = pd.read_csv(os.path.join(CUR_PATH, "../puf_stage2/puf_weights.csv.gz"))
bf = pd.read_csv(os.path.join(CUR_PATH, "../puf_stage1/growfactors.csv"), index_col=0)

# Call adjustment function for each variable being adjusted
ints = adjustment(puf.e00100, puf.e00300, "INT", targets, wght, bf.AINTS)

# Concat each variable's ratios to the final DataFrame and set index name
var_ratios_list = [ints]
final_ratios = pd.concat(var_ratios_list, axis=1)
final_ratios = final_ratios.transpose()

# Create CSV from the final ratios
ratios_path = os.path.join(CUR_PATH, "puf_ratios.csv")
final_ratios.to_csv(ratios_path, float_format="%.4f", index_label="agi_bin")
