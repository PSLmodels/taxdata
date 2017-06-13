"""
Class for creating CPS tax units
"""

import pandas as pd
import numpy as np
from tqdm import tqdm


class Returns(object):
    """
    Class used to create tax units from the CPS file
    """
    def __init__(self, cps):
        """
        Parameters
        ----------
        cps: CPS file used
        """
        # Set CPS and household numbers in the file
        self.cps = cps
        self.h_nums = np.unique(self.cps['h_seq'].values)
        self.nunits = 0

        # Set filing thresholds
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

    def computation(self):
        """
        Construct tax units based on type of household
        1. Single person living alone
        2. Persons living in group quarters
        3. All other family structures

        Returns
        -------
        CPS Tax Units file
        """
        # Extract each household from full CPS file
        # TODO: Check if this is actually needed
        self.cps['alm_val'] = 0
        for index, row in self.cps.iterrows():
            if row['oi_off'] == 20:
                row['alm_val'] = row['oi_off']

        for num in tqdm(self.h_nums):
            self.nunits = 0
            # Clear house_units list
            del self.house_units[:]
            # Pull households from CPS
            household = self.cps[self.cps['h_seq'] == num]
            household = household.sort_values('a_lineno')
            house_dict = household.to_dict('records')

            # Set flags for household type
            single = (house_dict[0]['h_type'] == 6 or
                      house_dict[0]['h_type'] == 7)
            group = house_dict[0]['h_type'] == 9
            # other = not single and not group

            # Call create for each household
            # Single persons living alone
            if single:
                self.house_units.append(self.create(house_dict[0], house_dict))
            elif group:
                for person in house_dict:
                    self.house_units.append(self.create(person, house_dict))
            else:
                for person in house_dict:
                    # Only call create method if not flagged
                    if (not person['h_flag'] and not
                            person['s_flag'] and not
                            person['d_flag']):
                        self.house_units.append(self.create(person,
                                                            house_dict))
                    # Check if dependent needs to file
                    if not person['s_flag'] and person['d_flag']:
                        if self.must_file(person):
                            self.house_units.append(self.create(person,
                                                                house_dict))
                    # Search for dependencies within the household
                    if self.nunits > 1:
                        self.tax_units_search()
            # Check for head of household status
            [self.hhstatus(unit) for unit in self.house_units]

            # Add each unit to full tax unit list
            for unit in self.house_units:
                if not unit['t_flag']:
                    continue
                self.tax_units.append(self.output(unit, house_dict))
        final_output = pd.DataFrame(self.tax_units)
        # final_output.to_csv('CPSRETS2014.csv', index=False)
        return final_output

    def create(self, record, house):
        """
        Create a CPS tax unit
        Parameters
        ----------
        record: dictionary record for the head of the unit
        house: list of dictionaries, each containing a memeber of the hosuehold

        Returns
        -------
        A tax unit
        """
        # Set head of household as record
        self.nunits += 1
        # Flag head of household
        record['flag'] = True

        # Income items
        was = record['wsal_val']
        wasp = was
        intst = record['int_val']
        dbe = record['div_val']
        alimony = record['alm_val']
        bil = record['semp_val']
        pensions = record['rtm_val']
        rents = record['rnt_val']
        fil = record['frse_val']
        ucomp = record['uc_val']
        socsec = record['ss_val']

        # Weights and flags
        wt = record['fsup_wgt']
        ifdept = record['d_flag']  # Tax unit dependent flag
        record['h_flag'] = True  # Tax unit head flag

        # CPS identifiers
        xhid = record['h_seq']
        xfid = record['ffpos']
        xpid = record['ph_seq']
        xstate = record['gestfips']
        xregion = record['gereg']
        # CPS evaluation criteria (head)
        zifdep = record['d_flag']   # Tax unit dependent flag
        zntdep = 0
        zhhinc = record['hhinc']
        zagept = record['a_age']
        zagesp = 0
        zoldes = 0
        zyoung = 0
        zworkc = record['wc_val']
        zsocse = record['ss_val']
        zssinc = record['ssi_val']
        zpubas = record['paw_val']
        zvetbe = record['vet_val']
        zchsup = 0
        zfinas = 0
        zdepin = 0
        zowner = 0
        zwaspt = record['wsal_val']
        zwassp = 0

        # home Ownership Flag
        if (self.nunits == 1) and (record['h_tenure'] == 1):
            zowner = 1

        # store dependents info
        for i in range(1, 17):
            record['dep' + str(i)] = np.nan
        for i in range(1, 17):
            record['depage' + str(i)] = np.nan

        # marital status
        ms = record['a_maritl']
        if ms == 1 or ms == 2 or ms == 3:
            ms_type = 2
        else:
            ms_type = 1
        sp_ptr = record['a_spouse']
        relcode = record['a_exprrp']
        # ftype = record['ftype']
        ageh = record['a_age']
        if ageh >= 65:
            agede = 1
        else:
            agede = 0
        # Age related variables
        record['nu05'] = 0  # Only checked for dependents
        record['nu13'] = 0  # Only checked for dependents
        record['nu18_dep'] = 0
        record['nu18'] = 0
        record['n1821'] = 0
        record['n21'] = 0
        record['elderly_dependent'] = 0
        if record['a_age'] < 18:
            record['nu18'] += 1
        if 18 <= record['a_age'] < 21:
            record['n1821'] += 1
        if record['a_age'] >= 21:
            record['n21'] += 1
        depne = 0
        ages = np.nan
        wass = 0
        # Single and separated individuals
        if ms_type == 1:
            js = 1
            ages = np.nan
            # Certain single individuals can file as head of household
            if ((record['h_type'] == 6 or
                 record['h_type'] == 7) and record['h_numper'] == 1):
                if ms == 6:
                    js = 3
        else:
            js = 2
            if sp_ptr != 0:
                # Pull the spouse's record
                try:
                    spouse = house[sp_ptr - 1]
                # For households whose records are not in order, loop through
                # the house to search for the spouse
                except IndexError:
                    for person in house:
                        if (person['a_lineno'] == record['a_spouse'] and
                                person['a_spouse'] == record['a_lineno']):
                            spouse = person
                            break
                ages = spouse['a_age']
                if ages >= 65:
                    agede += 1
                # Income items
                # Determine spouse's age bracket
                if spouse['a_age'] < 18:
                    record['nu18'] += 1
                if 18 <= spouse['a_age'] < 21:
                    record['n1821'] += 1
                if spouse['a_age'] >= 21:
                    record['n21'] += 1
                wass = spouse['wsal_val']
                was += wass
                intst += spouse['int_val']
                dbe += spouse['div_val']
                alimony += spouse['alm_val']
                bil += spouse['semp_val']
                pensions += spouse['rtm_val']
                rents += spouse['rnt_val']
                fil += spouse['frse_val']
                ucomp += spouse['uc_val']
                socsec += spouse['ss_val']
                # Tax unit spouse flag
                spouse['s_flag'] = True

                # CPS evaluation criteria
                zagesp = spouse['a_age']
                zworkc += spouse['wc_val']
                zsocse += spouse['ss_val']
                zssinc += spouse['ssi_val']
                zpubas += spouse['paw_val']
                zvetbe += spouse['vet_val']
                zchsup += 0
                zfinas += 0
                zwassp = spouse['wsal_val']

        if intst > 400:
            xschb = 1
        else:
            xschb = 0
        if fil != 0:
            xschf = 1
        else:
            xschf = 0
        if rents != 0:
            xsche = 1
        else:
            xsche = 0
        if bil != 0:
            xschc = 1
        else:
            xschc = 0

        record['101'] = record['a_age']
        record['102'] = np.nan
        if sp_ptr != 0:
            record['102'] = spouse['a_age']
        # health insurance coverage
        record['110'] = 0
        record['111'] = 0
        record['112'] = 0
        record['113'] = np.nan
        record['114'] = np.nan
        record['115'] = np.nan
        if sp_ptr != 0:
            record['113'] = 0
            record['114'] = 0
            record['115'] = 0

        # pension coverage
        record['116'] = 0
        record['117'] = 0
        record['118'] = np.nan
        record['119'] = np.nan
        if sp_ptr != 0:
            record['118'] = 0
            record['119'] = 0
        # health status
        record['120'] = 0
        record['121'] = np.nan
        if sp_ptr != 0:
            record['121'] = 0

        # miscellaneous income amounts
        record['122'] = record['ssi_val']  # SSI
        record['123'] = record['paw_val']  # public assistance (TANF)
        record['124'] = record['wc_val']  # workman's compensation
        record['125'] = record['vet_val']  # veteran's benefits
        record['126'] = 0  # child support
        record['127'] = record['dsab_val']  # disablility income
        record['128'] = record['ss_val']  # social security income
        record['129'] = zowner  # home ownership flag
        record['130'] = 0  # wage share
        if sp_ptr != 0:
            record['122'] += spouse['ss_val']
            record['123'] += spouse['paw_val']
            record['124'] += spouse['wc_val']
            record['125'] += spouse['vet_val']
            record['126'] = 0
            record['127'] += spouse['dsab_val']
            record['128'] += spouse['ss_val']
            totalwas = was
            # Find total wage share
            if totalwas > 0:
                record['130'] = wasp / float(totalwas)

        if self.nunits == 1:
            record['131'] = 0
            record['132'] = 0
            record['133'] = 0
        else:
            record['131'] = np.nan
            record['132'] = np.nan
            record['133'] = np.nan

        record['134'] = 0
        record['135'] = record['ljcw']
        record['136'] = record['wemind']
        record['137'] = record['penatvty']
        record['138'] = np.nan
        record['139'] = np.nan
        record['140'] = np.nan
        record['141'] = np.nan
        if sp_ptr != 0:
            record['138'] = 0
            record['139'] = spouse['ljcw']
            record['140'] = spouse['wemind']
            record['141'] = spouse['penatvty']

        record['142'] = record['a_hga']  # Educational attainment
        record['143'] = record['a_sex']  # Gender
        record['144'] = np.nan
        record['145'] = np.nan
        if sp_ptr != 0:
            record['144'] = spouse['a_hga']  # Spouse educational attainment
            record['145'] = spouse['a_sex']  # Spouse gender

        # self-employed industry - head and spouse
        classofworker = record['ljcw']
        majorindustry = 0
        senonfarm = 0
        sefarm = 0
        if classofworker == 6:
            senonfarm = record['semp_val']
            sefarm = record['frse_val']
            majorindustry = record['wemind']
        if sp_ptr != 0:
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

        record['151'] = record['a_age']
        record['152'] = record['care']
        record['153'] = record['caid']
        record['154'] = record['oth']
        record['155'] = record['hi']
        record['156'] = record['priv']
        record['157'] = record['paid']
        record['158'] = record['filestat']
        record['159'] = record['agi']
        record['160'] = 0  # capital gains no longer on file
        record['161'] = np.nan
        record['162'] = np.nan
        record['163'] = np.nan
        record['164'] = np.nan
        record['165'] = np.nan
        record['166'] = np.nan
        record['167'] = np.nan
        record['168'] = np.nan
        record['169'] = np.nan
        record['170'] = np.nan
        if sp_ptr != 0:
            record['161'] = spouse['a_age']
            record['162'] = spouse['care']
            record['163'] = spouse['caid']
            record['164'] = spouse['oth']
            record['165'] = spouse['hi']
            record['166'] = spouse['priv']
            record['167'] = spouse['paid']
            record['168'] = spouse['filestat']
            record['169'] = spouse['agi']
            record['170'] = 0

        record['171'] = record['wsal_val']
        record['172'] = record['int_val']
        record['173'] = record['div_val']
        record['174'] = record['alm_val']
        record['175'] = record['semp_val']
        record['176'] = record['rtm_val']
        record['177'] = record['rnt_val']
        record['178'] = record['frse_val']
        record['179'] = record['uc_val']
        record['180'] = record['ss_val']  # capital gains no longer on file
        record['181'] = np.nan
        record['182'] = np.nan
        record['183'] = np.nan
        record['184'] = np.nan
        record['185'] = np.nan
        record['186'] = np.nan
        record['187'] = np.nan
        record['188'] = np.nan
        record['189'] = np.nan
        record['190'] = np.nan
        if sp_ptr != 0:
            record['181'] = spouse['wsal_val']
            record['182'] = spouse['int_val']
            record['183'] = spouse['div_val']
            record['184'] = spouse['alm_val']
            record['185'] = spouse['semp_val']
            record['186'] = spouse['rtm_val']
            record['187'] = spouse['rnt_val']
            record['188'] = spouse['frse_val']
            record['189'] = spouse['uc_val']
            record['190'] = spouse['ss_val']

        # retirement income
        record['191'] = record['ret_val1']
        record['192'] = record['ret_sc1']
        record['193'] = record['ret_val2']
        record['194'] = record['ret_sc2']
        record['195'] = np.nan
        record['196'] = np.nan
        record['197'] = np.nan
        record['198'] = np.nan

        if sp_ptr != 0:
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
        if sp_ptr != 0:
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

        if sp_ptr != 0:
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
        if sp_ptr != 0:
            record['221'] = spouse['vet_typ1']
            record['222'] = spouse['vet_typ2']
            record['223'] = spouse['vet_typ3']
            record['224'] = spouse['vet_typ4']
            record['225'] = spouse['vet_typ5']
            record['226'] = spouse['vet_val']

        record['227'] = sp_ptr

        # household

        record['228'] = record['fhip_val']
        record['229'] = record['fmoop']
        record['230'] = record['fotc_val']
        record['231'] = record['fmed_val']
        record['232'] = record['hmcaid']
        record['233'] = record['hrwicyn']
        record['234'] = record['hfdval']
        record['235'] = record['care_val']

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
        record['251'] = record['ss_val']
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

        if sp_ptr != 0:
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
            record['271'] = spouse['ss_val']
            record['272'] = spouse['uc_val']
            record['273'] = spouse['mcare']
            record['274'] = spouse['wc_val']
            record['275'] = spouse['vet_val']

        totincx = (was + intst + dbe + alimony + bil + pensions + rents + fil +
                   ucomp + socsec)

        if not ifdept:
            # Search for dependents among other members of the household who
            # are not already claimed on another return.
            for individual in house:
                idxfid = individual['ffpos']
                idxhea = individual['h_flag']
                idxspo = individual['s_flag']
                idxdep = individual['d_flag']
                dflag = False
                if ((house.index(individual) != house.index(record)) and
                        idxfid == xfid and not idxdep and not idxspo and
                        not idxhea):
                    # Determine if Individual is a dependent of the reference
                    # person
                    test1 = 1
                    test2 = 1
                    test3 = 1
                    test4 = 0
                    test5 = 0
                    dflag = False
                    age = individual['a_age']
                    income = (individual['wsal_val'] + individual['semp_val'] +
                              individual['frse_val'] + individual['uc_val'] +
                              individual['ss_val'] + individual['rtm_val'] +
                              individual['int_val'] + individual['div_val'] +
                              individual['rnt_val'] + individual['alm_val'])
                    # set up child flag (related == -1)
                    reference_person = record['a_exprrp']
                    index_person = individual['a_exprrp']
                    if reference_person == 5:
                        genref = -1
                    elif reference_person == 7:
                        genref = -2
                    elif reference_person == 8:
                        genref = 1
                    elif reference_person == 9:
                        genref = 0
                    elif reference_person == 11:
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
                        related = genind - genref
                    else:
                        related = 99
                    # In general, a person's income must be less than $2,500 to
                    # be eligible to be a dependent.
                    # But there are exceptions for children.
                    if income <= 2500:
                        test4 = 1
                    if (relcode == 5) or (related == -1):
                        if age <= 18 or (age <= 23 and record['a_enrlw'] > 0):
                            test4 = 1
                    if totincx + income > 0:
                        if income / float(totincx + income) < 0.5:
                            test5 = 1
                    else:
                        test5 = 1
                    dtest = test1 + test2 + test3 + test4 + test5
                    if dtest == 5:
                        dflag = True
                if dflag:
                    individual['d_flag'] = True
                    depne += 1
                    dage = individual['a_age']
                    record[('dep' + str(depne))] = house.index(individual)
                    record['depage' + str(depne)] = dage
                    if individual['a_age'] <= 5:
                        record['nu05'] += 1
                    if individual['a_age'] <= 13:
                        record['nu13'] += 1
                    if individual['a_age'] < 18:
                        record['nu18'] += 1
                        record['nu18_dep'] += 1
                    if 18 <= individual['a_age'] < 21:
                        record['n1821'] += 1
                    if individual['a_age'] >= 21:
                        record['n21'] += 1
                    if individual['a_age'] >= 65:
                        record['elderly_dependent'] += 1

        cahe = np.nan

        record['t_flag'] = True  # tax unit flag
        returns = record['t_flag']

        namelist = ['js', 'ifdept', 'agede', 'cahe', 'ageh', 'ages', 'was',
                    'intst', 'dbe', 'alimony', 'bil', 'pensions', 'rents',
                    'fil', 'ucomp', 'socsec', 'returns', 'wt', 'zifdep',
                    'zntdep', 'zhhinc', 'zagept', 'zagesp', 'zoldes', 'zyoung',
                    'zworkc', 'zsocse', 'zssinc', 'zpubas', 'zvetbe', 'zchsup',
                    'zfinas', 'zdepin', 'zowner', 'zwaspt', 'zwassp', 'wasp',
                    'wass', 'xregion', 'xschb', 'xschf', 'xsche', 'xschc',
                    'xhid', 'xfid', 'xpid', 'depne', 'totincx', 'xstate']

        varlist = [js, ifdept, agede, cahe, ageh, ages, was, intst, dbe,
                   alimony, bil, pensions, rents, fil, ucomp, socsec, returns,
                   wt, zifdep, zntdep, zhhinc, zagept, zagesp, zoldes, zyoung,
                   zworkc, zsocse, zssinc, zpubas, zvetbe, zchsup, zfinas,
                   zdepin, zowner, zwaspt, zwassp, wasp, wass, xregion, xschb,
                   xschf, xsche, xschc, xhid, xfid, xpid, depne, totincx,
                   xstate]

        for name, var in zip(namelist, varlist):
            record[name] = var
        return record

    def hhstatus(self, unit):
        """
        Determine head of household status

        Parameters
        ----------
        unit: a tax unit
        """

        income = 0
        # Find total income for the tax unit
        for iunit in self.house_units:
            totinc = (iunit['was'] + iunit['intst'] + iunit['dbe'] +
                      iunit['alimony'] + iunit['bil'] + iunit['pensions'] +
                      iunit['rents'] + iunit['fil'] + iunit['ucomp'] +
                      iunit['socsec'])
            income += totinc
        # Find income for the individual
        if income > 0:
            totincx = (unit['was'] + unit['intst'] + unit['dbe'] +
                       unit['alimony'] + unit['bil'] + unit['pensions'] +
                       unit['rents'] + unit['fil'] + unit['ucomp'] +
                       unit['socsec'])
            indjs = unit['js']  # Filind status
            indif = unit['ifdept']  # Dependency status
            inddx = unit['depne']  # Number of dependent exemptions
            if indjs == 1 and float(totincx) / income > 0.99:
                if indif != 1 and inddx > 0:
                    unit['js'] = 3

    def must_file(self, record):
        """
        Determine if a dependent must file
        Parameters
        ----------
        record: record for the dependent
        Returns
        -------
        True if person must file, False otherwise
        """
        wages = record['wsal_val']
        income = (wages + record['semp_val'] + record['frse_val'] +
                  record['uc_val'] + record['ss_val'] + record['rtm_val'] +
                  record['int_val'] + record['div_val'] + record['rnt_val'] +
                  record['alm_val'])
        # Determine if dependent exceeds filing thresholds
        if wages > self.depwages or income > self.depTotal:
            depfile = True
        else:
            depfile = False
        return depfile

    def convert(self, ix, iy):
        """
        Convert existing tax unit (ix) to a dependent filer and add dependent
        information to the target return (iy)

        Parameters
        ----------
        ix, iy: tax units

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
            self.house_units[iy]['dep' + str(iydeps + 1)] = ix
            self.house_units[iy][('dep' +
                                  str(iydeps +
                                      2))] = self.house_units[ix]['sp_ptr']
            self.house_units[iy][('depage' +
                                  str(iydeps +
                                      1))] = self.house_units[ix]['a_age']
            self.house_units[iy][('depage' +
                                  str(iydeps +
                                      2))] = self.house_units[ix]['ages']
            iybgin = iydeps + 2
        else:
            self.house_units[iy]['depne'] += (ixdeps + 1)
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

    def tax_units_search(self):
        """
        Search for dependencies among tax units in a household
        """
        highest = -9.9e32
        idxhigh = 0
        # Find tax unit with highest income
        for ix in range(0, self.nunits):
            totincx = self.house_units[ix]['totincx']
            if totincx > highest:
                highest = totincx
                idxhigh = ix
        # If it is not already a dependent unit, search for dependents
        if not self.house_units[idxhigh]['ifdept']:
            for ix in range(0, self.nunits):
                idxjs = self.house_units[ix]['js']
                idxdepf = self.house_units[ix]['ifdept']
                idxrelc = self.house_units[ix]['a_exprrp']
                idxfamt = self.house_units[ix]['ftype']
                if (ix != idxhigh and not idxdepf and highest > 0 and
                        idxjs != 2):
                    if idxfamt == 1 or idxfamt == 3 or idxfamt == 5:
                        totincx = self.house_units[ix]['totincx']
                        if totincx <= 0:
                            self.house_units[ix]['t_flag'] = False
                            self.convert(ix, idxhigh)
                        if 0 < totincx <= 3000:
                            self.convert(ix, idxhigh)
                    if idxrelc == 11:
                        self.house_units[ix]['t_flag'] = False
                        self.convert(ix, idxhigh)

    def filst(self, unit):
        """
        Determines whether or not a tax unit files a return using five tests
        1. Wage test. If anyone in the tax unit had wage and salary income,
           the unit is deemed to file a return
        2. Gross income test. The income thresholds in the 1040 filing
           requirements are used to determine if the tax unit has to file.
        3. Dependent filer test. Individuals who are claimed as dependents, but
           are required to file a return
        4. Random selection
        5. Negative income

        Parameters
        ----------
        unit: a tax unit
        """
        # Wage test
        unit['filst'] = 0
        if unit['js'] == 1:
            if unit['was'] >= self.wage1:
                unit['filst'] = 1
        elif unit['js'] == 2:
            if unit['depne'] > 0:
                if unit['was'] >= self.wage2:
                    unit['filst'] = 1
            else:
                if unit['was'] >= self.wage2nk:
                    unit['filst'] = 1
        elif unit['js'] == 3:
            if unit['was'] >= self.wage3:
                unit['filst'] = 1

        # Gross income test
        income = (unit['was'] + unit['intst'] + unit['dbe'] + unit['alimony'] +
                  unit['bil'] + unit['pensions'] + unit['rents'] +
                  unit['fil'] + unit['ucomp'])
        if unit['js'] == 1:
            amount = self.single - self.depExempt * unit['depne']
            if unit['agede'] != 0:
                amount = self.single65 - self.depExempt * unit['depne']
            if income >= amount:
                unit['filst'] = 1
        if unit['js'] == 2:
            amount = self.joint - self.depExempt * unit['depne']
            if unit['agede'] == 1:
                amount = self.joint65one - self.depExempt * unit['depne']
                amount = self.joint65both - self.depExempt * unit['depne']
            if income >= amount:
                unit['filst'] = 1
        if unit['js'] == 3:
            amount = self.hoh
            if unit['agede'] != 0:
                amount = self.hoh65 - self.depExempt * unit['depne']
            if income >= amount:
                unit['filst'] = 1

        # Dependent filer test
        if unit['ifdept']:
            unit['filst'] = 1
        # Random selection
        if (unit['js'] == 3 and unit['agede'] > 0 and
                income < 6500 and unit['depne'] > 0):
            unit['filst'] = 0
        # Negative incomet test
        if unit['bil'] < 0 or unit['fil'] < 0 or unit['rents'] < 0:
            unit['filst'] = 1

    def output(self, unit, house):
        """
        After the tax units have been created, output all records
        Parameters
        ----------
        unit: head tax unit
        house: household of tax unit

        Returns
        -------
        Completed tax unit
        """

        record = {}
        depne = unit['depne']
        if unit['js'] == 2:
            txpye = 2
        else:
            txpye = 2
        xxtot = txpye + depne
        # Check relationship codes among dependents
        xxoodep = 0
        xxopar = 0
        xxocah = 0
        xxocawh = 0
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

        record['xagex'] = unit['agede']
        record['hhid'] = unit['h_seq']

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
                unit['zoldes'] = oldest
                unit['zyoung'] = youngest
        record['oldest'] = oldest
        record['youngest'] = youngest
        record['xxocah'] = xxocah
        # This looks like a typo
        # record['xxpcawh'] = xxocawh
        record['xxocawh'] = xxocawh
        record['xxoodep'] = xxoodep
        record['xxopar'] = xxopar
        record['xxtot'] = xxtot

        repeated_vars = ['xstate', 'xregion', 'xschb', 'xschf',
                         'xsche', 'xschc', 'xhid', 'xfid', 'xpid', 'h_seq',
                         'peridnum', 'js', 'ifdept', 'agede', 'depne', 'cahe',
                         'ageh', 'ages', 'was', 'intst', 'dbe', 'alimony',
                         'bil', 'pensions', 'rents', 'fil', 'ucomp', 'socsec',
                         'returns', 'wt', 'zifdep', 'zntdep', 'zhhinc',
                         'zagesp', 'zoldes', 'zyoung', 'zworkc', 'zsocse',
                         'zssinc', 'zpubas', 'zvetbe', 'zfinas', 'zowner',
                         'zwaspt', 'zwassp', 'wasp', 'wass', 'nu05', 'nu13',
                         'nu18_dep', 'nu18', 'n1821', 'n21',
                         'elderly_dependent']
        for var in repeated_vars:
            record[var] = unit[var]

        icps1 = unit['101']
        icps2 = unit['102']
        icps3 = np.nan
        icps4 = np.nan
        icps5 = np.nan
        icps6 = np.nan
        icps7 = np.nan
        icps8 = youngest
        icps9 = oldest
        icps10 = unit['110']
        icps11 = unit['111']
        icps12 = unit['112']
        icps13 = unit['113']
        icps14 = unit['114']
        icps15 = unit['115']
        icps16 = unit['116']
        icps17 = unit['117']
        icps18 = unit['118']
        icps19 = unit['119']
        icps20 = unit['120']
        icps21 = unit['121']
        icps22 = unit['122']
        icps23 = unit['123']
        icps24 = unit['124']
        icps25 = unit['125']
        icps26 = unit['126']
        icps27 = unit['127']
        icps28 = unit['128']
        icps29 = unit['129']
        icps30 = unit['130']
        icps31 = unit['131']
        icps32 = unit['132']
        icps33 = unit['133']
        icps34 = unit['134']
        icps35 = unit['135']
        icps36 = unit['136']
        icps37 = unit['137']
        icps38 = unit['138']
        icps39 = unit['139']
        icps40 = unit['140']
        icps41 = unit['141']
        icps42 = unit['142']
        icps43 = unit['143']
        icps44 = unit['144']
        icps45 = unit['145']
        icps46 = unit['146']
        icps47 = unit['147']
        icps48 = unit['148']

        jcps1 = unit['151']
        jcps2 = unit['152']
        jcps3 = unit['153']
        jcps4 = unit['154']
        jcps5 = unit['155']
        jcps6 = unit['156']
        jcps7 = unit['157']
        jcps8 = unit['158']
        jcps9 = unit['159']
        jcps10 = unit['160']
        jcps11 = unit['161']
        jcps12 = unit['162']
        jcps13 = unit['163']
        jcps14 = unit['164']
        jcps15 = unit['165']
        jcps16 = unit['166']
        jcps17 = unit['167']
        jcps18 = unit['168']
        jcps19 = unit['169']
        jcps20 = unit['170']
        jcps21 = unit['171']
        jcps22 = unit['172']
        jcps23 = unit['173']
        jcps24 = unit['174']
        jcps25 = unit['175']
        jcps26 = unit['176']
        jcps27 = unit['177']
        jcps28 = unit['178']
        jcps29 = unit['179']
        jcps30 = unit['180']
        jcps31 = unit['181']
        jcps32 = unit['182']
        jcps33 = unit['183']
        jcps34 = unit['184']
        jcps35 = unit['185']
        jcps36 = unit['186']
        jcps37 = unit['187']
        jcps38 = unit['188']
        jcps39 = unit['189']
        jcps40 = unit['190']
        jcps41 = unit['191']
        jcps42 = unit['192']
        jcps43 = unit['193']
        jcps44 = unit['194']
        jcps45 = unit['195']
        jcps46 = unit['196']
        jcps47 = unit['197']
        jcps48 = unit['198']
        jcps49 = unit['199']
        jcps50 = unit['200']
        jcps51 = unit['201']
        jcps52 = unit['202']
        jcps53 = unit['203']
        jcps54 = unit['204']
        jcps55 = unit['205']
        jcps56 = unit['206']
        jcps57 = unit['207']
        jcps58 = unit['208']
        jcps59 = unit['209']
        jcps60 = unit['210']
        jcps61 = unit['211']
        jcps62 = unit['212']
        jcps63 = unit['213']
        jcps64 = unit['214']
        jcps65 = unit['215']
        jcps66 = unit['216']
        jcps67 = unit['217']
        jcps68 = unit['218']
        jcps69 = unit['219']
        jcps70 = unit['220']
        jcps71 = unit['221']
        jcps72 = unit['222']
        jcps73 = unit['223']
        jcps74 = unit['224']
        jcps75 = unit['225']
        jcps76 = unit['226']
        jcps77 = np.nan
        jcps78 = np.nan
        jcps79 = np.nan
        jcps80 = np.nan
        jcps81 = np.nan
        jcps82 = np.nan
        jcps83 = np.nan
        jcps84 = np.nan

        if not unit['ifdept']:
            jcps77 = unit['228']
            jcps78 = unit['229']
            jcps79 = unit['230']
            jcps80 = unit['231']
            jcps81 = unit['232']
            jcps82 = unit['233']
            jcps83 = unit['234']
            jcps84 = unit['235']

        jcps85 = unit['236']
        jcps86 = unit['237']
        jcps87 = unit['238']
        jcps88 = unit['239']
        jcps89 = unit['240']
        jcps90 = unit['241']
        jcps91 = unit['242']
        jcps92 = unit['243']
        jcps93 = unit['244']
        jcps94 = unit['245']
        jcps95 = unit['246']
        jcps96 = unit['247']
        jcps97 = unit['248']
        jcps98 = unit['249']
        jcps99 = unit['250']
        jcps100 = unit['251']
        jcps101 = unit['252']
        jcps102 = unit['253']
        jcps103 = unit['254']
        jcps104 = unit['255']
        jcps105 = unit['256']
        jcps106 = unit['257']
        jcps107 = unit['258']
        jcps108 = unit['259']
        jcps109 = unit['260']
        jcps110 = unit['261']
        jcps111 = unit['262']
        jcps112 = unit['263']
        jcps113 = unit['264']
        jcps114 = unit['265']
        jcps115 = unit['266']
        jcps116 = unit['267']
        jcps117 = unit['268']
        jcps118 = unit['269']
        jcps119 = unit['270']
        jcps120 = unit['271']
        jcps121 = unit['272']
        jcps122 = unit['273']
        jcps123 = unit['274']
        jcps124 = unit['275']

        for i in range(1, 49):
            var = 'icps' + str(i)
            record[str(var)] = eval(var)
        for i in range(1, 125):
            var = 'jcps' + str(i)
            record[str(var)] = eval(var)

        d5 = min(depne, 5)
        if d5 > 0:
            for i in range(1, d5 + 1):
                var = 'icps' + str(2+i)
                record[str(var)] = unit['depage' + str(i)]

        zdepin = 0
        if depne > 0:
            for i in range(1, depne + 1):
                dindex = unit['dep' + str(i)]
                if not house[dindex]['flag']:
                    zdepin += (house[dindex]['wsal_val'] +
                               house[dindex]['semp_val'] +
                               house[dindex]['frse_val'] +
                               house[dindex]['uc_val'] +
                               house[dindex]['ss_val'] +
                               house[dindex]['rtm_val'] +
                               house[dindex]['int_val'] +
                               house[dindex]['div_val'] +
                               house[dindex]['alm_val'])
        record['zdepin'] = zdepin
        record['income'] = (unit['was'] + unit['intst'] + unit['dbe'] +
                            unit['alimony'] + unit['bil'] + unit['pensions'] +
                            unit['rents'] + unit['fil'] + unit['ucomp'] +
                            unit['socsec'])
        # Find filing status of record
        self.filst(record)

        return record
