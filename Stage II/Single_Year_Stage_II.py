
import numpy as np
import pandas as pd
from numba import vectorize, float64
from cylp.cy import CyClpSimplex
from cylp.py.modeling.CyLPModel import CyLPArray, CyLPModel

def Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year, tol):


    length = len(puf.s006)


    print("Preparing coefficient matrix...")
    apopsnr = pd.Series([Stage_I_factors[year]["APOPSNR"]] * length)
    arets = pd.Series([Stage_I_factors[year]["ARETS"]] * length)

    # Set up the matrix
    One_half_LHS = np.vstack(blow_up(puf.e00100, puf.e00200, puf.e00300, puf.e00600, puf.e00900, puf.e01000,
                                     puf.e01700, puf.e02000, puf.e02300, puf.e02400, puf.s006, puf.mars,
                                     puf.xocah, puf.xocawh, puf.xoodep, puf.xopar, apopsnr, arets))


    # Coefficients for r and s
    A1 = np.matrix(One_half_LHS)
    A2 = np.matrix(-One_half_LHS)


    print("Preparing targets for ", year)

    APOPN = Stage_I_factors[year]["APOPN"]

    Single = Stage_II_targets[year]['Single']-single_return.sum()
    Joint = Stage_II_targets[year]['Joint']-joint_return.sum()
    HH = Stage_II_targets[year]['HH']-hh_return.sum()
    SS_return = Stage_II_targets[year]['SS_return']-return_w_SS.sum()
    Dep_return = Stage_II_targets[year]['Dep_return'] -  dependent_exempt_num.sum()

    AINTS = Stage_I_factors[year]["AINTS"]
    INTEREST = Stage_II_targets[year]['INTS']*APOPN/AINTS*1000-interest.sum()

    ADIVS = Stage_I_factors[year]["ADIVS"]
    DIVIDEND = Stage_II_targets[year]['DIVS']*APOPN/ADIVS*1000 - dividend.sum()

    ASCHCI = Stage_I_factors[year]["ASCHCI"]
    BIZ_INCOME = Stage_II_targets[year]['SCHCI']*APOPN/ASCHCI*1000 - biz_income.sum()


    ASCHCL = Stage_I_factors[year]["ASCHCL"]
    BIZ_LOSS = Stage_II_targets[year]['SCHCL']*APOPN/ASCHCL*1000 - biz_loss.sum()

    ACGNS = Stage_I_factors[year]["ACGNS"]
    CAP_GAIN = Stage_II_targets[year]['CGNS']*APOPN/ACGNS*1000 - cap_gain.sum()

    ATXPY = Stage_I_factors[year]["ATXPY"]
    ANNUITY_PENSION = Stage_II_targets[year]['Pension']*APOPN/ATXPY*1000 - annuity_pension.sum()

    ASCHEI = Stage_I_factors[year]["ASCHEI"]
    SCH_E_INCOME = Stage_II_targets[year]["SCHEI"]*APOPN/ASCHEI*1000 - sch_e_income.sum()

    ASCHEL = Stage_I_factors[year]["ASCHEL"]
    SCH_E_LOSS = Stage_II_targets[year]["SCHEL"]*APOPN/ASCHEL*1000 - sch_e_loss.sum()

    ASOCSEC = Stage_I_factors[year]["ASOCSEC"]
    APOPSNR = Stage_I_factors[year]["APOPSNR"]
    SS_INCOME = Stage_II_targets[year]["SS"]*APOPSNR/ASOCSEC*1000 - ss_income.sum()

    AUCOMP = Stage_I_factors[year]["AUCOMP"]
    UNEMPLOYMENT_COMP = Stage_II_targets[year]["UCOMP"]*APOPN/AUCOMP*1000 - unemployment_comp.sum()

    AWAGE = Stage_I_factors[year]["AWAGE"]
    WAGE_1 = Stage_II_targets[year]["WAGE_1"]*APOPN/AWAGE*1000 - wage_1.sum()
    WAGE_2 = Stage_II_targets[year]["WAGE_2"]*APOPN/AWAGE*1000 - wage_2.sum()
    WAGE_3 = Stage_II_targets[year]["WAGE_3"]*APOPN/AWAGE*1000 - wage_3.sum()
    WAGE_4 = Stage_II_targets[year]["WAGE_4"]*APOPN/AWAGE*1000 - wage_4.sum()
    WAGE_5 = Stage_II_targets[year]["WAGE_5"]*APOPN/AWAGE*1000 - wage_5.sum()
    WAGE_6 = Stage_II_targets[year]["WAGE_6"]*APOPN/AWAGE*1000 - wage_6.sum()
    WAGE_7 = Stage_II_targets[year]["WAGE_7"]*APOPN/AWAGE*1000 - wage_7.sum()
    WAGE_8 = Stage_II_targets[year]["WAGE_8"]*APOPN/AWAGE*1000 - wage_8.sum()
    WAGE_9 = Stage_II_targets[year]["WAGE_9"]*APOPN/AWAGE*1000 - wage_9.sum()
    WAGE_10 = Stage_II_targets[year]["WAGE_10"]*APOPN/AWAGE*1000 - wage_10.sum()
    WAGE_11 = Stage_II_targets[year]["WAGE_11"]*APOPN/AWAGE*1000 - wage_11.sum()
    WAGE_12 = Stage_II_targets[year]["WAGE_12"]*APOPN/AWAGE*1000 - wage_12.sum()



    temp = [Single, Joint, HH, SS_return, Dep_return,
            INTEREST,DIVIDEND, BIZ_INCOME, BIZ_LOSS, CAP_GAIN, ANNUITY_PENSION,
            SCH_E_INCOME, SCH_E_LOSS, SS_INCOME, UNEMPLOYMENT_COMP,
            WAGE_1,WAGE_2, WAGE_3,WAGE_4, WAGE_5, WAGE_6,
            WAGE_7,WAGE_8,WAGE_9, WAGE_10, WAGE_11, WAGE_12]
    
    b = list(temp)

    targets = CyLPArray(b)
    print("Targets for year ", year, " is ", targets)

    LP = CyLPModel()

    r = LP.addVariable('r', length)
    s = LP.addVariable('s', length)

    print("Adding constraints")
    LP.addConstraint(r >=0, "positive r")
    LP.addConstraint(s >=0, "positive s")
    LP.addConstraint(r + s <= tol, "abs upperbound")

    c = CyLPArray((np.ones(length)))
    LP.objective = c * r + c * s




    LP.addConstraint(A1 * r + A2 * s == targets, "Aggregates")

    print("Setting up the LP model")
    model = CyClpSimplex(LP)


    print("Solving LP......")
    model.initialSolve()

    print("DONE!!")
    z = np.empty([length])
    z = (1+model.primalVariableSolution['r'] - model.primalVariableSolution['s'])*s006
    return z

@vectorize([float64(float64, float64, float64, float64, float64, float64,
                    float64, float64, float64, float64, float64, float64,
                    float64, float64, float64, float64, float64, float64)])
def blow_up(e00100, e00200, e00300, e00600, e00900, e01000,
            e01700, e02000, e02300, e02400, s006, mars, xocah,
            xocawh, xoodep, xopar, apopsnr, arets):

    # blow up the weights
    if e02400 > 0:
        s006 = s006 * apopsnr / 100
    else:
        s006 = s006 * arets / 100
    
    single_return = 0
    joint_return = 0
    hh_return = 0
    if mars == 1:
        single_return = s006
    elif mars == 2 or mars == 3:
        joint_return = s006
    else:
        hh_return = s006
        
    if e02400 > 0:
        ss_return = s006
    else:
        ss_return = 0
        
    dependent_exempt_num = (xocah + xocawh + xoodep + xopar) * s006
    interest = e00300 * s006
    dividend = e00600 * s006
    
    biz_income = 0
    biz_loss = 0
    if e00900 > 0:
        biz_income = e00900 * s006
    else:
        biz_loss = -e00900 * s006
    
    
    if e01000 > 0:
        cap_gain = e01000 * s006
    else:
        cap_gain = 0
        
    
    annuity_pension = e01700 * s006
    
    sch_e_income = 0
    sch_e_loss = 0
    if e02000:
        sch_e_income = e02000 * s006
    else:
        sch_e_loss = -e02000 * s006

    ss_income = e02400 * s006
    
    unemployment_comp = e02300 * s006


    # Wage distribution
    wage_1 = 0
    wage_2 = 0
    wage_3 = 0
    wage_4 = 0
    wage_5 = 0
    wage_6 = 0
    wage_7 = 0
    wage_8 = 0
    wage_9 = 0
    wage_10 = 0
    wage_11 = 0
    wage_12 = 0

    if e00100<=0:
        wage_1 = e00200 * s006
    elif e00100 <= 10000:
        wage_2 = e00200 * s006
    elif e00100 <= 20000:
        wage_3 = e00200 * s006
    elif e00100 <= 30000:
        wage_4 = e00200 * s006
    elif e00100 <= 40000:
        wage_5 = e00200 * s006
    elif e00100 <= 50000:
        wage_6 = e00200 * s006
    elif e00100 <= 75000:
        wage_7 = e00200 * s006
    elif e00100 <= 100000:
        wage_8 = e00200 * s006
    elif e00100 <= 200000:
        wage_9 = e00200 * s006
    elif e00100 <= 500000:
        wage_10 = e00200 * s006
    elif e00100 <= 1000000:
        wage_11 = e00200 * s006
    else:
        wage_12 = e00200 * s006
        
    
    return (single_return, joint_return, hh_return, return_w_SS,
            dependent_exempt_num, interest, dividend,
            biz_income,biz_loss, cap_gain, annuity_pension,
            sch_e_income, sch_e_loss, ss_income, unemployment_comp,
            wage_1, wage_2, wage_3, wage_4, wage_5, wage_6,
            wage_7, wage_8, wage_9, wage_10, wage_11, wage_12)   
    
        

        
        
        



