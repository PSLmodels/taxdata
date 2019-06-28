INCOME_TUPLES = [
    ("wsal_val", "e00200"), ("int_val", "interest"),
    ("semp_val", "e00900"), ("frse_val", "e02100"),
    ("div_val", "e00600"), ("uc_val", "e02300"),
    ("rtm_val", "e01500"), ("alimony", "e00800")
]
BENEFIT_TUPLES = [
    ("MedicaidX", "mcaid_ben"), ("housing_impute", "housing_ben"),
    ("MedicareX", "mcare_ben"), ("snap_impute", "snap_ben"),
    ("ssi_impute", "ssi_ben"), ("tanf_impute", "tanf_ben"),
    ("UI_impute", "e02300"), ("vb_impute", "vet_ben"),
    ("wic_impute", "wic_ben"), ("ss_impute", "e02400")
]


class TaxUnit:
    def __init__(self, data: dict, year: int, dep_status: bool = False):
        """
        Parameters
        ----------
        data: dictionary of data from the CPS
        dep_status: indicator for whether or not this is a
                    dependent filer
        """
        # add attributes of the tax unit
        self.tot_inc = 0
        for cps_var, tc_var in INCOME_TUPLES:
            setattr(self, tc_var, data[cps_var])
            setattr(self, f"{tc_var}p", data[cps_var])
            setattr(self, f"{tc_var}s", 0.)
            self.tot_inc += data[cps_var]
        # add benefit data
        for cps_var, tc_var in BENEFIT_TUPLES:
            setattr(self, tc_var, data[cps_var])
        self.agi = data["agi"]

        self.age_head = data["a_age"]
        self.age_spouse = 0
        self.blind_head = data["pediseye"]
        self.fips = data["gestfips"]
        self.h_seq = data["hhid"]
        self.a_lineno = data["a_lineno"]
        self.ffpos = data["ffpos"]
        self.s006 = data["marsupwt"]
        self.FLPDYR = year
        self.XTOT = 1
        self.EIC = 0
        self.dep_stat = 0
        if dep_status:
            self.XTOT = 0
            self.dep_stat = 1
        self.mars = 1  # start with being single

        # age data
        self.nu18 = 0
        self.n1820 = 0
        self.n21 = 0
        self.nu06 = 0
        self.nu13 = 0
        self.n24 = 0
        self.elderly_dependents = 0
        self.check_age(data["a_age"])

        # list to hold line numbers of dependents and spouses
        self.deps_spouses = []

    def add_spouse(self, spouse: dict):
        """
        Add a spouse to the unit
        """
        for cps_var, tc_var in INCOME_TUPLES:
            self.tot_inc += spouse[cps_var]
            setattr(self, tc_var, getattr(self, tc_var) + spouse[cps_var])
            setattr(self, f"{tc_var}s", spouse[cps_var])
        for cps_var, tc_var in BENEFIT_TUPLES:
            setattr(
                self, tc_var, getattr(self, tc_var) + spouse[cps_var]
            )
        self.agi += spouse["agi"]
        self.XTOT += 1
        setattr(self, "blind_spouse", spouse["pediseye"])
        self.deps_spouses.append(spouse["a_lineno"])
        setattr(self, "age_spouse", spouse["a_age"])
        spouse["s_flag"] = True
        self.check_age(spouse["a_age"])
        self.mars = 2

    def add_dependent(self, dependent: dict):
        """
        Add dependent to the unit
        """
        for cps_var, tc_var in INCOME_TUPLES:
            # self.tot_inc += dependent[cps_var]
            setattr(self, tc_var, getattr(self, tc_var) + dependent[cps_var])
        for cps_var, tc_var in BENEFIT_TUPLES:
            dep_val = dependent[cps_var]
            setattr(
                self, tc_var, getattr(self, tc_var) + dep_val
            )
        self.check_age(dependent["a_age"], True)
        self.XTOT += 1
        self.EIC += 1
        self.deps_spouses.append(dependent["a_lineno"])
        dependent["d_flag"] = True
        dependent["claimer"] = self.a_lineno

    def remove_dependent(self, dependent: dict):
        """
        Remove dependent from the tax unit
        """
        for cps_var, tc_var in INCOME_TUPLES:
            dep_val = dependent[cps_var]
            setattr(
                self, tc_var, getattr(self, tc_var) - dep_val
            )
        for cps_var, tc_var in BENEFIT_TUPLES:
            dep_val = dependent[cps_var]
            setattr(
                self, tc_var, getattr(self, tc_var) - dep_val
            )
        if dependent["a_age"] < 6:
            self.nu06 -= 1
        if dependent["a_age"] < 13:
            self.nu13 -= 1
        if dependent["a_age"] <= 17:
            self.nu18 -= 1
            self.n24 -= 1
        elif 18 <= dependent["a_age"] <= 20:
            self.n1820 -= 1
        elif dependent["a_age"] >= 21:
            self.n21 -= 1
            if dependent["a_age"] >= 65:
                self.elderly_dependents -= 1

    def check_age(self, age: int, dependent: bool = False):
        """
        Modify the age variables in the tax unit
        """
        if age <= 17:
            self.nu18 += 1
        elif 18 <= age <= 20:
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
            if age >= 65:
                self.elderly_dependents += 1

    def output(self) -> dict:
        """
        Return tax attributes as a dictionary
        """
        # set marital status variable
        if self.mars == 1 & len(self.deps_spouses) > 0:
            # for now assume that if they're single and have any dependents
            # they can file as head of household
            self.mars = 4
        # determine if the unit is a filer here.
        self._must_file()
        # setattr(self, "filer", 1)
        return self.__dict__

    # private methods
    def _must_file(self):
        """
        determine if this unit must file
        """
        if self.mars == 1:
            income_min = 10000
            if self.age_head >= 65:
                income_min = 11500
        elif self.mars == 2:
            income_min = 20000
            if self.age_head >= 65:
                if self.age_spouse >= 65:
                    income_min = 22400
                else:
                    income_min = 21200
            elif self.age_spouse >= 65:
                income_min = 21200
        elif self.mars == 4:
            income_min = 12850
            if self.age_head >= 65:
                income_min = 14350
        if self.tot_inc >= income_min:
            setattr(self, "filer", 1)
        else:
            setattr(self, "filer", 0)
