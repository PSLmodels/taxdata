import copy
import numpy as np
import pandas as pd


def adjustment(agi, var, var_name, target, weight, blowup):
    """
    Parameters
    ----------
    agi: AGI provided in PUF
    var: Variable being adjusted
    var_name: Three letter code to identify variable being adjusted
    target: Target bin levels
    weight: Weights file
    blowup: Blowup factors created in Stage 1 of the extrapolation process

    Returns
    -------
    DataFrame of adjustment ratios for each year for that variable
    """

    # Make a copy of the variable and use to create target totals
    var_copy = copy.copy(var)
    goal_total = pd.DataFrame()
    for year in range(2009, 2027):
        wt_year = 'WT{}'.format(year)
        s006 = weight[wt_year] * 0.01
        var_copy *= blowup[year]
        total = (var_copy * s006).sum()
        goal_total[year] = [total]

    # Create DataFrame with the goal distribution for each year
    distribution = pd.DataFrame()
    for year in range(2009, 2015):
        distribution[year] = target[str(year)] / target[str(year)].sum()
    # Use 2014 distribution for all future years
    for year in range(2015, 2027):
        distribution[year] = distribution[2014]

    # Advance variable to 2009 level
    var *= blowup[2009]

    # In each year find the ratios to get the correct distribution
    ratios_df = pd.DataFrame()
    for year in range(2010, 2027):

        goal_amts = goal_total[year][0] * distribution[year]

        wt_year = 'WT{}'.format(year)
        s006 = weight[wt_year] * 0.01
        var = var * blowup[year]
        # Find current total in each bin
        bin_0 = np.where(agi < 0,
                         var * s006, 0).sum()
        bin_1 = np.where((agi >= 0) & (agi < 5000),
                         var * s006, 0).sum()
        bin_2 = np.where((agi >= 5000) & (agi < 10000),
                         var * s006, 0).sum()
        bin_3 = np.where((agi >= 10000) & (agi < 15000),
                         var * s006, 0).sum()
        bin_4 = np.where((agi >= 15000) & (agi < 20000),
                         var * s006, 0).sum()
        bin_5 = np.where((agi >= 20000) & (agi < 25000),
                         var * s006, 0).sum()
        bin_6 = np.where((agi >= 25000) & (agi < 30000),
                         var * s006, 0).sum()
        bin_7 = np.where((agi >= 30000) & (agi < 40000),
                         var * s006, 0).sum()
        bin_8 = np.where((agi >= 40000) & (agi < 50000),
                         var * s006, 0).sum()
        bin_9 = np.where((agi >= 50000) & (agi < 75000),
                         var * s006, 0).sum()
        bin_10 = np.where((agi >= 75000) & (agi < 100000),
                          var * s006, 0).sum()
        bin_11 = np.where((agi >= 100000) & (agi < 200000),
                          var * s006, 0).sum()
        bin_12 = np.where((agi >= 200000) & (agi < 500000),
                          var * s006, 0).sum()
        bin_13 = np.where((agi >= 500000) & (agi < 1e6),
                          var * s006, 0).sum()
        bin_14 = np.where((agi >= 1e6) & (agi < 1.5e6),
                          var * s006, 0).sum()
        bin_15 = np.where((agi >= 1.5e6) & (agi < 2e6),
                          var * s006, 0).sum()
        bin_16 = np.where((agi >= 2e6) & (agi < 5e6),
                          var * s006, 0).sum()
        bin_17 = np.where((agi >= 5e6) & (agi < 1e7),
                          var * s006, 0).sum()
        bin_18 = np.where((agi >= 1e7),
                          var * s006, 0).sum()
        # Create series holding each of the current totals
        actual_amts = pd.Series([bin_0, bin_1, bin_2, bin_3, bin_4, bin_5,
                                 bin_6, bin_7, bin_8, bin_9, bin_10, bin_11,
                                 bin_12, bin_13, bin_14, bin_15, bin_16,
                                 bin_17, bin_18],
                                index=goal_amts.index)

        ratios_index = ['BIN_0', 'BIN_1', 'BIN_2', 'BIN_3', 'BIN_4', 'BIN_5',
                        'BIN_6', 'BIN_7', 'BIN_8', 'BIN_9', 'BIN_10',
                        'BIN_11', 'BIN_12', 'BIN_13', 'BIN_14', 'BIN_15',
                        'BIN_16', 'BIN_17', 'BIN_18']

        # Find ratios for each AGI bin
        ratios = pd.Series(goal_amts / actual_amts)
        ratios.index = ratios_index

        var[agi < 0] *= ratios['BIN_0']
        var[(agi >= 0) & (agi < 5000)] *= ratios['BIN_1']
        var[(agi >= 5000) & (agi < 10000)] *= ratios['BIN_2']
        var[(agi >= 10000) & (agi < 15000)] *= ratios['BIN_3']
        var[(agi >= 15000) & (agi < 20000)] *= ratios['BIN_4']
        var[(agi >= 20000) & (agi < 25000)] *= ratios['BIN_5']
        var[(agi >= 25000) & (agi < 30000)] *= ratios['BIN_6']
        var[(agi >= 30000) & (agi < 40000)] *= ratios['BIN_7']
        var[(agi >= 40000) & (agi < 50000)] *= ratios['BIN_8']
        var[(agi >= 50000) & (agi < 75000)] *= ratios['BIN_9']
        var[(agi >= 75000) & (agi < 100000)] *= ratios['BIN_10']
        var[(agi >= 100000) & (agi < 200000)] *= ratios['BIN_11']
        var[(agi >= 200000) & (agi < 500000)] *= ratios['BIN_12']
        var[(agi >= 500000) & (agi < 1e6)] *= ratios['BIN_13']
        var[(agi >= 1e6) & (agi < 1.5e6)] *= ratios['BIN_14']
        var[(agi >= 1.5e6) & (agi < 2e6)] *= ratios['BIN_15']
        var[(agi >= 2e6) & (agi < 5e6)] *= ratios['BIN_16']
        var[(agi >= 5e6) & (agi < 1e7)] *= ratios['BIN_17']
        var[(agi >= 1e7)] *= ratios['BIN_18']
        ratios_df['{}{}'.format(var_name, year)] = ratios

    return ratios_df

# Read all necessary files
puf = pd.read_csv('../puf_data/cps-matched-puf.csv')
targets = pd.read_csv('stage3_targets.csv', index_col=0)
wght = pd.read_csv('../puf_stage2/puf_weights.csv')
bf = pd.read_csv('../stage1/growfactors.csv', index_col=0)

# Call adjustment function with each variable desired
ints = adjustment(puf.e00100, puf.e00300, 'INT', targets, wght, bf.AINTS)

# Concat each variables ratios to the final DataFrame
final_ratios = pd.concat([ints], axis=1)
final_ratios = final_ratios.transpose()

# Crate CSV from the final ratios
final_ratios.to_csv('puf_ratios.csv')
