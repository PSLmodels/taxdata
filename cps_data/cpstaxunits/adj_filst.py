import numpy as np


def adjfilst(cps):
    """
    Randomly make nonfilers filers
    Parameters
    ----------
    cps: A CPS based tax unit file
    Returns
    -------
    Separate DF's for filers and nonfilers
    """
    # Determine which files to change after the adjustment
    cps['case1'] = np.where((cps['filst'] == 0) &
                            (cps['was'] > 0.), 1, 0)
    cps['case2'] = np.where((cps['filst'] == 0) &
                            (cps['was'] <= 0.), 1, 0)
    np.random.seed(409)
    cps['z1'] = cps.apply(lambda row: np.random.uniform(0, 1)
                          if row['case1'] == 1 else 1
                          if row['case2'] else 0, axis=1)
    # np.random.seed(5410)
    cps['z2'] = cps.apply(lambda row: np.random.uniform(0, 1)
                          if row['case2'] == 1 else 1
                          if row['case1'] else 0, axis=1)
    # selected = (cps['z1'] <= 0.84 or cps['z2'] <= 0.54)
    cps['filst'] = np.where((cps['z1'] <= 0.84) | (cps['z2'] <= 0.54),
                            1, cps['filst'])
    cps.drop(['case1', 'case2'], axis=1, inplace=True)
    cps['cpsseq'] = cps.index + 1

    return cps
