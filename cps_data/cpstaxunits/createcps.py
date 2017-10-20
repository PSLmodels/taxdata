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

    # export and compress data
    print 'Exporting and Compressing Data'
    cps_v3.to_csv('../cps_raw.csv', index=False)
    subprocess.check_call(["gzip", "-nf", "../cps_raw.csv"])

if __name__ == '__main__':
    createcps()
