"""
This script automates the extraction of chained CPI-U values from
the most recent CBO inflation projection.

The CBO (chained-CPI) inflation projection is in the CBO tax
parameter projection spreadsheet, which is a supplement to the CBO
report entitled "The Budget and Economic Outlook."  The most recent
supplement is entitled:
CBO Tax Parameters and Effective Marginal Tax Rates | Feb 2024
and is available at this URL:
https://www.cbo.gov/system/files/2024-02/53724-2024-02-Tax-Parameters.xlsx

NOTE: whenever a new spreadsheet becomes available, it should be visually
inspected to see how the CBO_* structure data (see below) need to be updated.

USAGE: % python cbo_chained_cpiu.py --help

EXPECTED OUTPUT:
% python cbo_chained_cpiu.py CBO-2024-02-Tax-Parameters.xlsx
2021  144.814090
2022  149.063510
2023  159.840000
2024  168.474670
2025  172.770430
2026  176.567340
2027  180.230100
2028  183.738130
2029  187.305920
2030  190.989090
2031  194.765530
2032  198.642940
2033  202.612840
2034  206.669280
"""

import os
import sys
import argparse
import pandas
import taxcalc

# Data on the expected CBO spreadsheet structure:
CBO_SHEET = 1  # the sheet called "1. Tax Parameters"
CBO_STR_COLS = [0, 1, 2, 3]  # expect columns A:D are strings; others numeric
CBO_YEAR = {
    "first": {"year": 2021, "col": "E"},
    "last": {"year": 2034, "col": "R"},
}
# keys in CBO_ROWS are arbitrary names for parameter in the CBO spreadsheet
CBO_ROWS = {
    "year": {"row": 8, "label": "Tax Year"},
    # price index ...
    "c_cpiu": {"row": 158, "label": "Chained consumer price index"},
}


def rindex(row_number):
    """
    Convert spreadsheet row number (1-based) to DataFrame row index (0-based).
    """
    return row_number - 1


def cindex(capital_letter):
    """
    Convert spreadsheet column letter to DataFrame column index (0-based).
    """
    return ord(capital_letter) - ord("A")


def cbo_value(cbodf, name, year):
    """
    Return value in specified year of CBO parameter with specified name;
    return None if there are any problems.
    """
    # check argument values
    args_ok = True
    if name not in CBO_ROWS:
        msg = f"name {name} not in CBO_ROWS data structure"
        sys.stderr.write(f"CBO: {msg}\n")
        args_ok = False
    first_year = CBO_YEAR["first"]["year"]
    if year < first_year:
        msg = f"year {year} less than first year {first_year}"
        sys.stderr.write(f"CBO: {msg}\n")
        args_ok = False
    last_year = CBO_YEAR["last"]["year"]
    if year > last_year:
        msg = f"year {year} greater than last year {last_year}"
        sys.stderr.write(f"CBO: {msg}\n")
        args_ok = False
    if not args_ok:
        return None
    # translate name to row number
    row = CBO_ROWS[name]["row"]
    # convert year to column letter
    ord_first_year = ord(CBO_YEAR["first"]["col"])
    letter = chr(ord_first_year + year - first_year)
    # get cbo_value from cbodf
    val = cbodf.iat[rindex(row), cindex(letter)]
    if "pct" in CBO_ROWS[name]:
        return round(0.01 * val, 6)
    return val


def check_cbo_year():
    """
    Check CBO_YEAR for consistency: return 0 if OK, else return 1.
    """
    ydiff = CBO_YEAR["last"]["year"] - CBO_YEAR["first"]["year"]
    cdiff = cindex(CBO_YEAR["last"]["col"]) - cindex(CBO_YEAR["first"]["col"])
    if ydiff != cdiff:
        msg = "CBO_YEAR contents are inconsistent"
        sys.stderr.write(f"STRUCT: {msg}\n")
        return 1
    return 0


def read_cbo_label(cbolabel, row):
    """
    Return string label from cbodf row.
    """
    ridx = rindex(row)
    for col in CBO_STR_COLS:
        label = cbolabel[col][ridx]
        if label != "nan":
            return label
    return None


def read_check_spreadsheet(fname):
    """
    Read spreadsheet in specified fname and check its contents against
    the expected structure specified in the CBO_* data structures above.
    Function returns a pd.DataFrame except when any check errors are found,
    in which case it return None.
    """
    # check CBO_YEAR consistency
    rcode = check_cbo_year()
    if rcode != 0:
        return None
    # check taxcalc.Policy YEAR constants against CBO_YEAR info
    ok_years = True
    lky = taxcalc.Policy.LAST_KNOWN_YEAR
    valid_lky = range(CBO_YEAR["first"]["year"] + 1, CBO_YEAR["last"]["year"])
    if lky not in valid_lky:
        msg = f"Policy.LAST_KNOWN_YEAR={lky} inconsistent with CBO_YEAR info"
        sys.stderr.write(f"STRUCT: {msg}\n")
        ok_years = False
    lby = taxcalc.Policy.LAST_BUDGET_YEAR
    valid_lby = range(
        CBO_YEAR["first"]["year"] + 2, CBO_YEAR["last"]["year"] + 1
    )
    if lby not in valid_lby:
        msg = f"Policy.LAST_BUDGET_YEAR={lby} inconsistent with CBO_YEAR info"
        sys.stderr.write(f"STRUCT: {msg}\n")
        ok_years = False
    if not ok_years:
        return None
    # read spreadsheet
    try:
        cbodf = pandas.read_excel(fname, CBO_SHEET, header=None, dtype=object)
    except:  # pylint: disable=bare-except
        msg = f"could not read sheet in {fname} into a DataFrame"
        sys.stderr.write(f"READ: {msg}\n")
        return None
    # extract string columns into cbolabel dictionary containing row lists
    cbolabel = {}
    for col in CBO_STR_COLS:
        cbolabel[col] = [str(obj) for obj in cbodf[col].tolist()]
    # check spreadsheet against CBO_ROWS
    for cname, cdict in CBO_ROWS.items():
        elabel = cdict["label"]
        alabel = read_cbo_label(cbolabel, cdict["row"])
        if not alabel.startswith(elabel):
            msg = f"for {cname} expected label is {elabel} but found {alabel}"
            sys.stderr.write(f"READ: {msg}\n")
            return None
    return cbodf


def check_arguments(args):
    """
    Check validity of command-line arguments returning one if there
    are problems or zero if there are no problems.
    """
    rcode = 0
    fname = args.CBOFILENAME
    if len(fname) <= 0:
        msg = "must specify CBOFILENAME command-line argument"
        sys.stderr.write(f"ERROR: {msg}\n")
        return 1
    if not fname.endswith(".xlsx"):
        msg = f"CBOFILENAME {fname} does not end with .xlsx"
        sys.stderr.write(f"ERROR: {msg}\n")
        rcode = 1
    if not os.path.exists(fname):
        msg = f"CBOFILENAME {fname} does not exist"
        sys.stderr.write(f"ERROR: {msg}\n")
        rcode = 1
    return rcode


def main():
    """
    High-level script logic.
    """
    # parse command-line arguments:
    usage_str = "python cbo_chained_cpiu.py CBOFILENAME [--help]"
    parser = argparse.ArgumentParser(
        prog="",
        usage=usage_str,
        description=(
            "Writes to standard output chained CPI-U values that are "
            " extracted from the downloaded CBOFILENAME spreadsheet. "
            "IMPORTANT NOTE: always inspect a new CBO spreadsheet to "
            "see which CBO_* data structures at the top of this script "
            "need to be updated."
        ),
    )
    parser.add_argument(
        "CBOFILENAME",
        nargs="?",
        help=("file name of CBO .xlsx spreadsheet."),
        default="",
    )
    args = parser.parse_args()
    # check command-line arguments
    rcode = check_arguments(args)
    if rcode != 0:
        sys.stderr.write(f"USAGE: {usage_str}\n")
        return rcode
    # read and check structure of CBO tax parameters spreadsheet
    cbodf = read_check_spreadsheet(args.CBOFILENAME)
    if not isinstance(cbodf, pandas.DataFrame):
        sys.stderr.write("ERROR: CBO spreadsheet has unexpected structure\n")
        return 1
    # write chained CPI-U values for each year in CBO spreadsheet
    for year in range(CBO_YEAR["first"]["year"], CBO_YEAR["last"]["year"] + 1):
        val = cbo_value(cbodf, "c_cpiu", year)
        print(f"{year}  {val:.6f}")
    return 0


# end main function code


if __name__ == "__main__":
    sys.exit(main())
