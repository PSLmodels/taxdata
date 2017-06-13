import sys
import numpy as np
import pandas


BENPUF = False  # set temporarily to True to generate a benpuf.csv file
# BENPUF = False will generate a puf.csv file without any benefits variables


def main():
    """
    Contains all the logic of the puf_data/finalprep.py script.
    """
    # (*) Read unprocessed input file into a Pandas Dataframe
    data = pandas.read_csv('cps-matched-puf.csv')

    # check the PUF year
    max_flpdyr = max(data['flpdyr'])
    if max_flpdyr == 2008:
        data = transform_2008_varnames_to_2009_varnames(data)
    else:  # if PUF year is 2009+
        data = age_consistency(data)

    # (A) Make recid variable be a unique integer key:
    data = create_new_recid(data)

    # (B) Make several variable names be uppercase as in SOI PUF:
    data = capitalize_varnames(data)

    # (C) Impute cmbtp variable to estimate income on Form 6251 but not in AGI:
    cmbtp_standard = data['e62100'] - data['e00100'] + data['e00700']
    zero = np.zeros(len(data.index))
    medical_limit = np.maximum(zero, data['e17500'] -
                               np.maximum(zero, data['e00100']) * 0.075)
    med_adj = np.minimum(medical_limit,
                         0.025 * np.maximum(zero, data['e00100']))
    stx_adj = np.maximum(zero, data['e18400'])
    cmbtp_itemizer = (cmbtp_standard + data['p04470'] + data['e21040'] -
                      data['e18500'] - data['e20800'] - stx_adj - med_adj)
    cmbtp = np.where(data['FDED'] == 1, cmbtp_itemizer, cmbtp_standard)
    data['cmbtp'] = np.where(data['f6251'] == 1, cmbtp, 0.)

    # (D) Split earnings variables into taxpayer (p) and spouse (s) amounts:
    total = np.where(data['MARS'] == 2,
                     data['wage_head'] + data['wage_spouse'], 0)
    earnings_split = np.where(total != 0,
                              data['wage_head'] / total, 1.)
    one_minus_earnings_split = 1.0 - earnings_split
    data['e00200p'] = earnings_split * data['e00200']
    data['e00200s'] = one_minus_earnings_split * data['e00200']
    data['e00900p'] = earnings_split * data['e00900']
    data['e00900s'] = one_minus_earnings_split * data['e00900']
    data['e02100p'] = earnings_split * data['e02100']
    data['e02100s'] = one_minus_earnings_split * data['e02100']

    # (E) Randomly assign additional dependents to households:
    data = add_dependents(data)

    # (F) Add AGI bin indicator used for adjustment factors:
    data = add_agi_bin(data)

    # (G) Remove variables not expected by Tax-Calculator:
    if max_flpdyr >= 2009:
        data = remove_unused_variables(data)

    # (H) Remove benefits variables when BENPUF is False:
    if not BENPUF:
        data = remove_benefits_variables(data)

    # (*) Write processed data to the final CSV-formatted file:
    if BENPUF:
        data.to_csv('benpuf.csv', index=False)
    else:
        data.to_csv('puf.csv', index=False)

    return 0
# end of main function code


def create_new_recid(data):
    """
    Construct unique recid.
    """
    #     The recid (key) for each record is not unique after CPS match
    #     because (1) original SOI PUF records were split in some cases,
    #     and (2) non-filers were added from the CPS.
    #     This problem is fixed by (1) adding a digit at the end of recid
    #     for all original SOI PUF records (if no duplicates, add zero;
    #     otherwise, differentiate duplicates by numbering them with
    #     increment integers starting from zero), and (2) setting recid for
    #     all CPS non-filers to integers beginning with 4000000.

    # sort all the records based on old recid
    sorted_dta = data.sort_values(by='recid')
    # count how many duplicates each old recid has
    #   and save the dup count for each record
    seq = sorted_dta.index
    length = len(sorted_dta['recid'])
    count = [0 for _ in range(length)]
    for index in range(1, length):
        num = seq[index]
        previous = seq[index - 1]
        if sorted_dta['recid'][num] == sorted_dta['recid'][previous]:
            count[num] = count[previous] + 1
    # add the ending digit for filers and non-filers with the dup count
    new_recid = [0 for _ in range(length)]
    for index in range(0, length):
        if data['recid'][index] == 0:
            new_recid[index] = 4000000 + count[index]
        else:
            new_recid[index] = data['recid'][index] * 10 + count[index]
    # replace the old recid with the new one
    data['recid'] = new_recid
    return data


def age_consistency(data):
    """
    Construct age_head from agerange if available; otherwise use CPS value.
    Construct age_spouse as a normally-distributed agediff from age_head.
    """
    # set random-number-generator seed so that always get same random numbers
    np.random.seed(seed=123456789)
    # generate random integers to smooth age distribution in agerange
    shape = data['age_head'].shape
    agefuzz8 = np.random.randint(0, 9, size=shape)
    agefuzz9 = np.random.randint(0, 10, size=shape)
    agefuzz10 = np.random.randint(0, 11, size=shape)
    agefuzz15 = np.random.randint(0, 16, size=shape)

    # assign age_head using agerange midpoint or CPS age if agerange absent
    data['age_head'] = np.where(data['agerange'] == 0,
                                data['age_head'],
                                (data['agerange'] + 1 - data['dsi']) * 10)

    # smooth the agerange-based age_head within each agerange
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 1,
                                               data['dsi'] == 0),
                                data['age_head'] - 3 + agefuzz9,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 2,
                                               data['dsi'] == 0),
                                data['age_head'] - 4 + agefuzz9,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 3,
                                               data['dsi'] == 0),
                                data['age_head'] - 5 + agefuzz10,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 4,
                                               data['dsi'] == 0),
                                data['age_head'] - 5 + agefuzz10,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 5,
                                               data['dsi'] == 0),
                                data['age_head'] - 5 + agefuzz10,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 6,
                                               data['dsi'] == 0),
                                data['age_head'] - 5 + agefuzz15,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 1,
                                               data['dsi'] == 1),
                                data['age_head'] - 0 + agefuzz8,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 2,
                                               data['dsi'] == 1),
                                data['age_head'] - 2 + agefuzz8,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 3,
                                               data['dsi'] == 1),
                                data['age_head'] - 4 + agefuzz10,
                                data['age_head'])

    # convert zero age_head to one
    data['age_head'] = np.where(data['age_head'] == 0,
                                1, data['age_head'])

    # assign age_spouse relative to age_head if married;
    # if head is not married, set age_spouse to zero;
    # if head is married but has unknown age, set age_spouse to one;
    # do not specify age_spouse values below 15
    adiff = np.random.normal(0.0, 4.0, size=shape)
    agediff = np.int_(adiff.round())
    age_sp = data['age_head'] + agediff
    age_spouse = np.where(age_sp < 15, 15, age_sp)
    data['age_spouse'] = np.where(data['mars'] == 2,
                                  np.where(data['age_head'] == 1,
                                           1, age_spouse),
                                  0)

    return data


def capitalize_varnames(data):
    """
    Capitalize some variable names.
    """
    renames = {
        'dsi': 'DSI',
        'eic': 'EIC',
        'fded': 'FDED',
        'flpdyr': 'FLPDYR',
        'mars': 'MARS',
        'midr': 'MIDR',
        'xtot': 'XTOT',
        'recid': 'RECID',
    }
    data = data.rename(columns=renames)
    return data


def remove_unused_variables(data):
    """
    Delete non-benefit variables not expected by Tax-Calculator.
    """
    data['s006'] = data['matched_weight'] * 100

    UNUSED_READ_VARS = [
        'agir1', 'efi', 'elect', 'flpdmo', 'wage_head', 'wage_spouse',
        'f3800', 'f8582', 'f8606', 'f8829', 'f8910', 'f8936',
        'n20', 'n25', 'n30', 'prep', 'schb', 'schcf', 'sche',
        'tform', 'ie', 'txst', 'xfpt', 'xfst',
        'xocah', 'xocawh', 'xoodep', 'xopar', 'agerange',
        'gender', 'earnsplit', 'agedp1', 'agedp2', 'agedp3',
        's008', 's009', 'wsamp', 'txrt', 'matched_weight',
        'e01000', 'e03260', 'e09400', 'e24516', 'e62720', 'e62730',
        'e62740', 'e05100', 'e05800', 'e08800', 'e15360', 'p04470',
        'e00100', 'e20800', 'e21040', 'e62100', 'e59560', 'p60100',
        'e19550', 'e20550', 'e20600', 'e19700', 'e02500', 'e07200',
        'e87870', 'e30400', 'e24598', 'e11300', 'e24535', 'e30500',
        'e07180', 'e53458', 'e33000', 'e25940', 'e12000', 'p65400',
        'e15210', 'e24615', 'e07230', 'e11100', 'e10900', 'e11581',
        'e11582', 'e11583', 'e25920', 's27860', 'e10960', 'e59720',
        'e87550', 'e26190', 'e53317', 'e53410', 'e04600', 'e26390',
        'e15250', 'p65300', 'p25350', 'e06500', 'e10300', 'e26170',
        'e26400', 'e11400', 'p25700', 'e04250', 'e07150', 'e60000',
        'e59680', 'e24570', 'e11570', 'e53300', 'e10605', 'e22320',
        'e26160', 'e22370', 'e53240', 'p25380', 'e10700', 'e09600',
        'e06200', 'e24560', 'p61850', 'e25980', 'e53280', 'e25850',
        'e25820', 'e10950', 'e68000', 'e26110', 'e58950', 'e26180',
        'e04800', 'e06000', 'e87880', 't27800', 'e06300', 'e59700',
        'e26100', 'e05200', 'e87875', 'e82200', 'e25860', 'e07220',
        'e11070', 'e11550', 'e11580', 'p87482', 'FDED',
        'e11900', 'e18600', 'e25960', 'e15100', 'p27895', 'e12200']
    MORE_UNUSED_READ_VARS = [
        'jcps88',
        'jcps89',
        'jcps80',
        'jcps81',
        'jcps82',
        'jcps83',
        'jcps84',
        'jcps85',
        'jcps86',
        'jcps87',
        'zwaspt',
        'e52872',
        'jcps19',
        'jcps18',
        'jcps17',
        'jcps16',
        'jcps15',
        'jcps14',
        'jcps13',
        'jcps12',
        'jcps11',
        'jcps10',
        'icps4',
        'icps5',
        'jcps68',
        'jcps69',
        'cweight',
        'jcps63',
        'jcps60',
        'jcps61',
        'jcps66',
        'jcps67',
        'jcps64',
        'jcps65',
        'cpsseq',
        'jcps97',
        'jcps96',
        'jcps95',
        'jcps94',
        'jcps93',
        'jcps92',
        'jcps91',
        'jcps90',
        'jcps99',
        'jcps98',
        'soiseq',
        'jcps79',
        'jcps78',
        'wt',
        'jcps71',
        'jcps70',
        'jcps73',
        'jcps72',
        'jcps75',
        'jcps74',
        'jcps77',
        'jcps76',
        'jcps62',
        'jcps44',
        'jcps45',
        'jcps46',
        'jcps47',
        'jcps40',
        'jcps41',
        'jcps42',
        'jcps43',
        'zwassp',
        'jcps48',
        'jcps49',
        'p86421',
        'prodseq',
        'jcps53',
        'jcps52',
        'jcps51',
        'jcps50',
        'jcps57',
        'jcps56',
        'jcps55',
        'jcps54',
        'jcps59',
        'jcps58',
        'icps6',
        'jcps4',
        'finalseq',
        'jcps100',
        'e07140',
        'jcps26',
        'jcps27',
        'jcps24',
        'jcps25',
        'jcps22',
        'jcps23',
        'jcps20',
        'jcps21',
        'jcps28',
        'jcps29',
        'e52852',
        'jcps35',
        'jcps34',
        'jcps37',
        'jcps36',
        'jcps31',
        'jcps30',
        'jcps33',
        'jcps32',
        'jcps39',
        'jcps38',
        'jcps7',
        'jcps6',
        'jcps5',
        'icps7',
        'jcps3',
        'jcps2',
        'jcps1',
        'icps3',
        'icps8',
        'icps9',
        'jcps9',
        'jcps8']
    ALL_UNUSED_READ_VARS = UNUSED_READ_VARS + MORE_UNUSED_READ_VARS
    data = data.drop(ALL_UNUSED_READ_VARS, 1)

    NEW_POST_PR83_UNUSED_READ_VARS = [
        'SOISEQ',
        'age_dep1', 'age_dep2', 'age_dep3', 'age_dep4', 'age_dep5',
        'age_oldest', 'age_youngest',
        'cpsseq',
        'e07140',
        'e52852',
        'e52872',
        'finalseq',
        'ftpt_head', 'ftpt_spouse',
        'gender_head', 'gender_spouse',
        'h_seq',
        'hga_head', 'hga_spouse',
        'head_age',
        'i',
        'jcps25', 'jcps28', 'jcps35', 'jcps38',
        'medicaid',
        'medicarex_dep',
        'num_medicaid',
        'num_medicare',
        'num_snap',
        'num_ss',
        'num_ssi',
        'num_vet',
        'p86421',
        'peridnum',
        'prodseq',
        'snap_dep',
        'snap_participationp',
        'snap_participations',
        'sp_ptr',
        'spouse_age',
        'ss',
        'ssi_dep',
        'ssi_participationp',
        'ssi_participations',
        'vb',
        'vb_participationp',
        'vb_participations',
        'vbp',
        'vbs',
        'wt']
    # data = data.drop(NEW_POST_PR83_UNUSED_READ_VARS, 1)

    data = data.fillna(value=0)
    return data


def remove_benefits_variables(data):
    """
    Delete benefits variables.
    """
    BENEFIT_VARS = [
        'ssi', 'ssip', 'ssis', 'ssi_participation',
        'snap', 'snapp', 'snaps', 'snap_participation',
        'medicarex', 'medicarexp', 'medicarexs']
    # data = data.drop(BENEFIT_VARS, 1)
    return data


def transform_2008_varnames_to_2009_varnames(data):
    """
    Convert 2008 IRS-SOI PUF variable names into 2009 PUF variable names.
    """
    data['e18400'] = data['e18425'] + data['e18450']

    # drop unused variables only existing in 2008 IRS-SOI PUF
    UNUSED = {'e18425', 'e18450', 'e25370', 'e25380', 'state',
              'e87500', 'e87510', 'e87520', 'e87540'}
    data = data.drop(UNUSED, 1)

    # drop variables not expected by Tax-Calculator
    UNUSED_READ_VARS = {
        'agir1', 'efi', 'elect', 'flpdmo',
        'f3800', 'f8582', 'f8606',
        'n20', 'n25', 'prep', 'schb', 'schcf', 'sche',
        'tform', 'ie', 'txst', 'xfpt', 'xfst',
        'xocah', 'xocawh', 'xoodep', 'xopar',
        's008', 's009', 'wsamp', 'txrt',
        'e30400', 'e24598', 'e11300', 'e24535', 'e30500',
        'e07180', 'e53458', 'e33000', 'e25940', 'e12000', 'p65400',
        'e24615', 'e07230', 'e11100', 'e10900', 'e11581',
        'e11582', 'e11583', 'e25920', 's27860', 'e59720',
        'e87550', 'e26190', 'e53317', 'e53410', 'e04600', 'e26390',
        'p65300', 'p25350', 'e06500', 'e10300', 'e26170',
        'e26400', 'e11400', 'p25700', 'e04250', 'e07150',
        'e59680', 'e24570', 'e11570', 'e53300', 'e10605', 'e22320',
        'e26160', 'e22370', 'e53240', 'e10700', 'e09600',
        'e06200', 'e24560', 'p61850', 'e25980', 'e53280', 'e25850',
        'e25820', 'e68000', 'e26110', 'e58950', 'e26180',
        'e04800', 'e06000', 't27800', 'e06300', 'e59700',
        'e26100', 'e05200', 'e82200', 'e25860', 'e07220',
        'e11900', 'e25960', 'p27895', 'e12200'}
    data = data.drop(UNUSED_READ_VARS, 1)
    return data


def add_dependents(data):
    """
    Randomly assign fourth under 13 dependent to households with three or
    more dependents under 13 and randomly assign an elderly dependent

    Decimals used when randomly assigning dependents come from 2014 CPS data.
    Using the 'hunder15' variable (the closest one available to under13),
    roughly 1/3 of the number of households with three or more persons under
    15 had four or more under 15. Looking at those ages 13 and under in the
    data set, slightly over 1/3 of those in households with three or more
    under 15 were in households with four or more under 15. The decimal used
    here is the average of these two numbers.

    Similarly, the number used in elderly dependent assignment is the fraction
    of those 65 and older that are listed as dependents in the data set.
    """
    # pylint: disable=too-many-locals
    # Randomly assign fourth dependent to units with at lease three dependents
    np.random.seed(409)
    randDep = (list(np.random.rand(len(data.agedp3[(data.agedp3 > 0) &
                                                   (data.agedp3 <= 2)]))))
    agedp4 = []
    for item in data.agedp3:
        if 0 < item <= 2:
            x = randDep.pop(0)
            if x <= .360998:
                agedp4.append(1)
            else:
                agedp4.append(0)
        else:
            agedp4.append(0)
    agedp4 = np.array(agedp4)
    # Count number of dependents under 13
    under1 = np.where(((data.agedp1 > 0) & (data.agedp1 <= 2)), 1, 0)
    under2 = np.where(((data.agedp2 > 0) & (data.agedp2 <= 2)), 1, 0)
    under3 = np.where(((data.agedp3 > 0) & (data.agedp3 <= 2)), 1, 0)
    under4 = np.where(agedp4 == 1, 1, 0)
    nu13 = under1 + under2 + under3 + under4
    data["nu13"] = nu13
    # Add elderly dependent
    np.random.seed(1000)
    elderly = np.array(np.random.rand(len(data.agedp3)))
    elderly_dependent = np.where(elderly <= 0.000075509, 1, 0)
    data['elderly_dependent'] = elderly_dependent
    # Count dependents under 5
    age1 = np.where(data.agedp1 == 1, 1, 0)
    age2 = np.where(data.agedp2 == 1, 1, 0)
    age3 = np.where(data.agedp3 == 1, 1, 0)
    under5 = age1 + age2 + age3
    data['nu05'] = under5
    return data


def add_agi_bin(data):
    """
    Add an AGI bin indicator used in Tax-Calc to apply adjustment factors

    """
    agi = pandas.Series([0] * len(data.e00100))
    agi[data.e00100 < 0] = 0
    agi[(data.e00100 >= 0) & (data.e00100 < 5000)] = 1
    agi[(data.e00100 >= 5000) & (data.e00100 < 10000)] = 2
    agi[(data.e00100 >= 10000) & (data.e00100 < 15000)] = 3
    agi[(data.e00100 >= 15000) & (data.e00100 < 20000)] = 4
    agi[(data.e00100 >= 20000) & (data.e00100 < 25000)] = 5
    agi[(data.e00100 >= 25000) & (data.e00100 < 30000)] = 6
    agi[(data.e00100 >= 30000) & (data.e00100 < 40000)] = 7
    agi[(data.e00100 >= 40000) & (data.e00100 < 50000)] = 8
    agi[(data.e00100 >= 50000) & (data.e00100 < 75000)] = 9
    agi[(data.e00100 >= 75000) & (data.e00100 < 100000)] = 10
    agi[(data.e00100 >= 100000) & (data.e00100 < 200000)] = 11
    agi[(data.e00100 >= 200000) & (data.e00100 < 500000)] = 12
    agi[(data.e00100 >= 500000) & (data.e00100 < 1e6)] = 13
    agi[(data.e00100 >= 1e6) & (data.e00100 < 1.5e6)] = 14
    agi[(data.e00100 >= 1.5e6) & (data.e00100 < 2e6)] = 15
    agi[(data.e00100 >= 2e6) & (data.e00100 < 5e6)] = 16
    agi[(data.e00100 >= 5e6) & (data.e00100 < 1e7)] = 17
    agi[(data.e00100 >= 1e7)] = 18

    data['agi_bin'] = agi

    return data

if __name__ == '__main__':
    sys.exit(main())
