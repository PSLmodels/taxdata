import pandas as pd
import numpy as np
import os
from copy import deepcopy
import time

class Benefits():
    GROWTH_RATES_PATH = 'growth_rates.csv'
    CPS_BENEFIT_PATH = '../cps_data/cps_raw_rename.csv.gz'
    CPS_WEIGHTS_PATH = '../cps_stage2/cps_weights.csv.gz'

    def __init__(self,
                 growth_rates=GROWTH_RATES_PATH,
                 cps_benefit=CPS_BENEFIT_PATH,
                 cps_weights=CPS_WEIGHTS_PATH,
                 benefit_names=["ssi", "mcaid", "mcare",
                                "vet", "snap", 'tanf', 'housing', 'wic']):
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
            # part_wt = pd.concat(participation.sum(axis=1), WT)
            # extrapolated = part_wt.
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
            lab = benefit + '_' + str(self.current_year)
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
        start = time.time()

        extrap_df = Benefits._stack_df(WT, I, benefits, prob, J)

        receives = extrap_df.loc[extrap_df.I > 0, ]
        avg_benefit = receives.benefits_wt.sum() / receives.I_wt.sum()

        actual = extrap_df.I_wt.sum()
        diff = actual - target
        if diff < 0:
            remove = False
            candidates = extrap_df.loc[extrap_df.I == 0, ].copy()
            assert candidates.I.sum() == 0
            # set everyone as a participant and then remove surplus below
            # this is necessary since I * wt will all be zeroes
            candidates.loc[:, "I"] = np.ones(len(candidates))
            candidates.loc[:, "I_wt"] = candidates.I * candidates.wt
            noncandidates = extrap_df.loc[extrap_df.I == 1, ].copy()
            assert noncandidates.I.sum() == len(noncandidates)
        else:
            remove = True
            candidates = extrap_df.loc[extrap_df.I == 1, ].copy()
            assert candidates.I.sum() == len(candidates)
            noncandidates = extrap_df.loc[extrap_df.I == 0, ].copy()
            assert noncandidates.I.sum() == 0
        noncan_part = noncandidates.I_wt.sum()
        del extrap_df
        # sort by probability of getting benefits in descending order
        # of prob so that we only keep those with highest prob of
        # receiving benefits in the future
        candidates.sort_values(by="prob", ascending=False, inplace=True)
        # create running sum of weighted participants
        candidates["cum_participants"] = candidates.I_wt.cumsum() + noncan_part
        # get absolute difference between candidates and target
        candidates["_diff"] = candidates.cum_participants - target

        # # check to make results are close enough
        assert np.allclose(
            candidates[candidates._diff <= 0].cum_participants.max(), target,
            atol=0.0, rtol=tol
        )

        # individuals prior to min_diff have highest probability of getting
        # benefits in the future ==> they get benefits
        candidates.loc[candidates._diff <= 0, "I"] = 1
        candidates.loc[candidates._diff > 0, "I"] = 0

        if remove:
            candidates.loc[candidates._diff > 0, 'benefits'] = 0
        else:
            # all added candidates have indicator 1 but no benefits
            candidates.loc[(candidates.I == 1) &
                           (candidates.benefits == 0), 'benefits'] = avg_benefit

        result = pd.concat([noncandidates, candidates], axis=0, ignore_index=False)
        del candidates
        del noncandidates

        result.I_wt = result.I * result.wt
        finish = time.time()
        print('total time', finish - start)
        I = result.I.unstack().sort_index()
        benefits = result.benefits.unstack().sort_index()

        return I, benefits

    @staticmethod
    def _stack_df(WT, I, benefits, prob, J):
        wt_ext = pd.concat([WT for i in range(0, J)], axis=1)
        wt_ext.columns = list(range(0, J))

        wt_stack = wt_ext.stack()
        I_stack = I.stack()
        ben_stack = benefits.stack()
        prob_stack = prob.stack()

        extrap_df = pd.concat(
            (wt_stack, I_stack, ben_stack, prob_stack),
            axis=1
        )
        extrap_df.columns = ['wt', 'I', 'benefits', 'prob']
        extrap_df["I_wt"] = extrap_df.I * extrap_df.wt
        extrap_df["benefits_wt"] = extrap_df.benefits * extrap_df.wt

        return extrap_df

    def _read_data(self, growth_rates, cps_benefit, cps_weights,
                   cps=None, benefit_names=[]):
        """
        prepare data
        """
        cps_benefit = pd.read_csv(cps_benefit)
        self.index = cps_benefit["SEQUENCE"]

        if isinstance(cps_weights, str):
            assert(os.path.exists(cps_weights))
            cps_weights = pd.read_csv(cps_weights)
        else:
            assert(isinstance(cps_weights, pd.DataFrame))
        cps_weights["SEQUENCE"] = self.index
        cps_weights.set_index("SEQUENCE", inplace=True)

        benefit_extrapolation = pd.DataFrame({"SEQUENCE": self.index})
        benefit_extrapolation.set_index('SEQUENCE', inplace=True)

        cps_benefit.set_index("SEQUENCE", inplace=True)

        self.WT = cps_weights
        growth_rates = pd.read_csv(growth_rates, index_col=0)
        for benefit in benefit_names:

            # create benefit targets
            benefit_2014 = (cps_benefit[benefit] * cps_benefit.WT).sum()
            benefit_targets = benefit_2014 * (1 + growth_rates['{0}_benefit_growth'
                                                               .format(benefit)])
            benefit_targets = benefit_targets[1:]

            # extract program benefit in 2014 to base_benefits array
            base_benefits_col = [col for col in list(cps_benefit) if
                                 col.startswith('{0}_VAL'.format(benefit.upper()))]
            base_benefits = cps_benefit[base_benefits_col]
            base_benefits.columns = list(range(len(base_benefits.columns)))
            # Create Participation targets from tax-unit individual level markers
            # and growth rates from SSA
            base_participation = pd.DataFrame(np.where(base_benefits > 0, 1, 0),
                                              index=self.index,
                                              columns=list(range(len(base_benefits.columns))))


            # print(benefit,'value_counts baseline')
            # print(base_participation.sum(axis=1).value_counts())
            total_particpants = (base_participation.sum(axis=1) *
                                 cps_benefit.WT).sum()
            participant_targets = total_particpants * \
                (1 + growth_rates['{0}_participation_growth'.format(benefit)])
            # extract probability of participation in program from tax-unit database
            prob_col = [col for col in list(cps_benefit)
                        if col.startswith('{0}_PROB'.format(benefit.upper()))]
            prob = cps_benefit[prob_col]
            prob.columns = list(range(len(prob.columns)))

            # dataframe of number participants and total benefits from program
            benefit_extrapolation['{}_recipients_2014'.format(benefit)] = base_participation.sum(axis=1)
            benefit_extrapolation['{}_2014'.format(benefit)] = cps_benefit[benefit]
            setattr(self, '{}_prob'.format(benefit), prob)
            setattr(self, '{}_base_participation'.format(benefit), base_participation)
            setattr(self, '{}_base_benefits'.format(benefit), base_benefits)
            setattr(self, '{}_participant_targets'.format(benefit), participant_targets)
            setattr(self, '{}_benefit_targets'.format(benefit), benefit_targets)
            setattr(self, '{}_benefit_extrapolation'.format(benefit), benefit_extrapolation)
            setattr(self, '{}_participation'.format(benefit), base_participation)
            setattr(self, '{}_benefits'.format(benefit), base_benefits)

            # indexing check
            # assert (getattr(self, '{}_prob'.format(benefit)).index == cps_benefit.index).all()
            # assert (getattr(self, '{}_base_participation'.format(benefit)).index == cps_benefit.index).all()
            # assert (getattr(self, '{}_base_benefits'.format(benefit)).index == cps_benefit.index).all()
            # assert (getattr(self, '{}_benefit_extrapolation'.format(benefit)).index == cps_benefit.index).all()
            # assert (getattr(self, '{}_participation'.format(benefit)).index == cps_benefit.index).all()
            # assert (getattr(self, '{}_benefits'.format(benefit)).index == cps_benefit.index).all()

        # add record ID
        benefit_extrapolation['RECID'] = benefit_extrapolation.index.values
        self.benefit_extrapolation = benefit_extrapolation


if __name__ == "__main__":
    ben = Benefits()

    for _ in range(13):
        ben.increment_year()

    # drop unnecessary variables
    drop_list = []
    # drop all recipient columns
    for year in range(2014, 2027 + 1):
        for benefit in ben.benefit_names:
            drop_list.append('{}_recipients_{}'.format(benefit, year))
    # drop 2014 values
    for benefit in ben.benefit_names:
        drop_list.append('{}_2014'.format(benefit))
    ben.benefit_extrapolation = ben.benefit_extrapolation.drop(drop_list,
                                                               axis=1)
    # drop records with no benefits
    col_list = ben.benefit_extrapolation.columns
    mask = ben.benefit_extrapolation.loc[:, col_list != 'RECID'].sum(1)
    gets_benefits = deepcopy(ben.benefit_extrapolation[mask != 0])
    int_gets_benefits = gets_benefits.astype(np.int32)
    int_gets_benefits.to_csv("cps_benefits.csv.gz", index=False,
                             compression="gzip")
