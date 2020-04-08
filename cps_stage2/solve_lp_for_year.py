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
    def wage_bin(left, right):
        # Don't use pandas.Series.between since that's only inclusive on
        # both sides or neither side.
        return np.where((data.e00100 > left) & (data.e00100 <= right),
                        data.WAS, 0) * s006
    
    wage1 = wage_bin(-np.inf, 10000)
    wage2 = wage_bin(10000, 20000)
    wage3 = wage_bin(20000, 30000)
    wage4 = wage_bin(30000, 40000)
    wage5 = wage_bin(40000, 50000)
    wage6 = wage_bin(50000, 75000)
    wage7 = wage_bin(75000, 100000)
    wage8 = wage_bin(100000, np.inf)

    LHS_VAR_NAMES = [
        'single_returns', 'joint_returns', 'hh_returns', 'returns_w_ss',
        'dep_exemptions', 'interest', 'dividend', 'biz_income', 'biz_loss',
        'cap_gain', 'pension', 'sch_e_income', 'sch_e_loss', 'ss_income',
        'ucomp', 'wage1', 'wage2', 'wage3', 'wage4', 'wage5', 'wage6', 'wage7',
        'wage8']
    
    for i in LHS_VAR_NAMES:
        lhs_vars[i] = globals()[i]

    print('Preparing Targets for {}...'.format(year))
    FACTOR_VAR_NAMES = [
        'apopn', 'aints', 'adivs', 'aschci', 'aschcl', 'acgns', 'atxpy',
        'aschei', 'aschel', 'asocsec', 'apopsnr', 'aucomp', 'awage'
    ]
    
    for i in FACTOR_VAR_NAMES:
        exec(i + " = factors['" + i.upper() + "'][year]")

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
    
    def add_target(val, col, factor, pop=apopn):
        rhs_vars[val] = target(targets[year][col], apopn, factor, 
                               globals()[val].sum())
    
    add_target('interest', 'INTS', aints)
    add_target('dividend', 'DIVS', adivs)
    add_target('biz_income', 'SCHCI', aschci)
    add_target('biz_loss', 'SCHCL', aschcl)
    add_target('cap_gain', 'CGNS', acgns)
    add_target('pension', 'Pension', atxpy)
    add_target('sch_e_income', 'SCHEI', aschei)
    add_target('sch_e_loss', 'SCHEL', aschel)
    # Social Security income uses a different population variable.
    add_target('ss_income', 'SS', asocsec, apopsnr)
    add_target('ucomp', 'UCOMP', aucomp)
    for i in [1, 2, 3, 4, 5, 6, 7, 8]:
        add_target('wage' + str(i), 'wage' + str(i), awage)

    model_vars = ['single_returns', 'joint_returns', 'returns_w_ss',
                  'dep_exemptions', 'interest', 'dividend', 'biz_income',
                  'pension', 'ss_income', 'ucomp', 'wage1', 'wage2', 'wage3',
                  'wage4', 'wage5', 'wage6', 'wage7', 'wage8']
    # 2014 data lacks dividend and ucomp.
    if year == '2014':
        model_vars.remove('dividend')
        model_vars.remove('ucomp')

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
    print('Constructing LP Model...')
    lp = pulp.LpProblem('CPS Stage 2', pulp.LpMinimize)
    r = pulp.LpVariable.dicts('r', data.index, lowBound=0)
    s = pulp.LpVariable.dicts('s', data.index, lowBound=0)
    # add objective function
    lp += pulp.lpSum([r[i] + s[i] for i in data.index])
    # add constraints
    for i in data.index:
        lp += r[i] + s[i] <= tol
    for i in range(len(b)):
        lp += pulp.lpSum([(a1[i][j] * r[j] + a2[i][j] * s[j])
                          for j in data.index]) == b[i]
    print('Solving Model...')
    pulp.LpSolverDefault.msg = 1
    lp.solve()
    print(pulp.LpStatus[lp.status])

    # apply r and s to the weights
    r_val = np.array([r[i].varValue for i in r])
    s_val = np.array([s[i].varValue for i in s])
    z = (1. + r_val - s_val) * s006 * 100

    return z
