"""
Adjust top coded records
"""
import numpy as np
import pandas as pd


def was(cps):
    """
    Adjust wages and salaries for top coding
    """
    # Head of unit
    mask = cps['tc1_p'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(12. + 1. * rand)
    new_vals = np.where(new_vals < 200000., 200000., new_vals)
    cps.loc[mask, 'wasp'] = new_vals
    # spouse of unit
    mask = cps['tc1_s'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(12. + 1. * rand)
    new_vals = np.where(new_vals < 200000., 200000., new_vals)
    cps.loc[mask, 'wass'] = new_vals


def ints(cps):
    """
    Adjust interest income for top coding
    """
    # Head of unit
    mask = cps['tc2_p'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(9. + 1. * rand)
    new_vals = np.where(new_vals < 24000., 24000., new_vals)
    cps.loc[mask, 'intstp'] = new_vals
    # spouse of unit
    mask = cps['tc2_s'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(9. + 1. * rand)
    new_vals = np.where(new_vals < 24000., 24000., new_vals)
    cps.loc[mask, 'intsts'] = new_vals


def divs(cps):
    """
    Adjust dividend income for top coding
    """
    # Head of unit
    mask = cps['tc3_p'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(10.5 + 1. * rand)
    new_vals = np.where(new_vals < 20000., 20000., new_vals)
    cps.loc[mask, 'dbep'] = new_vals
    # spouse of unit
    mask = cps['tc3_s'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(10.5 + 1. * rand)
    new_vals = np.where(new_vals < 20000., 20000., new_vals)
    cps.loc[mask, 'dbes'] = new_vals


def alimony(cps):
    """
    Adjust alimony income for top coding
    """
    # Head of unit
    mask = cps['tc4_p'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(13. + 1. * rand)
    new_vals = np.where(new_vals < 45000., 45000., new_vals)
    cps.loc[mask, 'alimonyp'] = new_vals
    # spouse of unit
    mask = cps['tc4_s'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(13. + 1. * rand)
    new_vals = np.where(new_vals < 45000., 45000., new_vals)
    cps.loc[mask, 'alimonys'] = new_vals


def biz(cps):
    """
    Adjust alimony income for top coding
    """
    # Head of unit
    mask = cps['tc5_p'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(10.4 + 1. * rand)
    new_vals = np.where(new_vals < 50000., 50000., new_vals)
    cps.loc[mask, 'bilp'] = new_vals
    # spouse of unit
    mask = cps['tc5_s'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(10.4 + 1. * rand)
    new_vals = np.where(new_vals < 50000., 50000., new_vals)
    cps.loc[mask, 'bils'] = new_vals


def pensions(cps):
    """
    Adjust alimony income for top coding
    """
    # Head of unit
    mask = cps['tc6_p'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(10.5 + 1. * rand)
    new_vals = np.where(new_vals < 45000., 45000., new_vals)
    cps.loc[mask, 'pensionsp'] = new_vals
    # spouse of unit
    mask = cps['tc6_s'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(10.5 + 1. * rand)
    new_vals = np.where(new_vals < 45000., 45000., new_vals)
    cps.loc[mask, 'pensionss'] = new_vals


def rent(cps):
    """
    Adjust alimony income for top coding
    """
    # Head of unit
    mask = cps['tc7_p'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(13.15 + 1. * rand)
    new_vals = np.where(new_vals < 40000., 40000., new_vals)
    cps.loc[mask, 'rentsp'] = new_vals
    # spouse of unit
    mask = cps['tc7_s'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(13.15 + 1. * rand)
    new_vals = np.where(new_vals < 40000., 40000., new_vals)
    cps.loc[mask, 'rentss'] = new_vals


def farm(cps):
    """
    Adjust alimony income for top coding
    """
    # Head of unit
    mask = cps['tc8_p'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(13. + 1. * rand)
    new_vals = np.where(new_vals < 25000., 25000., new_vals)
    cps.loc[mask, 'filp'] = new_vals
    # spouse of unit
    mask = cps['tc8_s'] > 0
    cps_valid = cps[mask]
    rand = np.random.uniform(size=len(cps_valid))
    new_vals = np.exp(13. + 1. * rand)
    new_vals = np.where(new_vals < 25000., 25000., new_vals)
    cps.loc[mask, 'fils'] = new_vals


def topcoding(cps):
    """
    Parameters
    ----------
    cps: a full CPS file

    Returns
    -------
    None
    """
    np.random.seed(5410)
    ncopies = 15

    # Flag records for top coded values
    # wage and salary
    cps['tc1_p'] = np.where(cps['wasp'] > 200000., 1, 0)
    cps['tc1_s'] = np.where(cps['wass'] > 200000., 1, 0)
    # interest income
    cps['tc2_p'] = np.where(cps['intstp'] > 24000., 1, 0)
    cps['tc2_s'] = np.where(cps['intsts'] > 24000., 1, 0)
    # dividends
    cps['tc3_p'] = np.where(cps['dbep'] > 20000., 1, 0)
    cps['tc3_s'] = np.where(cps['dbes'] > 20000., 1, 0)
    # alimony
    cps['tc4_p'] = np.where(cps['alimonyp'] > 45000., 1, 0)
    cps['tc4_s'] = np.where(cps['alimonys'] > 45000., 1, 0)
    # business income/loss
    cps['tc5_p'] = np.where(cps['bilp'] > 50000., 1, 0)
    cps['tc5_s'] = np.where(cps['bils'] > 50000., 1, 0)
    # pensions
    cps['tc6_p'] = np.where(cps['pensionsp'] > 45000., 1, 0)
    cps['tc6_s'] = np.where(cps['pensionss'] > 45000., 1, 0)
    # rents
    cps['tc7_p'] = np.where(cps['rentsp'] > 40000., 1, 0)
    cps['tc7_s'] = np.where(cps['rentss'] > 40000., 1, 0)
    # farm income/loss
    cps['tc8_p'] = np.where(cps['filp'] > 25000., 1, 0)
    cps['tc8_s'] = np.where(cps['fils'] > 25000., 1, 0)
    # Add up to get total top codes
    cps['tc_all'] = (cps['tc1_p'] + cps['tc1_s'] + cps['tc2_p'] +
                     cps['tc2_s'] + cps['tc3_p'] + cps['tc3_s'] +
                     cps['tc4_p'] + cps['tc4_s'] + cps['tc5_p'] +
                     cps['tc5_s'] + cps['tc6_p'] + cps['tc6_s'] +
                     cps['tc7_p'] + cps['tc7_s'] + cps['tc8_p'] + cps['tc8_s'])

    # split CPS into two
    cps_tc = cps[cps['tc_all'] > 0]  # records with a top code
    cps_non_tc = cps[cps['tc_all'] == 0]  # records without a top code

    # create 15 copies of the top coded records
    tc_list = []
    for i in range(ncopies):
        tc_list.append(cps_tc)
    cps_exp = pd.concat(tc_list)
    # Call each function with the list of 15 copes
    was(cps_exp)
    ints(cps_exp)
    divs(cps_exp)
    alimony(cps_exp)
    biz(cps_exp)
    pensions(cps_exp)
    rent(cps_exp)
    farm(cps_exp)

    # Re-calculate aggregate variables in the expanded CPS
    cps_exp['was'] = cps_exp['wasp'] + cps_exp['wass']
    cps_exp['intst'] = cps_exp['intstp'] + cps_exp['intsts']
    cps_exp['dbe'] = cps_exp['dbep'] + cps_exp['dbes']
    cps_exp['alimony'] = cps_exp['alimonyp'] + cps_exp['alimonys']
    cps_exp['bil'] = cps_exp['bilp'] + cps_exp['bils']
    cps_exp['pensions'] = cps_exp['pensionsp'] + cps_exp['pensionss']
    cps_exp['rents'] = cps_exp['rentsp'] + cps_exp['rentss']
    cps_exp['fil'] = cps_exp['filp'] + cps_exp['fils']
    cps_exp['wt'] /= 15

    # recombine the CPS file
    cps_final = pd.concat([cps_non_tc, cps_exp])
    drop_vars = ['tc_all']
    for i in range(1, 9):
        drop_vars.append('tc{}_p'.format(i))
        drop_vars.append('tc{}_s'.format(i))
    cps_final = cps_final.drop(drop_vars, axis=1)

    return cps_final
