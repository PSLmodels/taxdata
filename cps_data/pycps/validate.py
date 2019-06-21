from pathlib import Path


CUR_PATH = Path(__file__).resolve().parent
INCOME_TUPLES = [
    ("wsal_val", "e00200"), ("int_val", "interest"),
    ("semp_val", "e00900"), ("frse_val", "e02100"),
    ("div_val", "e00600"), ("uc_val", "e02300"),
    ("rtm_val", "e01500")
]
output_str = "var, year, h_seq, pycps, cps\n"


def compare(data, cps, year):
    def record_error(var, h_seq, pycps, cps, year):
        """
        Append an error
        """
        global output_str
        err_str = f"{var},{year},{h_seq},{pycps},{cps}\n"
        output_str += err_str
    num_errors = 0
    # get subset of CPS
    sub_cps = cps[cps["h_seq"] == data.name]
    # compare age variables. everyone should have
    # been counted somewhere so these totals
    # are expected to be equal
    n21_data = data["n21"].sum()
    n21_cps = (sub_cps["a_age"] >= 21).sum()
    if n21_cps != n21_data:
        record_error("n21", data.name, n21_data, n21_cps, year)
        num_errors += 1
    n1820_data = data["n1820"].sum()
    n1820_cps = ((sub_cps["a_age"] >= 18) & (sub_cps["a_age"] <= 20)).sum()
    if n1820_cps != n1820_data:
        record_error("n1820", data.name, n1820_data, n1820_cps, year)
        num_errors += 1
    nu18_data = data["nu18"].sum()
    nu18_cps = (sub_cps["a_age"] < 18).sum()
    if nu18_cps != nu18_data:
        record_error("nu18", data.name, nu18_data, nu18_cps, year)
        num_errors += 1

    # compare income variables
    for cps, tc in INCOME_TUPLES:
        cps_sum = sub_cps[cps].sum()
        # if tc == "interest":
        #     tc_sum = (data["e00300"] + data["e00400"]).sum()
        # else:
        tc_sum = data[tc].sum()
        # it's acceptable for the sum in the CPS to be larger
        # than that in the tax unit file because it's possible
        # dependents have income, but aren't filing so it's not counted
        # we're only raising an error if the difference between the two
        # values is greater than .1 because for some reason
        # interest income would raise an error even though the totals
        # appeared to be the same
        error = cps_sum < tc_sum and abs(cps_sum - tc_sum) > .1
        if error:
            record_error(cps, data.name, tc_sum, cps_sum, year)

    if num_errors > 0:
        return 1
    else:
        return 0


def test():
    global output_str
    output_str += "one\n"
