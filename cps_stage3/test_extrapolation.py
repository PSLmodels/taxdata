import pandas as pd
import numpy as np

from extrapolation import Benefits

def test_ravel():
    """
    Test that ravel(unravel(data)) == data
    """
    ben = Benefits()
    indicator = ben.ssi_participation
    benefits = ben.ssi_benefits
    prob = ben.ssi_prob

    wt = ben.WT.loc[:, 'WT2015']

    extrap_df = Benefits._ravel_data(wt.copy(), indicator.copy(),
                                         benefits.copy(), prob.copy())
    # shuffle dataframe first
    extrap_df = extrap_df.sample(frac=1)
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


def test_add_particpants():
    """
    Check that entry with lowest probablity but is a participant is NOT removed
    and that entry highest probablity is added
    """
    wt = np.ones(10)
    I = pd.DataFrame({'I': [1, 1, 0, 1, 1, 0, 0, 0, 1, 0]})
    benefits = pd.DataFrame([10, 10, 0, 10, 10, 0, 0, 0, 10, 0])
    prob = [0.0, 0.9, 0.8, 0.9, 0.1, 0.0, 0.7, 0.0, 0.1, 1.0]

    target_part = 6

    I_act, ben_act = Benefits._extrapolate(wt, I, benefits, prob, target_part, J=1)

    I_exp = np.array([1, 1, 0, 1, 1, 0, 0, 0, 1, 1]).T
    ben_exp = np.array([10, 10, 0, 10, 10, 0, 0, 0, 10, 10]).T

    assert np.allclose(I_act.values.ravel(), I_exp)
    assert np.allclose(ben_act.values.ravel(), ben_exp)


def test_remove_participants():
    """
    Check that entry with lowest probablity is removed and that entry with
    highest probablity but is not participating is not added
    """
    wt = np.ones(10)
    I = pd.DataFrame({'I': [1, 1, 0, 1, 1, 0, 0, 0, 1, 0]})
    benefits = pd.DataFrame([10, 10, 0, 10, 10, 0, 0, 0, 10, 0])
    prob = [0.0, 0.9, 0.8, 0.9, 0.1, 0.0, 0.7, 0.0, 0.1, 1.0]

    target_part = 4

    I_act, ben_act = Benefits._extrapolate(wt, I, benefits, prob, target_part, J=1)

    I_exp = np.array([0, 1, 0, 1, 1, 0, 0, 0, 1, 0]).T
    ben_exp = np.array([0, 10, 0, 10, 10, 0, 0, 0, 10, 0]).T

    assert np.allclose(I_act.values.ravel(), I_exp)
    assert np.allclose(ben_act.values.ravel(), ben_exp)


def test_repeating_ravel():
    test = np.array([5,6,7,8])
    act = Benefits._repeating_ravel((4,2), apply_to=test)
    exp = np.array([5, 5, 6, 6, 7, 7, 8, 8])

    assert np.allclose(act, exp)


def test_unravel_data():
    test_df = pd.DataFrame({'i': [0, 0, 1, 1, 2, 2, 3, 3],
                            'j': [0, 1, 0, 1, 0, 1, 0, 1],
                            'var': [2, 3, 5, 7, 11, 13, 17, 19]})
    act = Benefits._unravel_data(test_df, 'var', ['var0', 'var1'])
    exp = pd.DataFrame({'var0': [2, 5, 11, 17],
                        'var1': [3, 7, 13, 19]})

    pd.testing.assert_frame_equal(exp, act, check_dtype=False)


def test_ravel_data():
    wt = [1, 2, 3, 4, 5, 6]
    I = np.array([[1, 1, 1, 1, 1, 0], [0, 1, 1, 1, 1, 1]]).T
    benefits = np.array([[9, 10, 11, 10, 9, 0], [0, 9, 10, 11, 10, 9]]).T
    prob = np.array([[0.9, 0.8, 0.7, 0.6, 0.5, 0.1],
                     [0.1, 0.5, 0.6, 0.7, 0.8, 0.9]]).T

    I_wt_exp = np.array([1, 0, 2, 2, 3, 3, 4, 4, 5, 5, 0, 6])
    benefits_wt_exp = np.array([9, 0, 20, 18, 33, 30, 40, 44, 45, 50, 0, 54])
    prob_exp = np.array([0.9, 0.1, 0.8, 0.5, 0.7, 0.6, 0.6, 0.7,
                         0.5, 0.8, 0.1, 0.9])
    i_exp = np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5])
    j_exp = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1])

    act = Benefits._ravel_data(wt, I, benefits, prob)

    assert np.allclose(act.I_wt.values, I_wt_exp)
    assert np.allclose(act.benefits_wt.values, benefits_wt_exp)
    assert np.allclose(act.prob.values, prob_exp)
    assert np.allclose(act.i.values, i_exp)
    assert np.allclose(act.j.values, j_exp)
