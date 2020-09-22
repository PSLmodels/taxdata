import collections
import numpy as np
from pathlib import Path
from helpers import filingparams, cps_yr_idx


CUR_PATH = Path(__file__).resolve().parent
INCOME_TUPLES = [
    ("wsal_val", "e00200"),
    ("int_val", "interest"),
    ("semp_val", "e00900"),
    ("frse_val", "e02100"),
    ("div_val", "divs"),
    ("uc_val", "e02300"),
    ("rtm_val", "e01500"),
]
BENEFIT_TUPLES = [
    ("MedicaidX", "mcaid_ben"),
    ("housing_impute", "housing_ben"),
    ("MedicareX", "mcare_ben"),
    ("snap_impute", "snap_ben"),
    ("ssi_impute", "ssi_ben"),
    ("tanf_impute", "tanf_ben"),
    ("UI_impute", "e02300"),
    ("vb_impute", "vet_ben"),
    ("wic_impute", "wic_ben"),
    ("ss_impute", "e02400"),
]
output_str = "var, year, h_seq, pycps, cps\n"


def compare(data, cps, h_seq, year):
    def record_error(var, h_seq, pycps, cps, year):
        """
        Append an error
        """
        global output_str
        err_str = f"{var},{year},{h_seq},{pycps},{cps}\n"
        output_str += err_str

    num_errors = 0

    # compare age variables. everyone should have
    # been counted somewhere so these totals
    # are expected to be equal
    age_totals = collections.defaultdict(int)
    for person in cps:
        if person["a_age"] >= 21:
            age_totals["n21"] += 1
        elif 18 <= person["a_age"] <= 20:
            age_totals["n1820"] += 1
        elif person["a_age"] < 18:
            age_totals["nu18"] += 1
        if person["a_age"] >= filingparams.elderly_age[cps_yr_idx]:
            age_totals["elderly_dependents"] += 1
    n21_data = data["n21"].sum()
    n21_cps = age_totals["n21"]
    if n21_cps != n21_data:
        record_error("n21", h_seq, n21_data, n21_cps, year)
        num_errors += 1
    n1820_data = int(data["n1820"].sum())
    n1820_cps = age_totals["n1820"]
    if n1820_cps != n1820_data:
        record_error("n1820", h_seq, n1820_data, n1820_cps, year)
        num_errors += 1
    nu18_data = data["nu18"].sum()
    nu18_cps = age_totals["nu18"]
    if nu18_cps != nu18_data:
        record_error("nu18", h_seq, nu18_data, nu18_cps, year)
        num_errors += 1
    elderly_deps_data = data["elderly_dependents"].sum()
    elderly_deps_cps = age_totals["elderly_dependents"]
    # number elderly dependents should never be higher than the number of
    # elderly people in the household
    if elderly_deps_data > elderly_deps_cps:
        record_error(
            "elderly_dependents", h_seq, elderly_deps_data, elderly_deps_cps, year
        )
        num_errors += 1

    for _cps, _tc in INCOME_TUPLES:
        cps_sum = sum([p[_cps] for p in cps])
        tc_sum = data[_tc].sum()
        allclose = np.allclose([cps_sum], [tc_sum], rtol=0.5)
        if not allclose:
            record_error(cps, h_seq, tc_sum, cps_sum, year)

    for _cps, _tc in BENEFIT_TUPLES:
        cps_sum = sum([p[_cps] for p in cps])
        tc_sum = data[_tc].sum()
        if not np.allclose(cps_sum, tc_sum, rtol=0.5):
            record_error(cps, h_seq, tc_sum, cps_sum, year)

    if num_errors > 0:
        return 1
    else:
        return 0
