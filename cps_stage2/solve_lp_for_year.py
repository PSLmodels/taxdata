import numpy as np
import pulp


def solve_lp_for_year(data, factors, targets, year, tol):
    """
    Parameters
    ----------
    data: CPS data
    factors: growth factors
    targets: aggregate targets
    year: year LP model is being solved for
    tol: tolerance
    """
    def target(target_val, pop, factor, value):
        return (target_val * pop / factor * 1000 - value)

    print('Preparing Coefficient Matrix for {}'.format(year))
    # data_len = len(data.WT)
    # dictionary used just to play with the targets we add
    lhs_vars = {}

    # don't divide by 100 because WT hasn't been multiplied by 100
    s006 = np.where(data.SS > 0,
                    data.WT * factors['APOPSNR'][year],
                    data.WT * factors['ARETS'][year])

    single_returns = np.where((data.JS == 1) & (data.FILST == 1),
                              s006, 0)
    joint_returns = np.where((data.JS == 2) & (data.FILST == 1),
                             s006, 0)
    hh_returns = np.where((data.JS == 3) & (data.FILST == 1),
                          s006, 0)
    returns_w_ss = np.where((data.SS > 0) & (data.FILST == 1),
                            s006, 0)
    dep_exemptions = np.where(data.JS == 2, data.XXTOT - 2,
                              data.XXTOT - 1) * s006
    interest = data.INTST * s006
    dividend = data.DBE * s006
    biz = data.JCPS25 + data.JCPS35
    biz_income = np.where(biz > 0, biz, 0) * s006
    biz_loss = np.where(biz < 0, -biz, 0) * s006
    cap_gain = np.where(data.CGAGIX > 0, data.CGAGIX, 0) * s006
    pension = data.PENSIONS * s006
    sch_e_income = np.where(data.RENTS > 0, data.RENTS, 0) * s006
    sch_e_loss = np.where(data.RENTS < 0, data.RENTS, 0) * s006
    ss_income = np.where(data.FILST == 1, data.SS, 0) * s006
    ucomp = data.UCOMP * s006

    # wage distribution
    wage1 = np.where((data.e00100 <= 10000), data.WAS, 0) * s006
    wage2 = np.where((data.e00100 > 10000) & (data.e00100 <= 20000),
                     data.WAS, 0) * s006
    wage3 = np.where((data.e00100 > 20000) & (data.e00100 <= 30000),
                     data.WAS, 0) * s006
    wage4 = np.where((data.e00100 > 30000) & (data.e00100 <= 40000),
                     data.WAS, 0) * s006
    wage5 = np.where((data.e00100 > 40000) & (data.e00100 <= 50000),
                     data.WAS, 0) * s006
    wage6 = np.where((data.e00100 > 50000) & (data.e00100 <= 75000),
                     data.WAS, 0) * s006
    wage7 = np.where((data.e00100 > 75000) & (data.e00100 <= 100000),
                     data.WAS, 0) * s006
    wage8 = np.where((data.e00100 > 100000), data.WAS, 0) * s006

    lhs_vars['single_returns'] = single_returns
    lhs_vars['joint_returns'] = joint_returns
    lhs_vars['hh_returns'] = hh_returns
    lhs_vars['returns_w_ss'] = returns_w_ss
    lhs_vars['dep_exemptions'] = dep_exemptions
    lhs_vars['interest'] = interest
    lhs_vars['dividend'] = dividend
    lhs_vars['biz_income'] = biz_income
    lhs_vars['biz_loss'] = biz_loss
    lhs_vars['cap_gain'] = cap_gain
    lhs_vars['pension'] = pension
    lhs_vars['sch_e_income'] = sch_e_income
    lhs_vars['sch_e_loss'] = sch_e_loss
    lhs_vars['ss_income'] = ss_income
    lhs_vars['ucomp'] = ucomp
    lhs_vars['wage1'] = wage1
    lhs_vars['wage2'] = wage2
    lhs_vars['wage3'] = wage3
    lhs_vars['wage4'] = wage4
    lhs_vars['wage5'] = wage5
    lhs_vars['wage6'] = wage6
    lhs_vars['wage7'] = wage7
    lhs_vars['wage8'] = wage8

    print('Preparing Targets for {}'.format(year))
    apopn = factors['APOPN'][year]
    aints = factors['AINTS'][year]
    adivs = factors['ADIVS'][year]
    aschci = factors['ASCHCI'][year]
    aschcl = factors['ASCHCL'][year]
    acgns = factors['ACGNS'][year]
    atxpy = factors['ATXPY'][year]
    aschei = factors['ASCHEI'][year]
    aschel = factors['ASCHEL'][year]
    asocsec = factors['ASOCSEC'][year]
    apopsnr = factors['APOPSNR'][year]
    aucomp = factors['AUCOMP'][year]
    awage = factors['AWAGE'][year]

    year = str(year)
    rhs_vars = {}

    rhs_vars['single_returns'] = targets[year]['Single'] - single_returns.sum()
    rhs_vars['joint_returns'] = targets[year]['Joint'] - joint_returns.sum()
    rhs_vars['hh_returns'] = targets[year]['HH'] - hh_returns.sum()
    target_name = 'SS_return'
    rhs_vars['returns_w_ss'] = targets[year][target_name] - returns_w_ss.sum()
    target_name = 'Dep_return'
    rhs_vars['dep_exemptions'] = (targets[year][target_name] -
                                  dep_exemptions.sum())
    rhs_vars['interest'] = target(targets[year]['INTS'], apopn, aints,
                                  interest.sum())
    rhs_vars['dividend'] = target(targets[year]['DIVS'], apopn, adivs,
                                  dividend.sum())
    rhs_vars['biz_income'] = target(targets[year]['SCHCI'], apopn, aschci,
                                    biz_income.sum())
    rhs_vars['biz_loss'] = target(targets[year]['SCHCL'], apopn, aschcl,
                                  biz_loss.sum())
    rhs_vars['cap_gain'] = target(targets[year]['CGNS'], apopn, acgns,
                                  cap_gain.sum())
    rhs_vars['pension'] = target(targets[year]['Pension'], apopn, atxpy,
                                 pension.sum())
    rhs_vars['sch_e_income'] = target(targets[year]['SCHEI'], apopn, aschei,
                                      sch_e_income.sum())
    rhs_vars['sch_e_loss'] = target(targets[year]['SCHEL'], apopn, aschel,
                                    sch_e_loss.sum())
    rhs_vars['ss_income'] = target(targets[year]['SS'], apopsnr, asocsec,
                                   ss_income.sum())
    rhs_vars['ucomp'] = target(targets[year]['UCOMP'], apopn, aucomp,
                               ucomp.sum())
    rhs_vars['wage1'] = target(targets[year]['wage1'], apopn, awage,
                               wage1.sum())
    rhs_vars['wage2'] = target(targets[year]['wage2'], apopn, awage,
                               wage2.sum())
    rhs_vars['wage3'] = target(targets[year]['wage3'], apopn, awage,
                               wage3.sum())
    rhs_vars['wage4'] = target(targets[year]['wage4'], apopn, awage,
                               wage4.sum())
    rhs_vars['wage5'] = target(targets[year]['wage5'], apopn, awage,
                               wage5.sum())
    rhs_vars['wage6'] = target(targets[year]['wage6'], apopn, awage,
                               wage6.sum())
    rhs_vars['wage7'] = target(targets[year]['wage7'], apopn, awage,
                               wage7.sum())
    rhs_vars['wage8'] = target(targets[year]['wage8'], apopn, awage,
                               wage8.sum())

    model_vars = ['single_returns', 'joint_returns', 'returns_w_ss',
                  'dep_exemptions', 'interest', 'dividend', 'biz_income',
                  'pension', 'ss_income', 'ucomp', 'wage1', 'wage2', 'wage3',
                  'wage4', 'wage5', 'wage6', 'wage7', 'wage8']
    if year == '2014':
        model_vars = ['single_returns', 'joint_returns', 'returns_w_ss',
                      'dep_exemptions', 'interest', 'biz_income',
                      'pension', 'ss_income', 'wage1', 'wage2', 'wage3',
                      'wage4', 'wage5', 'wage6', 'wage7', 'wage8']

    vstack_vars = []
    b = []  # list to hold the targets
    for var in model_vars:
        vstack_vars.append(lhs_vars[var])
        t = rhs_vars[var]
        b.append(t)
        # print(f'{var:14} {t:0.2f}') uncomment when moving to 3.6
        print('{:14} {:0.2f}'.format(var, t))

    vstack_vars = tuple(vstack_vars)
    one_half_lhs = np.vstack(vstack_vars)

    # coefficients for r and s
    a1 = np.array(one_half_lhs)
    a2 = np.array(-one_half_lhs)

    # set up LP model
    print('Constructing LP Model')
    LP = pulp.LpProblem('CPS Stage 2', pulp.LpMinimize)
    r = pulp.LpVariable.dicts('r', data.index, lowBound=0)
    s = pulp.LpVariable.dicts('s', data.index, lowBound=0)
    # add objective function
    LP += pulp.lpSum([r[i] + s[i] for i in data.index])
    # add constrains
    for i in data.index:
        LP += r[i] + s[i] <= tol
    for i in range(len(b)):
        LP += pulp.lpSum([(a1[i][j] * r[j] + a2[i][j] * s[j])
                          for j in data.index]) == b[i]
    print('Solving Model...')
    pulp.LpSolverDefault.msg = 1
    LP.solve()
    print(pulp.LpStatus[LP.status])

    # apply r and s to the weights
    r_val = np.array([r[i].varValue for i in r])
    s_val = np.array([s[i].varValue for i in s])
    z = (1. + r_val - s_val) * s006 * 100

    return z