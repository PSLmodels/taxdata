"""
Test CPS and PUF data file contents.
"""
import os
import pytest
import numpy as np


def unique_recid(data, dataname):
    """
    Test that RECID values are unique.
    """
    recid = data["RECID"]
    unique, counts = np.unique(recid, return_counts=True)
    recid_count = dict(zip(unique, counts))
    duplicates = False
    msg = ""
    for rid in sorted(recid_count.keys()):
        if recid_count[rid] > 1:
            duplicates = True
            msg += "\nRECID={} has COUNT={}".format(rid, recid_count[rid])
    if duplicates:
        title = "The following {} RECIDs have COUNTS greater than one:"
        raise ValueError(title.format(dataname) + msg)


def min_max(data, meta, dataname):
    """
    Test that variable variables are within their minimum/maximum range.
    """
    for var in meta.keys():
        availability = meta[var]["availability"]
        min_value = meta[var]["range"]["min"]
        max_value = meta[var]["range"]["max"]
        in_data = True
        if dataname not in availability:
            in_data = False
        if in_data:
            m = "{}-{} contains values less than min value".format(dataname, var)
            assert np.all(data[var] >= min_value), m
            m = "{}-{} contains values greater than max value".format(dataname, var)
            assert np.all(data[var] <= max_value), m


def relationships(data, dataname):
    """
    Test the relationships between variables.

    Note (1): we have weakened the XTOT == sum of nu18, n1820, n21 assertion
    for the PUF because in PUF data the value of XTOT is capped by IRS-SOI.

    Note (2): we have weakened the n24 <= nu18 assertion for the PUF because
    the only way to ensure it held true would be to create extreamly small
    bins during the tax unit matching process, which had the potential to
    reduce the overall match accuracy.
    """
    eq_str = "{}-{} not equal to {}"
    less_than_str = "{}-{} not less than or equal to {}"
    tol = 0.020001

    eq_vars = [
        ("e00200", ["e00200p", "e00200s"]),
        ("e00900", ["e00900p", "e00900s"]),
        ("e02100", ["e02100p", "e02100s"]),
    ]
    for lhs, rhs in eq_vars:
        if not np.allclose(data[lhs], data[rhs].sum(axis=1), atol=tol):
            raise ValueError(eq_str.format(dataname, lhs, rhs))

    nsums = data[["nu18", "n1820", "n21"]].sum(axis=1)
    if dataname == "CPS":
        m = eq_str.format(dataname, "XTOT", "sum of nu18, n1820, n21")
        assert np.all(data["XTOT"] >= nsums), m
    else:
        # see Note (1) in docstring
        m = less_than_str.format(dataname, "XTOT", "sum of nu18, n1820, n21")
        assert np.all(data["XTOT"] <= nsums), m

    m = less_than_str.format(dataname, "n24", "nu18")
    if dataname == "CPS":
        assert np.all(data["n24"] <= data["nu18"]), m
    else:
        # see Note (2) in docstring
        m = "Number of records where n24 > nu18 has changed"
        assert (data["n24"] > data["nu18"]).sum() == 9692, m
        subdata = data[data["n24"] > data["nu18"]]
        m = "n24 > nu18 + 3"
        assert np.all(subdata["n24"] <= subdata["nu18"] + 3), m

    m = less_than_str.format(dataname, "e00650", "e00600")
    assert np.all(data["e00600"] >= data["e00650"]), m

    m = less_than_str.format(dataname, "e01700", "e01500")
    assert np.all(data["e01500"] >= data["e01700"]), m

    m = less_than_str.format(dataname, "pencon_p", "e00200p+pencon_p")
    assert np.all((data["e00200p"] + data["pencon_p"]) >= data["pencon_p"]), m

    m = less_than_str.format(dataname, "pencon_s", "e00200s+pencon_s")
    assert np.all((data["e00200s"] + data["pencon_s"]) >= data["pencon_s"]), m

    # check that all non-married filers have zero spouse income
    nonmarried = data[data["MARS"] != 2]
    zeros = np.zeros_like(len(nonmarried))
    msg = "{} not always zero for non-married filing unit"
    spouse_vars = ["e00200s", "e00900s", "e02100s"]
    for var in spouse_vars:
        if not np.allclose(nonmarried[var], zeros):
            raise ValueError(msg.format(var))


def variable_check(test_path, data, dataname):
    """
    Test aggregate values in the data.
    """
    expected_file_name = "{}_agg_expected.txt".format(dataname)
    efile_path = os.path.join(test_path, expected_file_name)
    with open(efile_path, "r") as efile:
        expected_txt = efile.readlines()
    expected_sum = dict()
    expected_min = dict()
    expected_max = dict()
    for line in expected_txt[1:]:
        txt = line.rstrip()
        split = txt.split()
        assert len(split) == 4
        var = split[0]
        expected_sum[var] = int(split[1])
        expected_min[var] = int(split[2])
        expected_max[var] = int(split[3])

    # loop through each column in the dataset and check sum, min, max
    actual_txt = "{:20}{:>15}{:>15}{:>15}\n".format("VARIABLE", "SUM", "MIN", "MAX")
    var_inform = "{:20}{:15d}{:15d}{:15d}\n"
    diffs = False
    diff_list_str = ""  # string to hold all of the variables with errors
    new_vars = False
    new_var_list_str = ""  # srint to hold all of the unexpected variables
    for var in sorted(data.columns):
        sum = int(data[var].sum())
        min = int(data[var].min())
        max = int(data[var].max())
        actual_txt += var_inform.format(var, sum, min, max)
        try:
            var_diff = (
                sum != expected_sum[var]
                or min != expected_min[var]
                or max != expected_max[var]
            )
            if var_diff:
                diffs = True
                diff_list_str += var + "\n"
        except KeyError:
            # if the variable is not expected, print a new message
            new_vars = True
            new_var_list_str += var + "\n"

    # check for any missing variables
    missing_vars = False
    missing_vars_set = set(expected_sum.keys()) - set(data.columns)
    if missing_vars_set:
        missing_vars = True
        missing_vars_str = "\n".join(v for v in missing_vars_set)

    # if there is an error, write the actual file
    if diffs or new_vars or missing_vars:
        msg = "{}\n".format(dataname.upper)
        actual_file_name = "{}_agg_actual.txt".format(dataname)
        actual_file_path = os.path.join(test_path, actual_file_name)
        with open(actual_file_path, "w") as afile:
            afile.write(actual_txt)
        # modify error message based on which errors are raised
        if diffs:
            diff_msg = "Aggregate results differ for following variables:\n"
            diff_msg += diff_list_str
            msg += diff_msg + "\n"
        if new_vars:
            new_msg = "The following unexpected variables were discoverd:\n"
            new_msg += new_var_list_str
            msg += new_msg + "\n"
        if missing_vars:
            msg += "The following expected variables are missing in the data:"
            msg += "\n" + missing_vars_str + "\n\n"
        msg += "If new results OK, copy {} to {}".format(
            actual_file_name, expected_file_name
        )
        raise ValueError(msg)


def check_cps_benefits(data, expect_ben_stat):
    """
    Test benefit variables in CPS data.

    expect_ben_stat is a dictionary containing the expected minimum, maximum,
    and average value for each of the benefits in the CPS. That information
    can be found in cps_benefits_metadata.json
    """
    BNAMES = ["mcare", "mcaid", "ssi", "snap", "wic", "tanf", "housing", "vet", "other"]
    # # compare actual and expected benefit statistics
    error_msg = ""
    wgt = data["s006"] * 0.01
    for bname in BNAMES:
        col = "{}_ben".format(bname)
        assert col in data.columns
        ben = data[col]
        minben = ben.min()
        maxben = ben.max()
        pos = ben > 0
        minpben = ben[pos].min()
        avgben = (ben[pos] * wgt[pos]).sum() / wgt[pos].sum()
        if not np.allclose([minben], [0], rtol=0, atol=0.1):
            msg = "\nCPS {}_ben minben={} != 0"
            error_msg += msg.format(bname, minben)
        exp_minpben = expect_ben_stat[bname]["min"]
        if not np.allclose([minpben], [exp_minpben], rtol=0, atol=0.1):
            msg = "\nCPS {}_ben minpben={} != {}"
            error_msg += msg.format(bname, minpben, exp_minpben)
        exp_maxben = expect_ben_stat[bname]["max"]
        if not np.allclose([maxben], [exp_maxben], rtol=0, atol=0.1):
            msg = "\nCPS {}_ben maxben={} != {}"
            error_msg += msg.format(bname, maxben, exp_maxben)
        expect_avgben = expect_ben_stat[bname]["avg"]
        if not np.allclose([avgben], [expect_avgben], rtol=0, atol=1.0):
            msg = "\nCPS {}_ben avgben={:.2f} != {:.2f}"
            error_msg += msg.format(bname, avgben, expect_avgben)
        # check that mc??? benefits are actuarial values of health insurance
        if bname == "mcare" or bname == "mcaid":
            ratio = float(maxben) / minpben
            expect_ratio = round(ratio)
            if not np.allclose([ratio], [expect_ratio], rtol=0, atol=0.001):
                msg = "\nCPS {}_ben ratio={:.6f} != {:.0f}"
                error_msg += msg.format(bname, ratio, expect_ratio)
    if error_msg:
        raise ValueError(error_msg)


@pytest.mark.requires_pufcsv
def test_puf_unique_recid(puf, metadata, test_path):
    unique_recid(puf, "PUF")


@pytest.mark.requires_pufcsv
def test_puf_min_max(puf, metadata):
    min_max(puf, metadata, "puf")


@pytest.mark.requires_pufcsv
def test_puf_relationships(puf):
    relationships(puf, "PUF")


@pytest.mark.requires_pufcsv
def test_puf_variables(puf, test_path):
    variable_check(test_path, puf, "puf")


def test_cps_unique_recid(cps):
    unique_recid(cps, "CPS")


def test_cps_min_max(cps, metadata):
    min_max(cps, metadata, "cps")


def test_cps_relationships(cps):
    relationships(cps, "CPS")


def test_cps_variables(cps, test_path):
    variable_check(test_path, cps, "cps")


def test_cps_benefits(cps, cps_benefit_metadata):
    check_cps_benefits(cps, cps_benefit_metadata)
