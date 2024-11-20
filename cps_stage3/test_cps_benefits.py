import sys
import pandas as pd
import numpy as np
from pandas.util.testing import assert_frame_equal


'''
The tests in this script check distribution and aggregates for the benefit data.
Whenever the benefit data gets updated, the tests would create new statistics
and compare with the previous version. 

This file needs three inputs: CPS weights (cps_weights.csv.gz), CPS tax unit
database (cps.csv.gz), and CPS benefit (cps_benefits_extrap_full.csv.gz).
The first two input files are in their corresponding folders as indicated
in the code, but the third benefit file is different from the current version
in that it also includes recipient information for each tax unit. Because this
recipient per tax unit information is not used in the tax-calculator, we have
dropped those variable to save space. But the recipients is essential for
checking aggregates and distribution. So anyone who wants to run the tests needs
to recreate the full version of benefit data.

It is relatively simple to generate the full version:

1. find the extrapolation.py in the current folder and comment out the six
lines of code (line 310 - 315) that drop all recipients
2. Rename the output to cps_benefits_extrap_full.csv.gz
3. Run the extrapolation script with 'python extrapolation.py'

The tests will create three new files for statistic summary:

1. decile2015_new.csv: participation, total benefit and average benefit
by wage decile
2. aggregates_new.csv: total participation and benefits for each program
from 2014 to 2026
3. tabs_new.csv: tabulations of tax unit participation for each program
from 2014 to 2026

If all three files are exactly the same as the previous version, then the tests
will pass. If the tests fail, compare the new version with the previous version
carefully and then replace the previous with the new version if the difference is
reasonable.

'''


programs = ['ss', 'ssi', 'medicaid', 'medicare', 'vb', 'snap']
billion = 1e09
million = 1e06
delta = 1e-06

def read_files():
    ''' import weights, benefit, and raw cps file'''
    
    # import from taxdata repo
    # weights and wage are for 10-year and decile tables
    weights = pd.read_csv('../cps_stage2/cps_weights.csv.gz', compression='gzip')
    cps_income = pd.read_csv('../cps_data/cps.csv.gz',
                             compression='gzip')[['e00200', 's006', 'RECID']]
    # the benefit file that includes both benefits and recipients
    cps_benefit = pd.read_csv('cps_benefits_extrap_full.csv.gz')

    assert len(cps_income) == len(weights)
    
    # merge all essential variables
    cps = cps_income.merge(cps_benefit, on='RECID', how='left')
    cps.fillna(0, inplace=True)
    cps = cps.join(weights/100)
    
    # rename to facilitate for loops
    cps.rename(columns={'s006': 'WT2014'}, inplace=True)
    
    # create decile ranks by wage
    cps = cps.sort_values(by='e00200')
    cps['WT2015_cumsum'] = cps.WT2015.cumsum()
    cps['WT2015_decile'] = np.ceil(cps.WT2015_cumsum/(max(cps.WT2015_cumsum)/9.99))

    return cps

cps = read_files()

def test_decile_dist():
    
    ''' total participation, total benefits and average benefits
        by decile
    '''
    benefits_vars = [x + '_benefits_2015' for x in programs]
    p_vars = [x + '_recipients_2015' for x in programs]
    
    decile2015 = pd.DataFrame(np.linspace(1,10, num=10), columns=['2015_decile'])

    for i in range(6):

        # create weighted benefit
        cps[benefits_vars[i] + '_weighted'] = cps[benefits_vars[i]] * cps['WT2015']

        # temporary variable for weighted participation
        cps['dummy'] = np.where(cps[p_vars[i]]!=0, cps['WT2015'], 0)
        
        # calculate total benefits, participation (# tax units), and average per decile
        variables = [benefits_vars[i] + '_weighted', 'dummy']
        bp = cps[variables].groupby(cps.WT2015_decile, as_index=False).sum()
        
        
        bp['average'] = bp[benefits_vars[i] + '_weighted']/(bp['dummy'] + delta)

        # rename and save
        bp.columns = [programs[i]+'_benefits', programs[i]+'_taxunits', programs[i]+'_average']
        decile2015 = pd.concat([decile2015, bp], axis=1)
        
        decile2015.to_csv('decile2015_new.csv', float_format='%.1f', index=False)

    decile_old = pd.read_csv('decile2015.csv')
    assert_frame_equal(decile2015.round(1), decile_old)


def test_aggregates():
    
    '''total individual & taxunit participation, total benefits from 2014-2026'''
    
    benefits = pd.DataFrame(programs, columns=['programs'])
    taxunits = pd.DataFrame(programs, columns=['programs'])
    participants = pd.DataFrame(programs, columns=['programs'])
    
    for year in range(2014, 2025):
        #benefits
        benefits_vars = [x + '_benefits_' + str(year) for x in programs]
        raw_benefits = cps.loc[:,benefits_vars]
        weighted_benefits = raw_benefits.multiply(cps['WT' + str(year)], axis='index')
        benefit_total = pd.DataFrame(weighted_benefits.sum()/billion)
        benefits[year] = benefit_total.values

        #participants
        p_vars = [x + '_recipients_'+ str(year) for x in programs]
        raw_participants = cps.loc[:, p_vars]
        weighted_par = raw_participants.multiply(cps['WT' + str(year)], axis='index')
        participant_total = pd.DataFrame(weighted_par.sum()/million)
        participants[year] = participant_total.values

        # tax units
        dummy = raw_participants.astype(bool)
        weighted_taxunits = dummy.multiply(cps['WT' + str(year)], axis='index')
        taxunit_total = pd.DataFrame(weighted_taxunits.sum()/million)
        taxunits[year] = taxunit_total.values

    pd.options.display.float_format = '{:,.1f}'.format
    with open('aggregates_new.txt', 'w') as file:
        file.write("Total benefits (billions)\n" + benefits.to_string(index=False) + '\n\n')
        file.write('Total participating tax units (millions)\n' + taxunits.to_string(index=False) + '\n\n')
        file.write('Total participants (millions)\n' + participants.to_string(index=False) + '\n\n')

    # import the current version
    agg_old = pd.read_csv('aggregates.txt', delim_whitespace=True, skiprows=[0,9,18], thousands=',')
    agg_old.columns = ['programs'] + list(range(2014, 2025))

    benefits_old = agg_old.loc[0:5]
    assert_frame_equal(benefits.round(1), benefits_old)

    taxunits_old = agg_old.loc[7:12].reset_index().drop(['index'], axis=1)
    assert_frame_equal(taxunits.round(1), taxunits_old)

    participants_old = agg_old.loc[14:19].reset_index().drop(['index'], axis=1)
    assert_frame_equal(participants.round(1), participants_old)


def test_tabs():
    
    ''' tabulation of number of participants per tax unit from 2014 to 2026'''
    
    tabs = {}
    
    # inline function to create single year program tabulation
    p_tab = lambda program: cps[program].value_counts()

    for program in programs:
        program_tab = {}
        for year in range(2014, 2025): 
            program_tab[year] = p_tab(program+"_recipients_"+str(year))
            program_tab = pd.DataFrame(program_tab)
            program_tab.fillna(0, inplace=True)
        tabs[program] = program_tab.astype(int)

    with open('tabs_new.txt', 'w') as file:
        for key, dfs in tabs.iteritems():
            file.write(key + '\n')
            file.write(dfs.to_string() + '\n\n')

    tabs_old = pd.read_csv('tabs.txt', delim_whitespace=True,
                           names=['index'] + list(range(2014, 2025)))
    tabs_old = tabs_old[tabs_old['index']!='2014']

    for program in programs:
    
        unitmax = len(tabs[program])
        start_row = (tabs_old.index[tabs_old['index']==program] + 1).values[0]
        end_row = start_row + unitmax
    
        participation_old = tabs_old.loc[start_row: end_row]
        participation_old = participation_old.reset_index().drop(['level_0'], axis=1)
    
        assert_frame_equal(participation_old.astype(float),
                           tabs[program].reset_index().astype(float),
                           check_column_type=False, check_index_type=False)


