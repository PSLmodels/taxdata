from helpers import filingparams, cps_yr_idx


INCOME_TUPLES = [
    ("wsal_val", "e00200"), ("int_val", "interest"),
    ("semp_val", "e00900"), ("frse_val", "e02100"),
    ("div_val", "divs"), ("rnt_val", "rents"),
    ("rtm_val", "e01500"), ("alimony", "e00800"), ("ss_impute", "e02400"),
    ("UI_impute", "e02300")
]
BENEFIT_TUPLES = [
    ("MedicaidX", "mcaid_ben"),
    ("MedicareX", "mcare_ben"),
    ("ssi_impute", "ssi_ben"), ("tanf_impute", "tanf_ben"),
    ("UI_impute", "e02300"), ("vb_impute", "vet_ben"),
    ("wic_impute", "wic_ben"), ("ss_impute", "e02400")
]


class TaxUnit:
    def __init__(self, data: dict, year: int, hh_inc: float = 0.0,
                 dep_status: bool = False):
        """
        Parameters
        ----------
        data: dictionary of data from the CPS
        dep_status: indicator for whether or not this is a
                    dependent filer
        """
        # counters for medicaid and medicare
        self.mcare_count = 0
        self.mcaid_count = 0
        # add attributes of the tax unit
        self.tot_inc = 0
        for cps_var, tc_var in INCOME_TUPLES:
            setattr(self, tc_var, data[cps_var])
            setattr(self, f"{tc_var}p", data[cps_var])
            setattr(self, f"{tc_var}s", 0)
            self.tot_inc += data[cps_var]
        # add benefit data
        for cps_var, tc_var in BENEFIT_TUPLES:
            if tc_var == "mcaid_ben" and data[cps_var] != 0:
                self.mcaid_count += 1
            elif tc_var == "mcare_ben" and data[cps_var] != 0:
                self.mcare_count += 1
            setattr(self, tc_var, data[cps_var])
        self.snap_ben = data["snap_impute"]
        self.housing_ben = data["housing_impute"]
        self.agi = data["agi"]

        self.age_head = data["a_age"]
        self.age_spouse = 0
        self.blind_head = data["pediseye"]
        self.fips = data["gestfips"]
        self.h_seq = data["hhid"]
        self.a_lineno = data["a_lineno"]
        self.ffpos = data["ffpos"]
        self.s006 = data["fsup_wgt"]
        self.FLPDYR = year
        self.EIC = 0
        self.dep_stat = 0
        if dep_status:
            self.XTOT = 0
            self.dep_stat = 1
        self.mars = 1  # start with being single
        # update marital status based on CPS indication
        # note that to match the IRS PUF we include widowed people in this
        if data["a_maritl"] in [1, 2, 3, 4]:
            self.mars = 2
        self.XTOT = self.mars
        if data['filestat'] == 4:
            self.mars = 4
        self.hh_inc = hh_inc
        self.filer = 0
        if data['filestat'] != 6:
            self.filer = 1

        # age data
        self.nu18 = 0
        self.n1820 = 0
        self.n21 = 0
        self.nu06 = 0
        self.nu13 = 0
        self.n24 = 0
        self.elderly_dependents = 0
        self.f2441 = 0
        self.check_age(data["a_age"])

        # home related data
        self.home_owner = 0
        if not dep_status and data["h_tenure"] == 1:
            self.home_owner = 1
        # property taxes
        self.prop_tax = data["prop_tax"]
        # state and local taxes
        self.statetax = max(0., data["statetax_ac"])
        # property value
        self.prop_value = data["hprop_val"]
        # presence of a mortgage
        self.mortgage_yn = 0
        if data["hpres_mort"] == 1:
            self.mortgage_yn = 1

        # list to hold line numbers of dependents and spouses
        self.deps_spouses = []
        self.depne = 0  # number of dependents

    def add_spouse(self, spouse: dict):
        """
        Add a spouse to the unit
        """
        for cps_var, tc_var in INCOME_TUPLES:
            self.tot_inc += spouse[cps_var]
            setattr(self, tc_var, getattr(self, tc_var) + spouse[cps_var])
            setattr(self, f"{tc_var}s", spouse[cps_var])
        for cps_var, tc_var in BENEFIT_TUPLES:
            if tc_var == "mcaid_ben" and spouse[cps_var] != 0:
                self.mcaid_count += 1
            elif tc_var == "mcare_ben" and spouse[cps_var] != 0:
                self.mcare_count += 1
            setattr(
                self, tc_var, getattr(self, tc_var) + spouse[cps_var]
            )
        self.agi += spouse["agi"]
        setattr(self, "blind_spouse", spouse["pediseye"])
        self.deps_spouses.append(spouse["a_lineno"])
        setattr(self, "age_spouse", spouse["a_age"])
        spouse["s_flag"] = True
        self.check_age(spouse["a_age"])
        self.statetax += spouse["statetax_ac"]

    def add_dependent(self, dependent: dict, eic: int):
        """
        Add dependent to the unit
        """
        for cps_var, tc_var in BENEFIT_TUPLES:
            dep_val = dependent[cps_var]
            if tc_var == "mcaid_ben" and dep_val != 0:
                self.mcaid_count += 1
            elif tc_var == "mcare_ben" and dep_val != 0:
                self.mcare_count += 1
            setattr(
                self, tc_var, getattr(self, tc_var) + dep_val
            )
        self.check_age(dependent["a_age"], True)
        self.XTOT += 1
        self.EIC += eic
        self.deps_spouses.append(dependent["a_lineno"])
        dependent["d_flag"] = True
        dependent["claimer"] = self.a_lineno
        self.depne += 1

    def remove_dependent(self, dependent: dict):
        """
        Remove dependent from the tax unit
        """
        for cps_var, tc_var in BENEFIT_TUPLES:
            dep_val = dependent[cps_var]
            if tc_var == "mcaid_ben" and dep_val != 0:
                self.mcaid_count -= 1
            elif tc_var == "mcare_ben" and dep_val != 0:
                self.mcare_count -= 1
            setattr(
                self, tc_var, getattr(self, tc_var) - dep_val
            )
        if dependent["a_age"] < 6:
            self.nu06 -= 1
        if dependent["a_age"] < 13:
            self.nu13 -= 1
        if dependent["a_age"] < 17:
            self.n24 -= 1
        if dependent["a_age"] < 18:
            self.nu18 -= 1
        elif 18 <= dependent["a_age"] < 21:
            self.n1820 -= 1
        elif dependent["a_age"] >= 21:
            self.n21 -= 1
            if dependent["a_age"] >= filingparams.elderly_age[cps_yr_idx]:
                self.elderly_dependents -= 1
        self.depne -= 1
        self.XTOT -= 1

    def check_age(self, age: int, dependent: bool = False):
        """
        Modify the age variables in the tax unit
        """
        if age < 18:
            self.nu18 += 1
        elif 18 <= age < 21:
            self.n1820 += 1
        elif age >= 21:
            self.n21 += 1

        if dependent:
            if age < 17:
                self.n24 += 1
            if age < 6:
                self.nu06 += 1
            if age < 13:
                self.nu13 += 1
                self.f2441 += 1
            if age >= filingparams.elderly_age[cps_yr_idx]:
                self.elderly_dependents += 1

    def output(self) -> dict:
        """
        Return tax attributes as a dictionary
        """
        # enforce that all spouse income variables are zero for non-married
        if self.mars != 2:
            for _, tc_var in INCOME_TUPLES:
                value = getattr(self, f"{tc_var}s")
                msg = f"{tc_var}s is not zero for household {self.h_seq}"
                assert value == 0, msg
        # add family size variable
        fam_size = 1 + self.depne
        if self.mars == 2:
            fam_size += 1
        setattr(self, 'fam_size', fam_size)
        m = f'{self.XTOT} != {sum([self.nu18, self.n1820, self.n21])}'
        assert self.XTOT >= sum([self.nu18, self.n1820, self.n21]), m
        return self.__dict__

    # private methods
    def _must_file(self):
        """
        determine if this unit must file
        """
        aidx = 0  # age index for filing parameters
        midx = 0  # marital index for filing parameters
        if self.mars == 1:
            if self.age_head >= filingparams.elderly_age[cps_yr_idx]:
                aidx = 1
        elif self.mars == 2:
            midx = 1
            if self.age_head >= filingparams.elderly_age[cps_yr_idx]:
                aidx = 1
                if self.age_spouse >= filingparams.elderly_age[cps_yr_idx]:
                    aidx = 2
            elif self.age_spouse >= filingparams.elderly_age[cps_yr_idx]:
                aidx = 1
        elif self.mars == 4:
            midx = 2
            if self.age_head >= filingparams.elderly_age[cps_yr_idx]:
                aidx = 1
        else:
            msg = (f"Filing status not in [1, 2, 4]. HHID: {self.h_seq} "
                   f"a_lineno: {self.a_lineno}")
            raise ValueError(msg)
        income_min = filingparams.gross_inc_thd[cps_yr_idx][midx][aidx]
        if self.tot_inc >= income_min:
            setattr(self, "filer", 1)
        else:
            setattr(self, "filer", 0)
