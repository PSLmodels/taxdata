import pandas as pd
from tqdm import tqdm
from dask import compute, delayed


INCOME_TUPLES = [
    ("wsal_val", "e00200"), ("int_val", "interest"),
    ("semp_val", "e00900"), ("frse_val", "e02100"),
    ("div_val", "e00600"), ("uc_val", "e02300"),
    ("rtm_val", "e01500")
]


def record_error(var, h_seq, pycps, cps, year):
    """
    Append an error
    """
    global output_str
    global errors
    err_str = f"{var},{year},{h_seq},{pycps},{cps}\n"
    output_str += err_str
    errors += 1


def compare(data, year):
    # get subset of CPS
    sub_cps = CPS[CPS["h_seq"] == data.name]
    # compare age variables. everyone should have
    # been counted somewhere so these totals
    # are expected to be equal
    n21_data = data["n21"].sum()
    n21_cps = (sub_cps["a_age"] >= 21).sum()
    if n21_cps != n21_data:
        record_error("n21", data.name, n21_data, n21_cps)
    n1820_data = data["n1820"].sum()
    n1820_cps = ((sub_cps["a_age"] >= 18) & (sub_cps["a_age"] <= 20)).sum()
    if n1820_cps != n1820_data:
        record_error("n1820", data.name, n1820_data, n1820_cps)
    nu18_data = data["nu18"].sum()
    nu18_cps = (sub_cps["a_age"] < 18).sum()
    if nu18_cps != nu18_data:
        record_error("nu18", data.name, nu18_data, nu18_cps)

    # compare income variables
    for cps, tc in INCOME_TUPLES:
        cps_sum = sub_cps[cps].sum()
        if tc == "interest":
            tc_sum = (data["e00300"] + data["e00400"]).sum()
        else:
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
            record_error(cps, data.name, tc_sum, cps_sum)


print("Reading CPS")
years = [2013, 2014, 2015]
delay = [
    delayed(pd.read_csv)(f"data/cpsmar{year}.csv") for year in years
]
CPS13, CPS14, CPS15 = compute(*delay)
output_str = "var, h_seq, pycps, cps\n"
errors = 0
pycps = pd.read_csv("cps.csv.gz")
tqdm.pandas()
for year in years:
    if year == 2013:
        CPS = CPS13
    elif year == 2014:
        CPS = CPS14
    else:
        CPS = CPS15
    sub_py = pycps[pycps["FLPDYR"] == year - 1]
    gdf = sub_py.groupby("h_seq")
    print(f"comparing for {year}")
    gdf.progress_apply(compare, year=year)
print(f"{errors} errors")
print("writing file")
with open("validation.csv", "w") as f:
    f.write(output_str)
