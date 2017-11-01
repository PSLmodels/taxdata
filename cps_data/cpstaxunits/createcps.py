"""
Script to run all files that create the CPS file
"""
import pandas as pd
from cpsrets import Returns
from adj_filst import adjfilst
from assemble import assemble
from topcoding import topcoding
from imputetobit import imputation
from targets import targets
from blankslate import blankslate
from merge_benefits import BenefitMerge
import cpsmar_2013
import cpsmar_2014
import cpsmar_2015
import os
import subprocess


def createcps():
    """
    Logic for creating the CPS tax unit file
    """

    # first check for the presense of the CPS files with benefits merged
    cps13_merged = os.path.isfile('data/cps_2013_aug.csv')
    cps14_merged = os.path.isfile('data/cps_2014_aug.csv')
    cps15_merged = os.path.isfile('data/cps_2015_aug.csv')
    # second, check for the DAT formated CPS
    cps13_dat = os.path.isfile('data/asec2013_pubuse.dat')
    cps14_dat = os.path.isfile('data/asec2014_pubuse_tax_fix_5x8_2017.dat')
    cps15_dat = os.path.isfile('data/asec2015_pubuse.dat')

    # if the CSV CPS files are present, use those for the rest of the script
    if cps13_merged and cps14_merged and cps15_merged:
        print 'Reading Data'
        cps13 = pd.read_csv('data/cps_2013_aug.csv')
        cps14 = pd.read_csv('data/cps_2014_aug.csv')
        cps15 = pd.read_csv('data/cps_2015_aug.csv')
    # if the CSV CPS files are not present, create them from the dat files
    elif cps13_dat and cps14_dat and cps15_dat:
        print 'Creating CPS Files'
        cps13 = cpsmar_2013.create_cps('data/asec2013_pubuse.dat')
        path_2014 = 'data/asec2014_pubuse_tax_fix_5x8_2017.dat'
        cps14 = cpsmar_2014.create_cps(path_2014)
        cps15 = cpsmar_2015.create_cps('data/asec2015_pubuse.dat')
        # merge C-TAM imputed benefits
        print 'Merging Benefits'
        cps13, cps14, cps15 = BenefitMerge(cps13, cps14, cps15)
    else:
        msg = ('You must have either CSV files for the 2013, 2014, and 2015' +
               ' CPS files augmented with C-TAM imputed benefits, or the raw' +
               ' DAT formatted versions of the CPS, available from NBER')
        raise IOError(msg)

    print 'Creating Tax Units for 2013 CPS'
    rets2013 = Returns(cps13, 2013)
    taxunits13 = rets2013.computation()
    print 'Creating Tax Units for 2014 CPS'
    rets2014 = Returns(cps14, 2014)
    taxunits14 = rets2014.computation()
    print 'Creating Tax Units for 2015 CPS'
    rets2015 = Returns(cps15, 2015)
    taxunits15 = rets2015.computation()
    print 'Assembling File'
    full_taxunits = assemble(taxunits13, taxunits14, taxunits15)
    print 'Adjusting for Top Coding'
    cps_tc = topcoding(full_taxunits)
    print 'Imputing Deductions'
    # read in beta coefficients used in imputations
    logit_betas = pd.read_csv('data/logit_betas.csv', index_col=0)
    ols_betas = pd.read_csv('data/ols_betas.csv', index_col=0)
    tobit_betas = pd.read_csv('data/tobit_betas.csv', index_col=0)
    # impute
    cps_v2 = imputation(cps_tc, logit_betas, ols_betas, tobit_betas)
    print 'Adjusting for State Targets'
    state_targets = pd.read_csv('data/agg_state_data.csv', index_col='STATE')
    cps_v3 = targets(cps_v2, state_targets)
    print 'Blank Slate Imputations'
    blankslate(cps_v3)

    print 'Renaming Variables'
    rename = {'MCAID_PROB1': 'MEDICAID_PROB1',
              'MCAID_PROB10': 'MEDICAID_PROB10',
              'MCAID_PROB11': 'MEDICAID_PROB11',
              'MCAID_PROB12': 'MEDICAID_PROB12',
              'MCAID_PROB13': 'MEDICAID_PROB13',
              'MCAID_PROB14': 'MEDICAID_PROB14',
              'MCAID_PROB15': 'MEDICAID_PROB15',
              'MCAID_PROB2': 'MEDICAID_PROB2',
              'MCAID_PROB3': 'MEDICAID_PROB3',
              'MCAID_PROB4': 'MEDICAID_PROB4',
              'MCAID_PROB5': 'MEDICAID_PROB5',
              'MCAID_PROB6': 'MEDICAID_PROB6',
              'MCAID_PROB7': 'MEDICAID_PROB7',
              'MCAID_PROB8': 'MEDICAID_PROB8',
              'MCAID_PROB9': 'MEDICAID_PROB9',
              'MCAID_VAL1': 'MEDICAID_VAL1',
              'MCAID_VAL10': 'MEDICAID_VAL10',
              'MCAID_VAL11': 'MEDICAID_VAL11',
              'MCAID_VAL12': 'MEDICAID_VAL12',
              'MCAID_VAL13': 'MEDICAID_VAL13',
              'MCAID_VAL14': 'MEDICAID_VAL14',
              'MCAID_VAL15': 'MEDICAID_VAL15',
              'MCAID_VAL2': 'MEDICAID_VAL2',
              'MCAID_VAL3': 'MEDICAID_VAL3',
              'MCAID_VAL4': 'MEDICAID_VAL4',
              'MCAID_VAL5': 'MEDICAID_VAL5',
              'MCAID_VAL6': 'MEDICAID_VAL6',
              'MCAID_VAL7': 'MEDICAID_VAL7',
              'MCAID_VAL8': 'MEDICAID_VAL8',
              'MCAID_VAL9': 'MEDICAID_VAL9',
              'MCARE_PROB1': 'MEDICARE_PROB1',
              'MCARE_PROB10': 'MEDICARE_PROB10',
              'MCARE_PROB11': 'MEDICARE_PROB11',
              'MCARE_PROB12': 'MEDICARE_PROB12',
              'MCARE_PROB13': 'MEDICARE_PROB13',
              'MCARE_PROB14': 'MEDICARE_PROB14',
              'MCARE_PROB15': 'MEDICARE_PROB15',
              'MCARE_PROB2': 'MEDICARE_PROB2',
              'MCARE_PROB3': 'MEDICARE_PROB3',
              'MCARE_PROB4': 'MEDICARE_PROB4',
              'MCARE_PROB5': 'MEDICARE_PROB5',
              'MCARE_PROB6': 'MEDICARE_PROB6',
              'MCARE_PROB7': 'MEDICARE_PROB7',
              'MCARE_PROB8': 'MEDICARE_PROB8',
              'MCARE_PROB9': 'MEDICARE_PROB9',
              'MCARE_VAL1': 'MEDICARE_VAL1',
              'MCARE_VAL10': 'MEDICARE_VAL10',
              'MCARE_VAL11': 'MEDICARE_VAL11',
              'MCARE_VAL12': 'MEDICARE_VAL12',
              'MCARE_VAL13': 'MEDICARE_VAL13',
              'MCARE_VAL14': 'MEDICARE_VAL14',
              'MCARE_VAL15': 'MEDICARE_VAL15',
              'MCARE_VAL2': 'MEDICARE_VAL2',
              'MCARE_VAL3': 'MEDICARE_VAL3',
              'MCARE_VAL4': 'MEDICARE_VAL4',
              'MCARE_VAL5': 'MEDICARE_VAL5',
              'MCARE_VAL6': 'MEDICARE_VAL6',
              'MCARE_VAL7': 'MEDICARE_VAL7',
              'MCARE_VAL8': 'MEDICARE_VAL8',
              'MCARE_VAL9': 'MEDICARE_VAL9',
              'SSI': 'ssi_ben',
              'VB': 'vb_ben',
              'MEDICARE': 'medicare_ben',
              'MEDICAID': 'medicaid_ben',
              'SS': 'ss_ben',
              'SNAP': 'snap_ben',
              'WT': 's006'}
    cps_final = cps_v3.rename(columns=rename)

    # export and compress data
    print 'Exporting and Compressing Data'
    cps_final.to_csv('../cps_raw.csv', index=False)
    subprocess.check_call(["gzip", "-nf", "../cps_raw.csv"])

if __name__ == '__main__':
    createcps()
