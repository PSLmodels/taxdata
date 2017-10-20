"""
Create tax units using the 2013 and 2014 CPS
"""
import pandas as pd
import numpy as np
from tqdm import tqdm


class Returns(object):
    """
    Class used to create tax units
    """
    def __init__(self, cps, year):
        """
        Parameters
        ----------
        cps: CPS file used
        year: year the CPS file is from
        """
        # Set CPS and household numbers in the file
        self.cps = cps
        self.year = year
        self.h_nums = np.unique(self.cps['h_seq'].values)
        self.nunits = 0

        # Set filing income thresholds
        self.single = 10150
        self.single65 = 11700
        self.hoh = 13050
        self.hoh65 = 14600
        self.joint = 20300
        self.joint65one = 21500
        self.joint65both = 22700
        self.widow = 16350
        self.widow65 = 17550
        self.depwages = 0
        self.depTotal = 1000
        # Wage thresholds for non-dependent filers
        self.wage1 = 1000
        self.wage2 = 250
        self.wage2nk = 10000
        self.wage3 = 1
        # Dependent exemption
        self.depExempt = 3950

        # Lists to hold tax units in each household
        self.house_units = list()
        self.tax_units = list()

        # Set flags in CPS file
        self.cps['h_flag'] = False  # Tax unit head flag
        self.cps['s_flag'] = False  # Tax unit spouse flag
        self.cps['d_flag'] = False  # Tax Unit Dependent flag
        self.cps['flag'] = False  # General flag

    @staticmethod
    def check_age(record, age, dependent=False):
        """
        Check the age of an individual and adjust age variable accordingly

        Parameters
        ----------
        record: record counting the ages
        age: age of individual
        dependent: True/False indicator for whether or not the person being
                   added is a dependent
        Returns
        -------
        None
        """
        if age < 18:
            record['nu18'] += 1
            if dependent:
                record['nu18_dep'] += 1
                if age <= 5:
                    record['nu05'] += 1
                elif age <= 13:
                    record['nu13'] += 1
        elif 18 <= age < 21:
            record['n1821'] += 1
        elif age >= 21:
            record['n21'] += 1
            if age >= 65 and dependent:
                record['elderly_dependent'] += 1

    @staticmethod
    def totincx(unit):
        """
        Calculate total income for the unit
        Parameters
        ----------
        unit: unit income is being calculated for

        Returns
        -------
        total income
        """
        totinc = (unit['was'] + unit['intst'] + unit['dbe'] + unit['alimony'] +
                  unit['bil'] + unit['pensions'] + unit['rents'] +
                  unit['fil'] + unit['ucomp'] + unit['socsec'])
        return totinc

    @staticmethod
    def add_benefit(person, record, pos):
        """
        Add imputed benefit value of an individual to a tax unit
        Parameters
        ----------
        person: person benefits are being counted for
        record: main record
        pos: person's position in the record file

        Returns
        -------
        None
        """
        ben_list = [('ssi', 'SSI', 'ssi_impute'),
                    ('snap', 'SNAP', 'snap_impute'),
                    ('ss', 'SS', 'ss_val_y'),
                    ('vb', 'VB', 'vb_impute'),
                    ('mcare', 'MCARE', 'MedicareX'),
                    ('mcaid', 'MCAID', 'MedicaidX')]
        for a, b, c in ben_list:
            record[b] += person[c]
            record['{}_PROB{}'.format(b, pos)] = person['{}_probs'.format(a)]
            record['{}_VAL{}'.format(b, pos)] = person[c]

    def computation(self):
        """
        Construct CPS tax units based on type of household
        """
        # IN 2015 alimony was moved to other Income
        if self.year == 2015:
            self.cps['alm_val'] = np.where(self.cps['oi_off'] == 20,
                                           self.cps['oi_val'], 0.)
        for num in tqdm(self.h_nums):
            self.nunits = 0
            # Clear house_units list
            del self.house_units[:]
            # Pull households from the CPS
            household = self.cps[self.cps['h_seq'] == num]
            household = household.sort_values('a_lineno')
            house_dict = household.to_dict('records')
            # Set flag for household type
            single = (house_dict[0]['h_type'] == 6 or
                      house_dict[0]['h_type'] == 7)
            group = house_dict[0]['h_type'] == 9

            # Call create function for each household
            # Single persons living alone
            if single:
                self.house_units.append(self.create(house_dict[0], house_dict))
            # Group households
            elif group:
                for person in house_dict:
                    self.house_units.append(self.create(person, house_dict))
            else:  # All other household types
                for person in house_dict:
                    # Only call method if not flagged:
                    not_flagged = (not person['h_flag'] and
                                   not person['s_flag'] and
                                   not person['d_flag'])
                    if not_flagged:
                        self.house_units.append(self.create(person,
                                                            house_dict))
                    # Check if a dependent must file
                    if not person['s_flag'] and person['d_flag']:
                        if self.must_file(person):
                            self.house_units.append(self.create(person,
                                                                house_dict))
                    # Search for dependencies in the household
                    if self.nunits > 1:
                        self.search()
            # Check head of household status
            [self.hhstatus(unit) for unit in self.house_units]

            # Add each unit to full tax unit list
            for unit in self.house_units:
                if not unit['t_flag']:
                    continue
                self.tax_units.append(self.output(unit, house_dict))
        final_output = pd.DataFrame(self.tax_units)
        # final_output.to_csv('cpsrets2013.csv', index=False)
        print 'There are {} tax units in the {} file'.format(len(final_output),
                                                             self.year)
        return final_output

    def create(self, record, house):
        """
        Create a CPS tax unit
        Parameters
        ----------
        record: dictionary record for the head of the unit
        house: list of dictionaries, each containing a member of the household

        Returns
        -------
        A completed tax unit
        """
        # Set head of hosuehold as record
        self.nunits += 1
        # Flag head of hosuehold
        record['flag'] = True

        # Income items
        record['was'] = record['wsal_val']
        record['wasp'] = record['was']
        record['intst'] = record['int_val']
        record['intstp'] = record['intst']
        record['dbe'] = record['div_val']
        record['dbep'] = record['dbe']
        record['alimony'] = record['alm_val']
        record['alimonyp'] = record['alimony']
        record['bil'] = record['semp_val']
        record['bilp'] = record['bil']
        record['pensions'] = record['rtm_val']
        record['pensionsp'] = record['pensions']
        record['rents'] = record['rnt_val']
        record['rentsp'] = record['rents']
        record['fil'] = record['frse_val']
        record['filp'] = record['fil']
        record['ucomp'] = record['uc_val']
        record['socsec'] = record['ss_val_x']

        # Weights and flags
        record['wt'] = record['fsup_wgt']
        record['ifdept'] = record['d_flag']  # Tax unit dependent flag
        record['h_flag'] = True  # Tax unit head flag

        # CPS identifiers
        record['xhid'] = record['h_seq']
        record['xfid'] = record['ffpos']
        record['xpid'] = record['ph_seq']
        record['xstate'] = record['gestfips']
        record['xregion'] = record['gereg']
        # CPS evaluation criteria (head)
        record['zifdep'] = record['d_flag']   # Tax unit dependent flag
        record['zntdep'] = 0
        record['zhhinc'] = record['hhinc']
        record['zagept'] = record['a_age']
        record['zagesp'] = 0
        record['zoldes'] = 0
        record['zyoung'] = 0
        record['zworkc'] = record['wc_val']
        record['zsocse'] = record['ss_val_x']
        record['zssinc'] = record['ssi_val']
        record['zpubas'] = record['paw_val']
        record['zvetbe'] = record['vet_val']
        record['zchsup'] = 0
        record['zfinas'] = 0
        record['zdepin'] = 0
        record['zowner'] = 0
        record['zwaspt'] = record['wsal_val']
        record['zwassp'] = 0
        # blindness indicators
        record['blind_head'] = 0
        record['blind_spouse'] = 0
        if record['pediseye'] == 1:
            record['blind_head'] = 1
        # Homeownership flag
        if self.nunits == 1 and record['h_tenure'] == 1:
            record['zowner'] = 1

        # marital status
        ms = record['a_maritl']
        record['ms_type'] = 1
        if ms == 1 or ms == 2 or ms == 3:
            record['ms_type'] = 2

        record['sp_ptr'] = record['a_spouse']  # pointer to spouse's record
        record['relcode'] = record['a_exprrp']
        record['ftype'] = record['ftype']
        record['ageh'] = record['a_age']
        if record['ageh'] >= 65:
            record['agede'] = 1
        else:
            record['agede'] = 0
        # Age related variables
        record['nu05'] = 0  # only checked for dependents
        record['nu13'] = 0  # only checked for dependents
        record['nu18_dep'] = 0
        record['nu18'] = 0
        record['n1821'] = 0
        record['n21'] = 0
        record['elderly_dependent'] = 0
        self.check_age(record, record['a_age'])
        record['depne'] = 0
        record['ages'] = np.nan  # age of spouse
        record['wass'] = 0.  # spouse's wage
        record['intsts'] = 0.  # spouse's interest income
        record['dbes'] = 0.  # spouse's dividend income
        record['alimonys'] = 0.  # spouse's alimony
        record['bils'] = 0.  # spouse's business income
        record['pensionss'] = 0.  # spouse's pension
        record['rentss'] = 0.  # spouse's rental income
        record['fils'] = 0.  # spouse's farm income

        # Single and separated individuals
        if record['ms_type'] == 1:
            record['js'] = 1
            # Certain single individuals can file as head of household
            if ((record['h_type'] == 6 or
                 record['h_type'] == 7) and record['h_numper'] == 1):
                if ms == 6:
                    record['js'] = 3
        else:  # all other household types
            record['js'] = 2
            if record['sp_ptr'] != 0:
                # locate the spouse's record
                try:
                    spouse = house[record['sp_ptr'] - 1]
                except IndexError:
                    # For households whose records are not in order, loop
                    # through the house to search for the spouse
                    for person in house:
                        if (person['a_lineno'] == record['a_spouse'] and
                                person['a_spouse'] == record['a_lineno']):
                            spouse = person
                            break
                record['ages'] = spouse['a_age']
                if record['ages'] >= 65:
                    record['agede'] += 1
                self.check_age(record, spouse['a_age'])
                # Income variable
                record['wass'] = spouse['wsal_val']
                record['was'] += record['wass']
                record['intst'] += spouse['int_val']
                record['intsts'] = spouse['int_val']
                record['dbe'] += spouse['div_val']
                record['dbes'] = spouse['div_val']
                record['alimony'] += spouse['alm_val']
                record['alimonys'] = spouse['alm_val']
                record['bil'] += spouse['semp_val']
                record['bils'] = spouse['semp_val']
                record['pensions'] += spouse['rtm_val']
                record['pensionss'] = spouse['rtm_val']
                record['rents'] += spouse['rnt_val']
                record['rentss'] = spouse['rnt_val']
                record['fil'] += spouse['frse_val']
                record['fils'] = spouse['frse_val']
                record['ucomp'] += spouse['uc_val']
                record['socsec'] += spouse['ss_val_y']
                # Tax unit spouse flag
                spouse['s_flag'] = True

                # CPS evaluation criteria
                record['zagesp'] = spouse['a_age']
                record['zworkc'] += spouse['wc_val']
                record['zsocse'] += spouse['ss_val_x']
                record['zssinc'] += spouse['ssi_val']
                record['zpubas'] += spouse['paw_val']
                record['zvetbe'] += spouse['vet_val']
                record['zchsup'] += 0
                record['zfinas'] += 0
                record['zwassp'] = spouse['wsal_val']

                # blindness indicator
                if spouse['pediseye'] == 1:
                    record['blind_spouse'] = 1

        # construct tax unit
        for i in range(21, 37):
            record[i] = 0.
        for i in range(67, 83):
            record[i] = 0.

        record['xschb'] = 0
        record['xschf'] = 0
        record['xsche'] = 0
        record['xschc'] = 0
        if record['intst'] > 400.:
            record['xschb'] = 1
        if record['fil'] != 0:
            record['xschf'] = 1
        if record['rents'] != 0:
            record['xsche'] = 1
        if record['bil'] != 0:
            record['xschc'] = 1
        record['xxoodep'] = 0
        record['xxopar'] = 0
        record['xxtot'] = 0

        # health insurance coverage
        record['110'] = 0
        record['111'] = 0
        record['112'] = 0
        record['113'] = np.nan
        record['114'] = np.nan
        record['115'] = np.nan
        if record['sp_ptr'] != 0:
            record['113'] = 0
            record['114'] = 0
            record['115'] = 0
        # pension coverage
        record['116'] = 0
        record['117'] = 0
        record['118'] = np.nan
        record['119'] = np.nan
        if record['sp_ptr'] != 0:
            record['118'] = 0
            record['119'] = 0
        # health status
        record['120'] = 0
        record['121'] = np.nan
        if record['sp_ptr'] != 0:
            record['121'] = 0
        # miscellaneous income amounts
        record['122'] = record['ssi_val']  # SSI
        record['123'] = record['paw_val']  # public assistance (TANF)
        record['124'] = record['wc_val']  # workers comp
        record['125'] = record['vet_val']  # veteran's benefits
        record['126'] = 0  # child support
        record['127'] = record['dsab_val']  # disability income
        record['128'] = record['ss_val_x']  # social security income
        record['129'] = record['zowner']
        record['130'] = 0  # wage share
        if record['sp_ptr'] != 0:
            record['122'] += spouse['ssi_val']
            record['123'] += spouse['paw_val']
            record['124'] += spouse['wc_val']
            record['125'] += spouse['vet_val']
            record['126'] = 0
            record['127'] += spouse['dsab_val']
            record['128'] += spouse['ss_val_x']
            totalwas = record['was']
            # Find total wage share
            if totalwas > 0:
                record['130'] = record['wasp'] / float(totalwas)
        # Additional health related variables
        record['135'] = record['ljcw']
        record['136'] = record['wemind']
        record['137'] = record['penatvty']
        record['138'] = np.nan
        record['139'] = np.nan
        record['140'] = np.nan
        record['141'] = np.nan
        if record['sp_ptr'] != 0:
            record['139'] = spouse['ljcw']
            record['140'] = spouse['wemind']
            record['141'] = spouse['penatvty']
        # self-employed industry - head and spouse
        classofworker = record['ljcw']
        majorindustry = 0
        senonfarm = 0
        sefarm = 0
        if classofworker == 6:
            senonfarm = record['semp_val']
            sefarm = record['frse_val']
            majorindustry = record['wemind']
        if record['sp_ptr'] != 0:
            classofworker = spouse['ljcw']
            if classofworker == 6:
                senonfarm_sp = spouse['semp_val']
                sefarm_sp = spouse['frse_val']
                if abs(senonfarm_sp) > abs(senonfarm):
                    majorindustry = spouse['wemind']
                    senonfarm += senonfarm_sp
                    sefarm += sefarm_sp

        record['146'] = majorindustry
        record['147'] = senonfarm
        record['148'] = sefarm

        # retirement income
        record['191'] = record['ret_val1']
        record['192'] = record['ret_sc1']
        record['193'] = record['ret_val2']
        record['194'] = record['ret_sc2']
        record['195'] = np.nan
        record['196'] = np.nan
        record['197'] = np.nan
        record['198'] = np.nan

        if record['sp_ptr'] != 0:
            record['195'] = spouse['ret_val1']
            record['196'] = spouse['ret_sc1']
            record['197'] = spouse['ret_val2']
            record['198'] = spouse['ret_sc2']
        # disability income

        record['199'] = record['dis_val1']
        record['200'] = record['dis_sc1']
        record['201'] = record['dis_val2']
        record['202'] = record['dis_sc2']
        record['203'] = np.nan
        record['204'] = np.nan
        record['205'] = np.nan
        record['206'] = np.nan
        if record['sp_ptr'] != 0:
            record['203'] = spouse['dis_val1']
            record['204'] = spouse['dis_sc1']
            record['205'] = spouse['dis_val2']
            record['206'] = spouse['dis_sc2']

        # survivor income

        record['207'] = record['sur_val1']
        record['208'] = record['sur_sc1']
        record['209'] = record['sur_val2']
        record['210'] = record['sur_sc2']
        record['211'] = np.nan
        record['212'] = np.nan
        record['213'] = np.nan
        record['214'] = np.nan

        if record['sp_ptr'] != 0:
            record['211'] = spouse['sur_val1']
            record['212'] = spouse['sur_sc1']
            record['213'] = spouse['sur_val2']
            record['214'] = spouse['sur_sc2']

        # veterans income

        record['215'] = record['vet_typ1']
        record['216'] = record['vet_typ2']
        record['217'] = record['vet_typ3']
        record['218'] = record['vet_typ4']
        record['219'] = record['vet_typ5']
        record['220'] = record['vet_val']
        record['221'] = np.nan
        record['222'] = np.nan
        record['223'] = np.nan
        record['224'] = np.nan
        record['225'] = np.nan
        record['226'] = np.nan
        if record['sp_ptr'] != 0:
            record['221'] = spouse['vet_typ1']
            record['222'] = spouse['vet_typ2']
            record['223'] = spouse['vet_typ3']
            record['224'] = spouse['vet_typ4']
            record['225'] = spouse['vet_typ5']
            record['226'] = spouse['vet_val']
        # taxpayer
        record['236'] = record['paw_val']
        record['237'] = record['mcaid']
        record['238'] = record['pchip']
        record['239'] = record['wicyn']
        record['240'] = record['ssi_val']
        record['241'] = record['hi_yn']
        record['242'] = record['hiown']
        record['243'] = record['hiemp']
        record['244'] = record['hipaid']
        record['245'] = record['emcontrb']
        record['246'] = record['hi']
        record['247'] = record['hityp']
        record['248'] = record['paid']
        record['249'] = record['priv']
        record['250'] = record['prityp']
        record['251'] = record['ss_val_x']
        record['252'] = record['uc_val']
        record['253'] = record['mcare']
        record['254'] = record['wc_val']
        record['255'] = record['vet_val']
        record['256'] = np.nan
        record['257'] = np.nan
        record['258'] = np.nan
        record['259'] = np.nan
        record['260'] = np.nan
        record['261'] = np.nan
        record['262'] = np.nan
        record['263'] = np.nan
        record['264'] = np.nan
        record['265'] = np.nan
        record['266'] = np.nan
        record['267'] = np.nan
        record['268'] = np.nan
        record['269'] = np.nan
        record['270'] = np.nan
        record['271'] = np.nan
        record['272'] = np.nan
        record['273'] = np.nan
        record['274'] = np.nan
        record['275'] = np.nan

        if record['sp_ptr'] != 0:
            record['256'] = spouse['paw_val']
            record['257'] = spouse['mcaid']
            record['258'] = spouse['pchip']
            record['259'] = spouse['wicyn']
            record['260'] = spouse['ssi_val']
            record['261'] = spouse['hi_yn']
            record['262'] = spouse['hiown']
            record['263'] = spouse['hiemp']
            record['264'] = spouse['hipaid']
            record['265'] = spouse['emcontrb']
            record['266'] = spouse['hi']
            record['267'] = spouse['hityp']
            record['268'] = spouse['paid']
            record['269'] = spouse['priv']
            record['270'] = spouse['prityp']
            record['271'] = spouse['ss_val_x']
            record['272'] = spouse['uc_val']
            record['273'] = spouse['mcare']
            record['274'] = spouse['wc_val']
            record['275'] = spouse['vet_val']
        # Check spouse's age
        if record['sp_ptr'] != 0:
            self.check_age(record, spouse['a_age'])
        # Add imputed benefits data
        ben_list = [('ssi', 'SSI', 'ssi_impute'),
                    ('snap', 'SNAP', 'snap_impute'),
                    ('ss', 'SS', 'ss_val_y'),
                    ('vb', 'VB', 'vb_impute'),
                    ('mcare', 'MCARE', 'MedicareX'),
                    ('mcaid', 'MCAID', 'MedicaidX')]
        for a, b, c in ben_list:
            record[b] = record[c]
            record['{}_PROB1'.format(b)] = record['{}_probs'.format(a)]
            record['{}_VAL1'.format(b)] = record[c]
            if record['sp_ptr'] != 0:
                record[b] += record[c]
                record['{}_PROB2'.format(b)] = spouse['{}_probs'.format(a)]
                record['{}_VAL2'.format(b)] = spouse[c]
            else:
                record['{}_PROB2'.format(b)] = 0.
                record['{}_VAL2'.format(b)] = 0.
            for i in range(3, 16):
                record['{}_PROB{}'.format(b, str(i))] = 0.
                record['{}_VAL{}'.format(b, str(i))] = 0.
            record['ben_number'] = 3  # track how many benefits have been added
        # Search for dependents in the household
        for person in house:
            idxfid = person['ffpos']
            idxhea = person['h_flag']
            idxspo = person['s_flag']
            idxdep = person['d_flag']

            search = ((house.index(person) != house.index(record)) and
                      idxfid == record['xfid'] and not idxdep and
                      not idxspo and not idxhea)
            if search:
                person['d_flag'] = self.ifdept(person, record)
            if person['d_flag']:
                self.addept(person, record, house.index(person))
        record['t_flag'] = True
        return record

    def hhstatus(self, unit):
        """
        Determine head of household status

        Parameters
        ----------
        unit: a tax unit

        Returns
        -------
        None
        """
        income = 0
        # Find total income for the tax unit
        for iunit in self.house_units:
            totinc = self.totincx(iunit)
            income += totinc
        # Find total income for the individual
        if income > 0:
            totinc_i = self.totincx(unit)
            indjs = unit['js']  # Filing status
            indif = unit['ifdept']  # Dependency status
            inddx = unit['depne']  # number of dependent exemptions
            if indjs == 1 and float(totinc_i) / income > 0.99:
                if indif != 1 and inddx > 0:
                    unit['js'] = 3

    def must_file(self, record):
        """
        Determine if a dependent must file a return
        Parameters
        ----------
        record: record for the dependent

        Returns
        -------
        True if person must file, False otherwise
        """
        wages = record['wsal_val']
        income = (wages + record['semp_val'] + record['frse_val'] +
                  record['uc_val'] + record['ss_val_x'] + record['rtm_val'] +
                  record['int_val'] + record['div_val'] + record['rnt_val'] +
                  record['alm_val'])
        # determine if dependent exceeds filing thresholds
        depfile = wages > self.depwages or income > self.depTotal
        return depfile

    def convert(self, ix, iy):
        """
        Convert an existing tax unit (ix) into a dependent filer of (iy)

        Parameters
        ----------
        ix: index location of tax unit to be converted
        iy: index location of targeted tax unit

        Returns
        -------
        None
        """
        self.house_units[ix]['ifdept'] = True
        ixdeps = self.house_units[ix]['depne']
        iydeps = self.house_units[iy]['depne']
        self.house_units[ix]['depne'] = 0
        ixjs = self.house_units[ix]['js']
        if ixjs == 2:
            self.house_units[iy]['depne'] += ixdeps + 2
            # Add location of two new dependets
            self.house_units[iy]['dep' + str(iydeps + 1)] = ix
            self.house_units[iy][('dep' +
                                  str(iydeps +
                                      2))] = self.house_units[ix]['sp_ptr']
            # Add ages of two new dependents
            self.house_units[iy][('depage' +
                                  str(iydeps +
                                      1))] = self.house_units[ix]['a_age']
            self.house_units[iy][('depage' +
                                  str(iydeps +
                                      2))] = self.house_units[ix]['ages']
            iybgin = iydeps + 2
        else:
            self.house_units[iy]['depne'] += ixdeps + 1
            self.house_units[iy]['dep' + str(iydeps + 1)] = ix
            self.house_units[iy][('depage' +
                                  str(iydeps +
                                      1))] = self.house_units[ix]['a_age']
            iybgin = iydeps + 1
        if ixdeps > 0:
            # Assign any dependents to target record
            for ndeps in range(1, ixdeps + 1):
                dep = 'dep' + str(iybgin + ndeps)
                depx = 'dep' + str(ndeps)
                depage = 'depage' + str(iybgin + ndeps)
                depagex = 'depage' + str(ndeps)
                self.house_units[iy][dep] = self.house_units[ix][depx]
                self.house_units[ix][dep] = 0
                self.house_units[iy][depage] = self.house_units[ix][depagex]
        # Add age variables together
        self.house_units[iy]['nu05'] += self.house_units[ix]['nu05']
        self.house_units[iy]['nu13'] += self.house_units[ix]['nu13']
        self.house_units[iy]['nu18_dep'] += self.house_units[ix]['nu18_dep']
        self.house_units[iy]['nu18'] += self.house_units[ix]['nu18']
        self.house_units[iy]['n1821'] += self.house_units[ix]['n1821']
        self.house_units[iy]['n21'] += self.house_units[ix]['n21']
        elderly = self.house_units[ix]['elderly_dependent']
        self.house_units[iy]['elderly_dependent'] += elderly

    @staticmethod
    def relation(person, record):
        """
        Determine relationship between subfamilies

        Parameters
        -----------
        person: individual being checked
        record: record they may be related to

        Returns
        -------
        Code for related
        """
        ref_person = record['a_exprrp']
        index_person = person['a_exprrp']
        if ref_person == 5:
            genref = -1
        elif ref_person == 7:
            genref = -2
        elif ref_person == 8:
            genref = 1
        elif ref_person == 9:
            genref = 0
        elif ref_person == 11:
            genref = -1
        else:
            genref = 99

        if index_person == 5:
            genind = -1
        elif index_person == 7:
            genind = -2
        elif index_person == 8:
            genind = 1
        elif index_person == 9:
            genind = 0
        elif index_person == 11:
            genind = -1
        else:
            genind = 99

        if genref != 99 and genind != 99:
            related = genind = genref
        else:
            related = 99
        return related

    def ifdept(self, person, record):
        """
        Determine if an individual is a dependent of the reference person
        Five tests must be passed for an individual to be a dependent:
            1. Relationship
            2. Marital status
            3. Citizenship
            4. Income
            5. Support
        Parameters
        ----------
        person: individual being evaluated
        record: reference person

        Returns
        -------
        True if person is a dependent, false otherwise
        """
        test1 = 1  # Only looking at families so assume test is passed
        test2 = 1  # Only looking at families so assume test is passed
        test3 = 1  # Assume citizenship requirment is always met
        test4 = 0
        test5 = 0
        dflag = False
        age = person['a_age']
        income = (person['wsal_val'] + person['semp_val'] +
                  person['frse_val'] + person['uc_val'] + person['ss_val_y'] +
                  person['rtm_val'] + person['int_val'] + person['int_val'] +
                  person['div_val'] + person['rnt_val'] + person['alm_val'])
        related = self.relation(person, record)
        if income <= 2500:
            test4 = 1
        if record['relcode'] == 5 or related == -1:
            if age <= 18 or age <= 23 and record['a_enrlw'] > 0:
                test4 = 1
        totinc = self.totincx(record)
        if totinc + income > 0:
            if income / float(totinc + income) < 0.5:
                test5 = 1
        else:
            test5 = 1
        dtest = test1 + test2 + test3 + test4 + test5
        if dtest == 5:
            dflag = True

        return dflag

    def addept(self, person, record, p_index):
        """
        Add a dependent to a tax unit file

        Parameters
        ----------
        person: individual being claimed as a dependent
        record: reference person
        p_index: index of the person being claimed
        """
        person['d_flag'] = True
        record['depne'] += 1
        depne = record['depne']
        record['dep' + str(depne)] = p_index
        # Add age of the dependent to age variables
        self.check_age(record, person['a_age'], True)
        record['depage' + str(depne)] = person['a_age']
        # Add benefit variables to record
        self.add_benefit(person, record, record['ben_number'])
        record['ben_number'] += 1

    def filst(self, record):
        """
        Determines if a tax unit files a return using five tests
            1. Wage test: If anyone in the unit had wage and salary income, the
                          unit is deemed to be a filer
            2. Gross income test. The income thresholds in the 1040 filing
               requirements are used to determine if the tax unit has to file.
            3. Dependent filer test. Individuals who are claimed as dependents,
               but are required to file a return
            4. Random selection
            5. Negative income

        Parameters
        ----------
        record: a tax unit

        Returns
        -------
        filing status
        """
        # Wage and gross income tests
        income = (record['was'] + record['intst'] + record['dbe'] +
                  record['alimony'] + record['bil'] + record['pensions'] +
                  record['rents'] + record['fil'] + record['ucomp'])
        if record['js'] == 1:  # Single filers
            if record['was'] >= self.wage1:
                return 1
            else:  # income test
                amount = self.single - self.depExempt * record['depne']
                if income >= amount:
                    return 1

        elif record['js'] == 2:  # Joint filers
            if record['depne'] > 0:
                if record['was'] >= self.wage2:
                    return 1
            else:
                if record['was'] >= self.wage2nk:
                    return 1
            # income tests
            amount = self.joint - self.depExempt * record['depne']
            if record['agede'] == 1:
                amount = self.joint65one - self.depExempt * record['depne']
            elif record['agede'] == 2:
                amount = self.joint65both - self.depExempt * record['depne']
            if income >= amount:
                return 1

        elif record['js'] == 3:  # Head of household filers
            if record['was'] >= self.wage3:
                return 1
            else:
                amount = self.hoh
                if record['agede'] != 0:
                    amount = self.hoh65 - self.depExempt * record['depne']
                if income >= amount:
                    return 1

        # Dependent filer test
        if record['ifdept']:
            return 1
        # Random selection
        fils = (record['js'] == 3 and record['agede'] > 0 and
                income < 6500 and record['depne'] < 0)
        if fils:
            return 1
        # Negative income test
        if record['bil'] < 0 or record['fil'] < 0 or record['rents'] < 0:
            return 1

    def search(self):
        """
        Search for dependencies among tax units
        """
        highest = -9.9e32
        idxhigh = 0
        for unit in self.house_units:
            totinc = self.totincx(unit)
            if totinc >= highest:
                highest = totinc
                idxhigh = self.house_units.index(unit)
        # If the unit isn't already a dependent, search for dependents
        if not self.house_units[idxhigh]['ifdept']:
            for ix in range(0, self.nunits):
                unit = self.house_units[ix]
                idxjs = unit['js']
                idxdepf = unit['ifdept']
                idxrelc = unit['a_exprrp']
                idxfamt = unit['ftype']
                convert1 = (ix != idxhigh and not idxdepf and highest > 0 and
                            idxjs != 2)
                if convert1:
                    if idxfamt == 1 or idxfamt == 3 or idxfamt == 5:
                        totinc = self.totincx(unit)
                        if totinc <= 0.:
                            unit['t_flag'] = False
                            self.convert(ix, idxhigh)
                        elif 0. < totinc <= 3000.:
                            self.convert(ix, idxhigh)
                    if idxrelc == 11:
                        unit['t_flag'] = False
                        self.convert(ix, idxhigh)

    def output(self, unit, house):
        """
        After the tax units have been created, output all records

        Parameters
        ----------
        unit: head of tax unit
        house: household of tax unit

        Returns
        -------
        Completed tax unit
        """
        record = {}
        depne = unit['depne']
        # Many variables keep the same name in the final file
        repeated_vars = ['js', 'ifdept', 'agede', 'depne', 'ageh',
                         'ages', 'was', 'intst', 'dbe', 'alimony', 'bil',
                         'pensions', 'rents', 'fil', 'ucomp', 'socsec',
                         'wt', 'zifdep', 'zntdep', 'zhhinc', 'zagept',
                         'zagesp', 'zoldes', 'zyoung', 'zworkc', 'zsocse',
                         'zssinc', 'zpubas', 'zvetbe', 'zchsup', 'zdepin',
                         'zowner', 'zwaspt', 'zwassp', 'wasp', 'wass', 'nu18',
                         'n1821', 'n21', 'SSI', 'SS', 'SNAP', 'VB', 'MCARE',
                         'MCAID', 'xstate', 'xregion', 'xschf', 'xschb',
                         'xsche', 'xschc', 'xhid', 'xfid', 'xpid',
                         'intstp', 'intsts', 'dbep', 'dbes', 'alimonyp',
                         'alimonys', 'pensionsp', 'pensionss', 'rentsp',
                         'rentss', 'filp', 'fils', 'bilp', 'bils', 'hi',
                         'paid', 'priv']
        for i in range(1, 16):
            repeated_vars.append('SSI_PROB{}'.format(str(i)))
            repeated_vars.append('SSI_VAL{}'.format(str(i)))
            repeated_vars.append('SS_PROB{}'.format(str(i)))
            repeated_vars.append('SS_VAL{}'.format(str(i)))
            repeated_vars.append('SNAP_PROB{}'.format(str(i)))
            repeated_vars.append('SNAP_VAL{}'.format(str(i)))
            repeated_vars.append('MCARE_PROB{}'.format(str(i)))
            repeated_vars.append('MCARE_VAL{}'.format(str(i)))
            repeated_vars.append('MCAID_PROB{}'.format(str(i)))
            repeated_vars.append('MCAID_VAL{}'.format(str(i)))
            repeated_vars.append('VB_PROB{}'.format(str(i)))
            repeated_vars.append('VB_VAL{}'.format(str(i)))
        for var in repeated_vars:
            record[var] = unit[var]

        txpye = 1
        if unit['js'] == 2:
            txpye = 2
        record['xxtot'] = txpye + depne

        # Check relationship codes among dependents
        xxoodep = 0
        xxopar = 0
        xxocah = 0
        record['xxocawh'] = 0
        if depne > 0:
            for i in range(1, depne + 1):
                dindex = unit['dep' + str(i)]
                drel = house[dindex]['a_exprrp']
                dage = house[dindex]['a_age']
                if drel == 8:
                    xxopar += 1
                if drel >= 9 and dage >= 18:
                    xxoodep += 1
                if dage < 18:
                    xxocah += 1
        oldest = 0
        youngest = 0
        if depne > 0:
            oldest = -9.9e16
            youngest = 9.9e16
            for i in range(1, depne + 1):
                dage = unit['depage' + str(i)]
                if dage > oldest:
                    oldest = dage
                if dage < youngest:
                    youngest = dage
            record['zoldes'] = oldest
            record['zyoungest'] = youngest
        record['oldest'] = oldest
        record['youngest'] = youngest

        # Dependent income
        zdepin = 0.
        if depne > 0:
            for i in range(1, depne + 1):
                dindex = unit['dep' + str(i)]
                if not house[dindex]['flag']:
                    zdepin = (house[dindex]['wsal_val'] +
                              house[dindex]['semp_val'] +
                              house[dindex]['frse_val'] +
                              house[dindex]['uc_val'] +
                              house[dindex]['ss_val_x'] +
                              house[dindex]['semp_val'] +
                              house[dindex]['rtm_val'] +
                              house[dindex]['int_val'] +
                              house[dindex]['div_val'] +
                              house[dindex]['alm_val'])
        record['zdepin'] = zdepin
        record['income'] = self.totincx(unit)
        record['filst'] = self.filst(unit)

        # add spouse records used in blank slate imputations
        record['hi_spouse'] = unit['266']
        record['paid_spouse'] = unit['268']
        record['priv_spouse'] = unit['269']
        return record
