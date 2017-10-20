"""
Merge imputed benefits from the open source C-TAM model to the three CPS files
"""
import pandas as pd


def len_check(start, cps, var):
    """
    Used for error checking
    """
    if start != len(cps['peridnum']):
        difference = start - len(cps['peridnum'])
        msg = 'CPS missing records: {}. Difference: {}'.format(var, difference)
        raise ValueError(msg)


def merge(cps, vb, mcaid, mcaid_prob, mcare, mcare_prob, ss, snap, ssi, year):
    """
    Merge the benefit variables onto the CPS files.
    """
    start = len(cps['peridnum'])
    cps = cps.merge(vb, how='left', on='peridnum')
    len_check(start, cps, 'vb')
    cps = cps.rename(columns={'prob': 'vb_probs'})
    cps = cps.merge(mcaid, how='left', on='peridnum')
    len_check(start, cps, 'mcaid')
    cps = cps.merge(mcaid_prob, how='left', on='peridnum')
    len_check(start, cps, 'mcaid_prob')
    cps = cps.rename(columns={'prob': 'mcaid_probs'})
    cps = cps.merge(mcare, how='left', on='peridnum')
    len_check(start, cps, 'mcare')
    cps = cps.merge(mcare_prob, how='left', on='peridnum')
    len_check(start, cps, 'mcare_prob')
    cps = cps.rename(columns={'prob': 'mcare_probs'})
    cps = cps.merge(ss, how='left', on='peridnum')
    len_check(start, cps, 'ss')
    cps = cps.rename(columns={'Prob_Received': 'ss_probs'})
    cps = cps.merge(snap, how='left', on='h_seq')
    len_check(start, cps, 'snap')
    cps = cps.rename(columns={'probs': 'snap_probs'})
    cps = cps.merge(ssi, how='left', on='peridnum')
    len_check(start, cps, 'ssi')
    cps = cps.rename(columns={'probs': 'ssi_probs'})
    cps = cps.fillna(0.)
    return cps


def BenefitMerge(cps_2013, cps_2014, cps_2015):
    """
    Main logic for merging imputed benefits onto the CPS files
    """

    # Read in benefit files
    # For the 2015 CPS
    vb2015 = pd.read_csv('data/VB_Imputation15.csv',
                         usecols=['peridnum', 'vb_impute', 'prob'])
    mcare2015_prob = pd.read_csv('data/medicare_prob15.csv',
                                 usecols=['peridnum', 'prob'])
    mcare2015 = pd.read_csv('data/medicare15.csv',
                            usecols=['peridnum', 'MedicareX'])
    mcaid2015_prob = pd.read_csv('data/medicaid_prob15.csv',
                                 usecols=['peridnum', 'prob'])
    mcaid2015 = pd.read_csv('data/medicaid15.csv',
                            usecols=['peridnum', 'MedicaidX'])
    ssi_2015 = pd.read_csv('data/SSI_Imputation15.csv',
                           usecols=['peridnum', 'ssi_impute', 'probs'])
    ss_2015 = pd.read_csv('data/SS_augmentation_15.csv',
                          usecols=['peridnum', 'ss_val', 'Prob_Received'])
    snap2015 = pd.read_csv('data/SNAP_imputation_15.csv',
                           usecols=['h_seq', 'snap_impute', 'probs'])

    # Function to merge all the files with the CPS
    cps_2015_final = merge(cps_2015, vb2015, mcaid2015, mcaid2015_prob,
                           mcare2015, mcare2015_prob, ss_2015, snap2015,
                           ssi_2015, 2015)

    # For the 2014 CPS
    vb2014 = pd.read_csv('data/VB_Imputation14.csv',
                         usecols=['peridnum', 'vb_impute', 'prob'])
    mcare2014_prob = pd.read_csv('data/medicare_prob14.csv',
                                 usecols=['peridnum', 'prob'])
    mcare2014 = pd.read_csv('data/medicare14.csv',
                            usecols=['peridnum', 'MedicareX'])
    mcaid2014_prob = pd.read_csv('data/medicaid_prob14.csv',
                                 usecols=['peridnum', 'prob'])
    mcaid2014 = pd.read_csv('data/medicaid14.csv',
                            usecols=['peridnum', 'MedicaidX'])
    ssi_2014 = pd.read_csv('data/SSI_Imputation14.csv',
                           usecols=['peridnum', 'ssi_impute', 'probs'])
    ss_2014 = pd.read_csv('data/SS_augmentation_14.csv',
                          usecols=['peridnum', 'ss_val', 'Prob_Received'])
    snap2014 = pd.read_csv('data/SNAP_imputation_14.csv',
                           usecols=['h_seq', 'snap_impute', 'probs'])

    # Function to merge all the files with the CPS
    cps_2014_final = merge(cps_2014, vb2014, mcaid2014, mcaid2014_prob,
                           mcare2014, mcare2014_prob, ss_2014, snap2014,
                           ssi_2014, 2014)

    # For the 2013 CPS
    vb2013 = pd.read_csv('data/VB_Imputation13.csv',
                         usecols=['peridnum', 'vb_impute', 'prob'])
    mcare2013_prob = pd.read_csv('data/medicare_prob13.csv',
                                 usecols=['peridnum', 'prob'])
    mcare2013 = pd.read_csv('data/medicare13.csv',
                            usecols=['peridnum', 'MedicareX'])

    mcaid2013_prob = pd.read_csv('data/medicaid_prob13.csv',
                                 usecols=['peridnum', 'prob'])
    mcaid2013 = pd.read_csv('data/medicaid13.csv')
    ssi_2013 = pd.read_csv('data/SSI_Imputation13.csv',
                           usecols=['peridnum', 'ssi_impute', 'probs'])
    ss_2013 = pd.read_csv('data/SS_augmentation_13.csv',
                          usecols=['peridnum', 'ss_val', 'Prob_Received'])
    snap2013 = pd.read_csv('data/SNAP_imputation_13.csv',
                           usecols=['h_seq', 'snap_impute', 'probs'])

    # Function to merge all the files with the CPS
    cps_2013_final = merge(cps_2013, vb2013, mcaid2013, mcaid2013_prob,
                           mcare2013, mcare2013_prob, ss_2013, snap2013,
                           ssi_2013, 2013)

    print 'Exporting data'
    cps_2015_final.to_csv('data/cps_2015_aug.csv', index=False)
    cps_2014_final.to_csv('data/cps_2014_aug.csv', index=False)
    cps_2013_final.to_csv('data/cps_2013_aug.csv', index=False)

    return cps_2013_final, cps_2014_final, cps_2015_final
