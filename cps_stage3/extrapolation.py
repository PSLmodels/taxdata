import pandas as pd
import numpy as np
import copy


def ravel_test(indicator, benefits, prob, CPS_weights):

    wt = CPS_weights.loc[:, 'WT'+str("2015")]

    extrap_df = ravel_data(wt.copy(), indicator.copy(),
                           benefits.copy(), prob.copy())
    extrap_df.sort_values(by=["i", "j"], inplace=True)

    I_unrav = unravel_data(extrap_df, "I",
                           indicator.columns.tolist(),
                           dtype=np.int64)
    benefits_unrav = unravel_data(extrap_df, "benefits",
                                  benefits.columns.tolist(),
                                  dtype=np.float64)
    prob_unrav = unravel_data(extrap_df, "prob",
                              prob.columns.tolist(),
                              dtype=np.float64)

    pd.testing.assert_frame_equal(indicator, I_unrav, check_dtype=False)
    pd.testing.assert_frame_equal(benefits, benefits_unrav, check_dtype=False)
    pd.testing.assert_frame_equal(prob, prob_unrav, check_dtype=False)


def prepare_data(target_grates_path, CPS_tax_unit_path, CPS_weights,
                 benefit="SSI"):
    """ prepare data """
    target_grates = pd.read_csv(target_grates_path, index_col=0)
    CPS_tax_unit = pd.read_csv(CPS_tax_unit_path)

    # create benefit targets
    benefit_2014 = (CPS_tax_unit[benefit] * CPS_tax_unit.s006).sum()
    benefit_targets = benefit_2014 * (1 + target_grates['{0} Target Growth'
                                                        .format(benefit)])
    benefit_targets = benefit_targets[1:]

    # extract program benefit in 2014 to Benefit_base array
    benefit_base_col = [col for col in list(CPS_tax_unit) if
                        col.startswith('{0}_VAL'.format(benefit))]
    benefit_base = CPS_tax_unit[benefit_base_col]

    # Create Participation targets from tax-unit individual level markers
    # and growth rates from SSA
    participation_2014 = pd.DataFrame(np.where(benefit_base > 0, 1, 0))
    total_particpants = (participation_2014.sum(axis=1) *
                         CPS_tax_unit.s006).sum()
    participant_targets = total_particpants * \
        (1 + target_grates['{0} Participation Growth'.format(benefit)])

    # extract probability of participation in program from tax-unit database
    prob_col = [col for col in list(CPS_tax_unit)
                if col.startswith('{0}_PROB'.format(benefit))]
    prob_base = CPS_tax_unit[prob_col]

    # dataframe of number participants and total benefits from program
    benefit_extrapolation = pd.DataFrame(participation_2014.sum(axis=1),
                                         columns=['Parcipation_2014'])
    benefit_extrapolation['Benefit_2014'] = CPS_tax_unit[benefit]

    return (prob_base, participation_2014, benefit_base,
            participant_targets, benefit_targets, benefit_extrapolation)


def unravel_data(df, var_name, column_names, dtype=None):
    # dataframe df should already be sorted by i and j in extrapolate
    # df.sort_values(by=["i", "j"], inplace=True)

    var = df[var_name].values
    max_i = int(df.i.max()) + 1
    max_j = int(df.j.max()) + 1
    var = var.reshape(max_i, max_j)

    df = pd.DataFrame(var, columns=column_names, dtype=dtype)

    return df


def repeating_ravel(shape, apply_to=None):
    """
    test = np.array([5,6,7,8])
    repeating_ravel((4,2), apply_to=test)
    returns array([5, 5, 6, 6, 7, 7, 8, 8])
    """
    if apply_to is None:
        apply_to = np.arange(shape[0], dtype=np.int32)
    assert(isinstance(apply_to, np.ndarray))
    assert (apply_to.shape[0] == shape[0])
    i = np.tile(apply_to, shape[1])
    i = i.reshape(shape[1], shape[0])
    i = i.T.ravel()
    return i


def ravel_data(wt, I, benefits, prob):
    wt_arr = np.array(wt)
    I_arr = np.array(I)
    benefits_arr = np.array(benefits)
    prob_arr = np.array(prob)

    I_wt = (wt_arr * I_arr.T).T

    # create indices
    i = repeating_ravel(I_arr.shape)
    j = i % I_arr.shape[1]

    # stack and create data frame with all individuals
    extrap_arr = np.vstack((prob_arr.ravel(), I_arr.ravel(), I_wt.ravel(),
                            benefits_arr.ravel(), i, j)).T
    extrap_df = pd.DataFrame(extrap_arr,
                             columns=["prob", "I", "I_wt", "benefits",
                                      "i", "j"])

    return extrap_df


def extrapolate(wt, I, benefits, prob, target):
    """
    Goal: get number of participants as close to target as possible
    Steps:
        1. Data is currently in N x 15 shape. Reshape it to be
            N * 15 dim vector
        2. Determine if adding or removing
            if adding, only consider those who are not receiving benefits
            if removing, only consider those who are receiving benefits
        2. Sort in descending order of probability of receiving
            benefits in the future
        3. Calculate cumulative sum over all participants
        4. Find index where minimum absolute difference between
            cum. sum and target is minimized
        5. All those with index <= minimimizing index receive benefits
            and all those with index > minimizing index do not
        6. Stack dataframes, unravel (go back to N x 15 dim), return result

        Note: Unraveling is done by keeping track of each individual's
            location in the matrix (i, j).  Sorting by i and then j gives
            us a vector of tuples (1,1), (1,2),...,(1,15),(2,1),(2,2),
            ...,(N,15). Then by reshaping to n rows, 15 columns we
            get the same matrix that we started with but with the
            updated values
    """

    extrap_df = ravel_data(wt.copy(), I.copy(), benefits.copy(), prob.copy())

    actual = extrap_df.I_wt.sum()
    diff = actual - target
    if diff < 0:
        remove = False
        candidates = extrap_df.loc[extrap_df.I == 0, ]
        noncandidates = extrap_df.loc[extrap_df.I == 1, ]
    else:
        remove = True
        candidates = extrap_df.loc[extrap_df.I == 1, ]
        noncandidates = extrap_df.loc[extrap_df.I == 0, ]
    del extrap_df
    # sort by probability of getting benefits in descending order
    # of prob so that we only keep those with highest prob of
    # receiving benefits in the future
    candidates.sort_values(by="prob", ascending=False, inplace=True)
    # create index based on new ordering for idxmin operation below
    candidates.reset_index(drop=True, inplace=True)
    # create running sum of weighted participants
    candidates["cum_participants"] = candidates.I_wt.cumsum()
    # get absolute difference between candidates and target
    candidates["abs_diff"] = np.abs(candidates.cum_participants -
                                    abs(target))

    # get index of minimum absolute difference
    min_diff = candidates.abs_diff.idxmin()

    # check to make sure difference is less than 1000
    # TODO: justify using 1000 or pick other number/method
    assert(candidates.iloc[min_diff].abs_diff < 1000)

    # individuals prior to min_diff have highest probability of getting
    # benefits in the future ==> they get benefits
    candidates.iloc[:min_diff, candidates.columns.get_loc("I")] = 1
    candidates.iloc[(min_diff + 1):, candidates.columns.get_loc("I")] = 0
    candidates.iloc[(min_diff + 1):,
                    candidates.columns.get_loc("prob")] = 10000

    if remove:
        candidates.loc[(min_diff + 1):, 'benefits'] = 0
    else:
        # all added candidates have indicator 1 but no benefits
        avg_benefit = target/(candidates.I_wt.sum() + noncandidates.I_wt.sum())
        candidates.loc[(candidates.I == 1) &
                       (candidates.benefits == 0), 'benefits'] = avg_benefit

    result = pd.concat([noncandidates, candidates], axis=0, ignore_index=True)
    del candidates
    del noncandidates
    result.sort_values(by=["i", "j"], inplace=True)
    wt_ravel = repeating_ravel((len(wt), 15), apply_to=np.array(wt))

    result.I_wt = result.I * wt_ravel

    I = unravel_data(result, "I", I.columns.tolist(), dtype=np.int64)
    benefits = unravel_data(result, "benefits", benefits.columns.tolist(),
                            dtype=np.float64)
    prob = unravel_data(result, "prob", prob.columns.tolist(),
                        dtype=np.float64)

    return I, benefits, prob


def run(indicator, benefits, prob, CPS_weights, participant_targets,
        benefit_targets, benefit_extrapolation):
    prior_year_indicator = copy.deepcopy(indicator)
    prior_year_benefits = copy.deepcopy(benefits)
    prior_year_prob = copy.deepcopy(prob)
    for year in benefit_targets.index:
        diff = participant_targets[year] - \
            (indicator.sum(axis=1) * CPS_weights['WT'+str(year)]).sum()
        if abs(diff) <= 1000:
            print('The differece of participants is neglegible')
        else:
            if diff > 0:
                print('Need to impute more participants')
            else:
                print('Need to remove current participants')

            wt = CPS_weights.loc[:, 'WT'+str(year)]
            indicator, benefits, prob = extrapolate(wt, prior_year_indicator,
                                                    prior_year_benefits,
                                                    prior_year_prob,
                                                    participant_targets[year])
        print('Done with year ', year)
        extrapolated = (indicator.sum(axis=1) *
                        CPS_weights['WT'+str(year)]).sum()
        print('this year total is ', extrapolated,
              'while target is ', participant_targets[year],
              'thus diff is ',
              (extrapolated - participant_targets[year]))

        benefit_extrapolation['Participation_'+str(year)] = \
            indicator.sum(axis=1)
        sum_this_year = (benefits.sum(axis=1) *
                         CPS_weights['WT'+str(year)]).sum()
        benefit_extrapolation['Benefit_'+str(year)] = \
            benefits.sum(axis=1) * benefit_targets[year] / sum_this_year

        prior_year_indicator = indicator.copy()
        prior_year_benefits = benefits.copy()
        prior_year_prob = prob.copy()

    return (prior_year_indicator, prior_year_prob, prior_year_benefits,
            benefit_extrapolation)


if __name__ == "__main__":

    CPS_weights = pd.read_csv('cps_weights.csv')

    benefits = {"SSI": {"grates_path": "GrowthRates.csv",
                        "cps_tax_units_path": "cps_ssi.csv"}
                }

    for benefit in benefits:
        (prob, indicator, benefits, participant_targets, benefit_targets,
            benefit_extrapolation) = \
                prepare_data(benefits[benefit]["grates_path"],
                             benefits[benefit]["cps_tax_units_path"],
                             CPS_weights,
                             benefit=benefit)

        """extrapolate"""

        indicator, prob, benefits, benefit_extrapolation = \
            run(indicator, benefits, prob,
                CPS_weights, participant_targets,
                benefit_targets,
                benefit_extrapolation)

    # ravel_test(indicator, benefits, prob, CPS_weights)
