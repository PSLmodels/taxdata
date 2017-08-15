import pandas as pd
import numpy as np
import os


def ravel_test(indicator, benefits, prob, CPS_weights):

    wt = CPS_weights.loc[:, 'WT'+str("2015")]

    extrap_df = Benefits._ravel_data(wt.copy(), indicator.copy(),
                                         benefits.copy(), prob.copy())
    extrap_df.sort_values(by=["i", "j"], inplace=True)

    I_unrav = Benefits._unravel_data(extrap_df, "I",
                                                 indicator.columns.tolist(),
                                                 dtype=np.int64)
    ben_unrav = Benefits._unravel_data(extrap_df, "benefits",
                                                   benefits.columns.tolist(),
                                                   dtype=np.float64)
    prob_unrav = Benefits._unravel_data(extrap_df, "prob",
                                                    prob.columns.tolist(),
                                                    dtype=np.float64)

    pd.testing.assert_frame_equal(indicator, I_unrav, check_dtype=False)
    pd.testing.assert_frame_equal(benefits, ben_unrav, check_dtype=False)
    pd.testing.assert_frame_equal(prob, prob_unrav, check_dtype=False)


class Benefits():
    TARGET_GRATES_PATH = 'GrowthRates.csv'
    CPS_BENEFIT_PATH = 'cps_ben.csv.gz'
    CPS_WEIGHTS_PATH = 'cps_weights.csv'

    def __init__(self,
                 target_grates_path=TARGET_GRATES_PATH,
                 cps_benefit_path=CPS_BENEFIT_PATH,
                 cps_weights=CPS_WEIGHTS_PATH,
                 benefit="SSI"):
        self._read_data(target_grates_path, cps_benefit_path, cps_weights,
                        benefit=benefit)
        self.current_year = 2014

        setattr(self, 'participation', self.base_participation)
        setattr(self, 'benefits', self.base_benefits)


    def increment_year(self):
        self.current_year += 1

        WT = self.WT.loc[:, 'WT'+str(self.current_year)]

        diff = self.participant_targets[self.current_year] - \
            (self.base_participation.sum(axis=1) * WT).sum()

        if abs(diff) > 1000:
            self.participation, self.benefits = \
                self._extrapolate(WT,
                                  self.participation.copy(deep=True),
                                  self.benefits.copy(deep=True),
                                  self.prob,
                                  self.participant_targets[self.current_year])

        print('Done with year ', self.current_year)

        extrapolated = (self.participation.sum(axis=1) * WT).sum()
        print('this year total is ', extrapolated,
              'while target is ', self.participant_targets[self.current_year],
              'thus diff is ',
              (extrapolated - self.participant_targets[self.current_year]))

        lab = self.benefit_name.lower() + '_recipients_' + str(self.current_year)
        self.benefit_extrapolation[lab] = \
            self.participation.sum(axis=1)

        total_current_benefits = (self.benefits.sum(axis=1) * WT).sum()
        lab = self.benefit_name.lower() + '_benefits_' + str(self.current_year)
        self.benefit_extrapolation[lab] = \
            (self.benefits.sum(axis=1) *
             self.benefit_targets[self.current_year] / total_current_benefits)


    def _read_data(self, target_grates_path, cps_benefit_path, cps_weights,
                   cps=None, benefit="SSI"):
        """
        prepare data
        """
        target_grates = pd.read_csv(target_grates_path, index_col=0)
        cps_benefit = pd.read_csv(cps_benefit_path)

        if isinstance(cps_weights, str):
            assert(os.path.exists(cps_weights))
            cps_weights = pd.read_csv(cps_weights)
        else:
            assert(isinstance(cps_weights, pd.DataFrame))

        # create benefit targets
        benefit_2014 = (cps_benefit[benefit] * cps_benefit.s006).sum()
        benefit_targets = benefit_2014 * (1 + target_grates['{0}_target_growth'
                                                            .format(benefit.lower())])
        benefit_targets = benefit_targets[1:]

        # extract program benefit in 2014 to base_benefits array
        base_benefits_col = [col for col in list(cps_benefit) if
                             col.startswith('{0}_VAL'.format(benefit))]
        base_benefits = cps_benefit[base_benefits_col]

        # Create Participation targets from tax-unit individual level markers
        # and growth rates from SSA
        base_participation = pd.DataFrame(np.where(base_benefits > 0, 1, 0))
        total_particpants = (base_participation.sum(axis=1) *
                             cps_benefit.s006).sum()
        participant_targets = total_particpants * \
            (1 + target_grates['{0}_participation_growth'.format(benefit.lower())])

        # extract probability of participation in program from tax-unit database
        prob_col = [col for col in list(cps_benefit)
                    if col.startswith('{0}_PROB'.format(benefit))]
        prob = cps_benefit[prob_col]

        # dataframe of number participants and total benefits from program
        benefit_extrapolation = pd.DataFrame(base_participation.sum(axis=1),
                                             columns=['{}_recipients_2014'.format(benefit.lower())])
        benefit_extrapolation['{}_benefits_2014'.format(benefit.lower())] = cps_benefit[benefit]

        setattr(self, 'prob', prob)
        setattr(self, 'base_participation', base_participation)
        setattr(self, 'base_benefits', base_benefits)
        setattr(self, 'participant_targets', participant_targets)
        setattr(self, 'benefit_targets', benefit_targets)
        setattr(self, 'benefit_extrapolation', benefit_extrapolation)
        setattr(self, 'WT', cps_weights)
        setattr(self, 'benefit_name', benefit)

    @staticmethod
    def _extrapolate(WT, I, benefits, prob, target):
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
        wt_ravel = Benefits._repeating_ravel((len(WT), 15),
                                                          apply_to=np.array(WT))

        result.I_wt = result.I * wt_ravel

        I = Benefits._unravel_data(result, "I", I.columns.tolist(),
                                               dtype=np.int64)
        benefits = Benefits._unravel_data(result, "benefits",
                                                      benefits.columns.tolist(),
                                                      dtype=np.float64)
        # prob = Extrapolation._unravel_data(result, "prob", prob.columns.tolist(),
        #                     dtype=np.float64)

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

        # create indices
        i = Benefits._repeating_ravel(I_arr.shape)
        j = i % I_arr.shape[1]

        # stack and create data frame with all individuals
        extrap_arr = np.vstack((prob_arr.ravel(), I_arr.ravel(), I_wt.ravel(),
                                benefits_arr.ravel(), i, j)).T
        extrap_df = pd.DataFrame(extrap_arr,
                                 columns=["prob", "I", "I_wt", "benefits",
                                          "i", "j"])

        return extrap_df


if __name__ == "__main__":


    benefits = {"SSI": {"grates_path": "ssi_growth_rates.csv",
                        "cps_tax_units_path": "cps_ssi.csv"}
                }

    for benefit in benefits:
        # (prob, indicator, benefits, participant_targets, benefit_targets,
        #     benefit_extrapolation) = \
        #         prepare_data(benefits[benefit]["grates_path"],
        #                      benefits[benefit]["cps_tax_units_path"],
        #                      CPS_weights,
        #                      benefit=benefit)
        #
        # """extrapolate"""
        #
        # indicator, prob, benefits, benefit_extrapolation = \
        #     run(indicator, benefits, prob,
        #         CPS_weights, participant_targets,
        #         benefit_targets,
        #         benefit_extrapolation)
        ben = Benefits(benefits[benefit]["grates_path"],
                                      benefits[benefit]["cps_tax_units_path"],
                                      pd.read_csv('cps_weights.csv'),
                                      benefit=benefit)
        for _ in range(12):
            ben.increment_year()

        ben.benefit_extrapolation.to_csv("benefit_extrapolation.csv", index=False)




    # ravel_test(indicator, benefits, prob, CPS_weights)
