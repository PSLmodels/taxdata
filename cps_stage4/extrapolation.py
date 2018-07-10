from __future__ import print_function
import time
from copy import deepcopy
import numpy as np
import pandas as pd


SYEAR = 2014
LYEAR = 2027

BENEFIT_NAMES = ['ssi', 'mcaid', 'mcare', 'vet',
                 'snap', 'tanf', 'housing', 'wic']


class Benefits(object):

    def __init__(self):
        self.read_data()
        self.current_year = SYEAR

    def increment_year(self, tol):
        self.current_year += 1
        print('starting year', self.current_year)
        WT = self.WT.loc[:, 'WT'+str(self.current_year)]
        for bname in BENEFIT_NAMES:
            participant_targets = getattr(
                self,
                '{}_participant_targets'.format(bname)
            )
            benefit_targets = getattr(
                self,
                '{}_benefit_targets'.format(bname)
            )
            participation = getattr(self, '{}_participation'.format(bname))
            benefits = getattr(self, '{}_benefits'.format(bname))
            prob = getattr(self, '{}_prob'.format(bname))

            diff = participant_targets[self.current_year] - \
                (participation.sum(axis=1) * WT).sum()
            if abs(diff)/participant_targets[self.current_year] > tol:
                participation, benefits = \
                    self.extrapolate(WT,
                                     participation.copy(deep=True),
                                     benefits.copy(deep=True),
                                     prob,
                                     participant_targets[self.current_year],
                                     bname,
                                     self.current_year,
                                     tol=tol)
            extrapolated = (participation.sum(axis=1) * WT).sum()
            target_ = participant_targets[self.current_year]
            msg = '{} benefit in {}: '.format(bname, self.current_year)
            msg += 'total= {:.0f} and target= {:.0f}\n'.format(
                extrapolated, target_)
            reldiff_ = extrapolated / target_ - 1.
            msg += '   which implies reldiff= {:.3f}'.format(reldiff_)
            lab = bname + '_recipients_' + str(self.current_year)
            self.benefit_extrapolation[lab] = participation.sum(axis=1)
            total_current_benefits = (benefits.sum(axis=1) * WT).sum()
            lab = bname + '_' + str(self.current_year)
            self.benefit_extrapolation[lab] = \
                (benefits.sum(axis=1) *
                 benefit_targets[self.current_year] / total_current_benefits)
            setattr(self, '{}_participation'.format(bname), participation)
            setattr(self, '{}_benefits'.format(bname), benefits)

    @staticmethod
    def extrapolate(WT, part, benefits, prob, target,
                    benefit_name, benefit_year, tol, maxsize=15):
        """
        Arguments:
          - part is boolean array indicating benefit program participation.
          - maxsize is the assumed maximum number of people in a filing unit.
        Goal: get number of participants as close to target as possible
        Steps:
            1. Data is currently in N x maxsize shape. Reshape it to be
                N * maxsize dim vector
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
            6. Stack dataframes, unravel (go back to N x maxsize dim), and
                return result
            Note: Unraveling is done by keeping track of each individual's
                location in the matrix (i, j).  Sorting by i and then j gives
                us a vector of tuples (1,1),(1,2),...,(1,maxsize),(2,1),(2,2),
                ...,(N,maxsize). Then by reshaping to n rows, maxsize columns
                we get the same matrix that we started with but with the
                updated values.
        """
        start = time.time()

        extrap_df = Benefits._stack_df(WT, part, benefits, prob, maxsize)

        receives = extrap_df.loc[extrap_df.part > 0, ]
        avg_benefit = receives.benefits_wt.sum() / receives.part_wt.sum()

        actual = extrap_df.part_wt.sum()
        diff = actual - target
        if diff < 0:
            remove = False
            candidates = extrap_df.loc[extrap_df.part == 0, ].copy()
            assert candidates.part.sum() == 0
            # set everyone as a participant and then remove surplus below
            #   this is necessary since part * wt will all be zeroes
            candidates.loc[:, 'part'] = np.ones(len(candidates))
            candidates.loc[:, 'part_wt'] = candidates.part * candidates.wt
            noncandidates = extrap_df.loc[extrap_df.part == 1, ].copy()
            assert noncandidates.part.sum() == len(noncandidates)
        else:
            remove = True
            candidates = extrap_df.loc[extrap_df.part == 1, ].copy()
            assert candidates.part.sum() == len(candidates)
            noncandidates = extrap_df.loc[extrap_df.part == 0, ].copy()
            assert noncandidates.part.sum() == 0
        noncan_part = noncandidates.part_wt.sum()
        del extrap_df
        # sort by probability of getting benefits in descending order
        #   of prob so that we only keep those with highest prob of
        #   receiving benefits in the future
        candidates.sort_values(by='prob', ascending=False, inplace=True)
        # create running sum of weighted participants
        candidates['cum_participants'] = (candidates.part_wt.cumsum() +
                                          noncan_part)
        # get absolute difference between candidates and target
        candidates['_diff'] = candidates.cum_participants - target

        # check to make sure that results are close enough
        results_ = candidates[candidates._diff <= 0].cum_participants.max()
        if not np.allclose(results_, target, atol=0.0, rtol=tol):
            msg = 'Problem with {} participants in year {}:\n'.format(
                benefit_name, benefit_year)
            msg += ' results={:.0f} and target={:.0f} are not close;\n'.format(
                results_, target)
            reldiff_ = results_ / target - 1.
            msg += ' abs of reldiff={:.3f} larger than rtol={:.3f}'.format(
                reldiff_, tol)
            raise ValueError(msg)

        # individuals prior to min_diff have highest probability of getting
        #   benefits in the future ==> they get benefits
        candidates.loc[candidates._diff <= 0, 'part'] = 1
        candidates.loc[candidates._diff > 0, 'part'] = 0

        if remove:
            candidates.loc[candidates._diff > 0, 'benefits'] = 0
        else:
            # all added candidates have indicator 1 but no benefits
            candidates.loc[(candidates.part == 1) & (candidates.benefits == 0),
                           'benefits'] = avg_benefit

        result = pd.concat([noncandidates, candidates], axis=0,
                           sort=False, ignore_index=False)
        del candidates
        del noncandidates

        result.part_wt = result.part * result.wt
        part = result.part.unstack().sort_index()
        benefits = result.benefits.unstack().sort_index()

        finish = time.time()
        msg = '{} benefit for {} execution time is {:.1f} seconds'.format(
            benefit_name, benefit_year, (finish - start))
        print(msg)

        return part, benefits

    @staticmethod
    def _stack_df(WT, part, benefits, prob, maxsize):
        wt_ext = pd.concat([WT for _ in range(0, maxsize)], axis=1)
        wt_ext.columns = list(range(0, maxsize))

        wt_stack = wt_ext.stack()
        part_stack = part.stack()
        ben_stack = benefits.stack()
        prob_stack = prob.stack()

        extrap_df = pd.concat(
            (wt_stack, part_stack, ben_stack, prob_stack),
            axis=1
        )
        extrap_df.columns = ['wt', 'part', 'benefits', 'prob']
        extrap_df['part_wt'] = extrap_df.part * extrap_df.wt
        extrap_df['benefits_wt'] = extrap_df.benefits * extrap_df.wt

        return extrap_df

    def read_data(self):
        """
        prepare data
        """
        cps_benefit = pd.read_csv('../cps_data/cps_raw_rename.csv.gz')
        self.index = cps_benefit['SEQUENCE']

        cps_weights = pd.read_csv('../cps_stage2/cps_weights.csv.gz')
        cps_weights['SEQUENCE'] = self.index
        cps_weights.set_index('SEQUENCE', inplace=True)

        benefit_extrapolation = pd.DataFrame({'SEQUENCE': self.index})
        benefit_extrapolation.set_index('SEQUENCE', inplace=True)

        cps_benefit.set_index('SEQUENCE', inplace=True)

        self.WT = cps_weights
        growth_rates = pd.read_csv('growth_rates.csv', index_col=0)

        for bname in BENEFIT_NAMES:
            # create benefit targets
            benefit_syear = (cps_benefit[bname] * cps_benefit.WT).sum()
            benefit_targets = (benefit_syear *
                               (1 + growth_rates['{}_benefit_growth'
                                                 .format(bname)]))
            benefit_targets = benefit_targets[1:]
            # extract program benefit in SYEAR to base_benefits array
            ubn = bname.upper()
            base_benefits_col = [col for col in list(cps_benefit)
                                 if col.startswith('{}_VAL'.format(ubn))]
            base_benefits = cps_benefit[base_benefits_col]
            base_benefits.columns = list(range(len(base_benefits.columns)))
            # create Participation targets from tax-unit individual
            #   level markers and growth rates from SSA
            col_list = list(range(len(base_benefits.columns)))
            base_participation = pd.DataFrame(np.where(base_benefits > 0,
                                                       1, 0),
                                              index=self.index,
                                              columns=col_list)
            total_particpants = (base_participation.sum(axis=1) *
                                 cps_benefit.WT).sum()
            participant_targets = total_particpants * \
                (1 + growth_rates['{}_participation_growth'.format(bname)])
            # extract probability of participation in program from
            #   tax-unit database
            prob_col = [col for col in list(cps_benefit)
                        if col.startswith('{}_PROB'.format(bname.upper()))]
            prob = cps_benefit[prob_col]
            prob.columns = list(range(len(prob.columns)))
            # dataframe of number participants and total benefits from program
            idx = '{}_recipients_{}'.format(bname, SYEAR)
            benefit_extrapolation[idx] = base_participation.sum(axis=1)
            idx = '{}_{}'.format(bname, SYEAR)
            benefit_extrapolation[idx] = cps_benefit[bname]
            setattr(self, '{}_prob'.format(bname),
                    prob)
            setattr(self, '{}_base_participation'.format(bname),
                    base_participation)
            setattr(self, '{}_base_benefits'.format(bname),
                    base_benefits)
            setattr(self, '{}_participant_targets'.format(bname),
                    participant_targets)
            setattr(self, '{}_benefit_targets'.format(bname),
                    benefit_targets)
            setattr(self, '{}_benefit_extrapolation'.format(bname),
                    benefit_extrapolation)
            setattr(self, '{}_participation'.format(bname),
                    base_participation)
            setattr(self, '{}_benefits'.format(bname),
                    base_benefits)

        # add record ID
        benefit_extrapolation['RECID'] = benefit_extrapolation.index.values
        self.benefit_extrapolation = benefit_extrapolation


if __name__ == '__main__':
    # create extrapolated benefits
    ben = Benefits()
    for _ in range(SYEAR + 1, LYEAR + 1):
        ben.increment_year(tol=0.05)
    # drop unnecessary variables
    drop_list = []
    # drop all recipient columns
    for year in range(SYEAR, LYEAR + 1):
        for bname in BENEFIT_NAMES:
            drop_list.append('{}_recipients_{}'.format(bname, year))
    # drop SYEAR benefit values
    for bname in BENEFIT_NAMES:
        drop_list.append('{}_{}'.format(bname, SYEAR))
    extrapolated_benefit = ben.benefit_extrapolation.drop(drop_list, axis=1)
    # drop records with no benefits and write to file
    column_list = extrapolated_benefit.columns
    mask = extrapolated_benefit.loc[:, column_list != 'RECID'].sum(1)
    gets_benefits = deepcopy(extrapolated_benefit[mask != 0])
    integer_gets_benefits = gets_benefits.astype(np.int32)
    integer_gets_benefits.to_csv('cps_benefits.csv.gz', index=False,
                                 compression='gzip')
