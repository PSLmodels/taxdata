import pandas as pd
import numpy as np
import os
from copy import deepcopy


class Benefits():
    GROWTH_RATES_PATH = 'growth_rates.csv'
    CPS_BENEFIT_PATH = '../cps_data/cps_raw.csv.gz'
    CPS_WEIGHTS_PATH = '../cps_stage2/cps_weights.csv.gz'

    def __init__(self,
                 growth_rates=GROWTH_RATES_PATH,
                 cps_benefit=CPS_BENEFIT_PATH,
                 cps_weights=CPS_WEIGHTS_PATH,
                 benefit_names=["ssi", "medicaid", "medicare",
                                "vb", "snap", "ss"]):
        benefit_names = [bn.lower() for bn in benefit_names]
        self._read_data(growth_rates, cps_benefit, cps_weights,
                        benefit_names=benefit_names)
        self.current_year = 2014
        self.benefit_names = benefit_names


    def increment_year(self, tol=0.01):
        self.current_year += 1
        print("starting year", self.current_year)
        WT = self.WT.loc[:, 'WT'+str(self.current_year)] * 0.01
        for benefit in self.benefit_names:
            participant_targets = getattr(self, "{}_participant_targets".format(benefit))
            benefit_targets = getattr(self, "{}_benefit_targets".format(benefit))
            # base_participation = getattr(self, "{}_base_participation".format(benefit))
            participation = getattr(self, "{}_participation".format(benefit))
            benefits = getattr(self, "{}_benefits".format(benefit))
            prob = getattr(self, "{}_prob".format(benefit))

            diff = participant_targets[self.current_year] - \
                (participation.sum(axis=1) * WT).sum()
            if abs(diff)/participant_targets[self.current_year] > tol:
                participation, benefits = \
                    self._extrapolate(WT,
                                      participation.copy(deep=True),
                                      benefits.copy(deep=True),
                                      prob,
                                      participant_targets[self.current_year],
                                      tol=tol)
            extrapolated = (participation.sum(axis=1) * WT).sum()
            print(benefit, 'this year total is ', extrapolated,
                  ', target is ', participant_targets[self.current_year],
                  ', diff is ',
                  (extrapolated - participant_targets[self.current_year]), ',',
                  ((extrapolated - participant_targets[self.current_year]) /
                   participant_targets[self.current_year]))

            lab = benefit + '_recipients_' + str(self.current_year)
            self.benefit_extrapolation[lab] = participation.sum(axis=1)

            total_current_benefits = (benefits.sum(axis=1) * WT).sum()
            lab = benefit + '_benefits_' + str(self.current_year)
            self.benefit_extrapolation[lab] = \
                (benefits.sum(axis=1) *
                 benefit_targets[self.current_year] / total_current_benefits)

            setattr(self, '{}_participation'.format(benefit), participation)
            setattr(self, '{}_benefits'.format(benefit), benefits)


    @staticmethod
    def _extrapolate(WT, I, benefits, prob, target, tol=0.01, J=15):
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
        extrap_df = Benefits._ravel_data(WT.copy(),
                                         I.copy(),
                                         benefits.copy(),
                                         prob.copy())
        receives = extrap_df.loc[extrap_df.I > 0, ]
        avg_benefit = receives.benefits_wt.sum() / receives.I_wt.sum()

        actual = extrap_df.I_wt.sum()
        diff = actual - target
        if diff < 0:
            remove = False
            candidates = extrap_df.loc[extrap_df.I == 0, ].copy()
            # set everyone as a participant and then remove surplus below
            # this is necassary since I * wt will all be zeroes
            candidates.loc[:, "I"] = np.ones(len(candidates))
            candidates.loc[:, "I_wt"] = candidates.I * candidates.WT
            noncandidates = extrap_df.loc[extrap_df.I == 1, ]
        else:
            remove = True
            candidates = extrap_df.loc[extrap_df.I == 1, ]
            noncandidates = extrap_df.loc[extrap_df.I == 0, ]
        noncan_part = noncandidates.I_wt.sum()
        del extrap_df
        # sort by probability of getting benefits in descending order
        # of prob so that we only keep those with highest prob of
        # receiving benefits in the future
        candidates.sort_values(by="prob", ascending=False, inplace=True)
        # create index based on new ordering for idxmin operation below
        candidates.reset_index(drop=True, inplace=True)
        # create running sum of weighted participants
        candidates["cum_participants"] = candidates.I_wt.cumsum() + noncan_part
        # get absolute difference between candidates and target
        candidates["abs_diff"] = np.abs(candidates.cum_participants -
                                        target)

        # get index of minimum absolute difference
        min_diff = candidates.abs_diff.idxmin()

        # # check to make results are close enough
        assert np.allclose(candidates.iloc[min_diff].cum_participants, target,
                           atol=0.0, rtol=tol)

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
            candidates.loc[(candidates.I == 1) &
                           (candidates.benefits == 0), 'benefits'] = avg_benefit

        result = pd.concat([noncandidates, candidates], axis=0, ignore_index=True)
        del candidates
        del noncandidates
        result.sort_values(by=["i", "j"], inplace=True)
        wt_ravel = Benefits._repeating_ravel((len(WT), J),
                                                          apply_to=np.array(WT))

        result.I_wt = result.I * wt_ravel

        I = Benefits._unravel_data(result, "I", I.columns.tolist(),
                                               dtype=np.int64)
        benefits = Benefits._unravel_data(result, "benefits",
                                                      benefits.columns.tolist(),
                                                      dtype=np.float64)

        return I, benefits

    @staticmethod
    def _unravel_data(df, var_name, column_names, dtype=None):
        # dataframe df should already be sorted by i and j in extrapolate
        # df.sort_values(by=["i", "j"], inplace=True)

        var = df[var_name].values
        max_i = int(df.i.max()) + 1
        max_j = int(df.j.max()) + 1
        var = var.reshape(max_i, max_j)

        df = pd.DataFrame(var, columns=column_names, dtype=dtype)

        return df

    @staticmethod
    def _repeating_ravel(shape, apply_to=None):
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

    @staticmethod
    def _ravel_data(WT, I, benefits, prob):
        wt_arr = np.array(WT)
        I_arr = np.array(I)
        benefits_arr = np.array(benefits)
        prob_arr = np.array(prob)

        I_wt = (wt_arr * I_arr.T).T
        benefits_wt = (wt_arr * benefits_arr.T).T
        # ben_wt = (wt_arr)
        wt_rav = Benefits._repeating_ravel(I_arr.shape, apply_to=wt_arr)

        # create indices
        i = Benefits._repeating_ravel(I_arr.shape)
        j = i % I_arr.shape[1]

        # stack and create data frame with all individuals
        extrap_arr = np.vstack((prob_arr.ravel(), I_arr.ravel(), I_wt.ravel(),
                                wt_rav, benefits_arr.ravel(),
                                benefits_wt.ravel(), i, j)).T
        extrap_df = pd.DataFrame(extrap_arr,
                                 columns=["prob", "I", "I_wt", "WT",
                                          "benefits", "benefits_wt", "i", "j"])

        return extrap_df


    def _read_data(self, growth_rates, cps_benefit, cps_weights,
                   cps=None, benefit_names=[]):
        """
        prepare data
        """
        cps_benefit = pd.read_csv(cps_benefit)

        if isinstance(cps_weights, str):
            assert(os.path.exists(cps_weights))
            cps_weights = pd.read_csv(cps_weights)
        else:
            assert(isinstance(cps_weights, pd.DataFrame))
        self.WT = cps_weights
        growth_rates = pd.read_csv(growth_rates, index_col=0)
        benefit_extrapolation = pd.DataFrame()
        for benefit in benefit_names:

            # create benefit targets
            benefit_2014 = (cps_benefit[benefit + '_ben'] * cps_benefit.s006).sum()
            benefit_targets = benefit_2014 * (1 + growth_rates['{0}_benefit_growth'
                                                               .format(benefit)])
            benefit_targets = benefit_targets[1:]

            # extract program benefit in 2014 to base_benefits array
            base_benefits_col = [col for col in list(cps_benefit) if
                                 col.startswith('{0}_VAL'.format(benefit.upper()))]
            base_benefits = cps_benefit[base_benefits_col]

            # Create Participation targets from tax-unit individual level markers
            # and growth rates from SSA
            base_participation = pd.DataFrame(np.where(base_benefits > 0, 1, 0))
            # print(benefit,'value_counts baseline')
            # print(base_participation.sum(axis=1).value_counts())
            total_particpants = (base_participation.sum(axis=1) *
                                 cps_benefit.s006).sum()
            participant_targets = total_particpants * \
                (1 + growth_rates['{0}_participation_growth'.format(benefit)])
            # extract probability of participation in program from tax-unit database
            prob_col = [col for col in list(cps_benefit)
                        if col.startswith('{0}_PROB'.format(benefit.upper()))]
            prob = cps_benefit[prob_col]

            # dataframe of number participants and total benefits from program
            benefit_extrapolation['{}_recipients_2014'.format(benefit)] = base_participation.sum(axis=1)
            benefit_extrapolation['{}_benefits_2014'.format(benefit)] = cps_benefit[benefit + '_ben']

            setattr(self, '{}_prob'.format(benefit), prob)
            setattr(self, '{}_base_participation'.format(benefit), base_participation)
            setattr(self, '{}_base_benefits'.format(benefit), base_benefits)
            setattr(self, '{}_participant_targets'.format(benefit), participant_targets)
            setattr(self, '{}_benefit_targets'.format(benefit), benefit_targets)
            setattr(self, '{}_benefit_extrapolation'.format(benefit), benefit_extrapolation)
            setattr(self, '{}_participation'.format(benefit), base_participation)
            setattr(self, '{}_benefits'.format(benefit), base_benefits)

        # add record ID
        benefit_extrapolation['RECID'] = cps_benefit['SEQUENCE']
        self.benefit_extrapolation = benefit_extrapolation


if __name__ == "__main__":
    ben = Benefits()

    for _ in range(12):
        ben.increment_year()

    # drop unnecessary variables
    drop_list = []
    for year in range(2014, 2027):
        for benefit in ben.benefit_names:
            drop_list.append('{}_recipients_{}'.format(benefit, year))
    ben.benefit_extrapolation = ben.benefit_extrapolation.drop(drop_list,
                                                               axis=1)
    # drop records with no benefits
    col_list = ben.benefit_extrapolation.columns
    mask = ben.benefit_extrapolation.loc[:, col_list != 'RECID'].sum(1)
    ben.benefit_extrapolation = deepcopy(ben.benefit_extrapolation[mask != 0])

    ben.benefit_extrapolation.to_csv("cps_benefits_extrap.csv.gz", index=False,
                                     compression="gzip")



    # ravel_test(indicator, benefits, prob, CPS_weights)
