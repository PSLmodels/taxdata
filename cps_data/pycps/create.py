import cpsmar2013
import cpsmar2014
import cpsmar2015
import subprocess
import pandas as pd
import validate
from pathlib import Path
from pycps import pycps
from splitincome import split_income
from targeting import target
from finalprep import final_prep
from tqdm import tqdm


CUR_PATH = Path(__file__).resolve().parent
DATA_PATH = Path(CUR_PATH, "data")
# metadata on each CPS file
CPS_META_DATA = {
    2013: {
        "dat_file": "asec2013_pubuse.dat",
        "create_func": cpsmar2013.create_cps
    },
    2014: {
        "dat_file": "asec2014_pubuse_tax_fix_5x8_2017.dat",
        "create_func": cpsmar2014.create_cps
    },
    2015: {
        "dat_file": "asec2015_pubuse.dat",
        "create_func": cpsmar2015.create_cps
    }
}
# list of which CPS file to actually use
CPS_FILES = [2013, 2014, 2015]


def create(export_raw: bool = False, skip=False, validate=False):
    """
    Logic for creating tax units from the CPS
    """
    # add progress_apply to pandas if they want to validate
    if validate:
        tqdm.pandas()
    cps_dfs = {}  # dictionary to hold each CPS DataFrame
    for year in CPS_FILES:
        meta = CPS_META_DATA[year]
        csv_path = Path(DATA_PATH, f"cpsmar{year}.csv")
        # check and see if CSV version of this year's CPS has been created
        if not csv_path.exists():
            print(f"Creating CSV version of CPS for {year}")
            # use creation functin for that year to create the DataFrame
            df = meta["create_func"](Path(DATA_PATH, meta["dat_file"]), year)
            cps_dfs[year] = df
        else:
            print(f"Reading CSV for {year}")
            cps_dfs[year] = pd.read_csv(csv_path)

    # convert CPS files to tax units
    if skip:
        units = pd.read_csv("raw_cps.csv", index_col=None)
    else:
        units = []
        for year in CPS_FILES:
            print(f"Creating tax units for {year}")
            _units = pycps(cps_dfs[year], year)
            if validate:
                validation(cps_dfs[year], _units, year)
            units.append(_units)

        # create single DataFrame
        print("Combining tax units")
        units = pd.concat(units)
        # divide weight by number of CPS files
        num_cps = len(CPS_FILES)
        units["s006"] = units["s006"] / num_cps
        # export raw CPS file
        if export_raw:
            print("Exporting raw file")
            units.to_csv(Path(CUR_PATH, "raw_cps.csv"), index=False)
    # split up income
    print("Splitting up income")
    data = split_income(units)
    # target state totals
    print("Targeting State Level Data")
    state_data_link = "https://www.irs.gov/pub/irs-soi/14in54cmcsv.csv"
    data = target(data, state_data_link)
    # final prep
    print("Cleaning file")
    final_cps = final_prep(data)
    print("Exporting final file")
    final_cps.to_csv(Path(CUR_PATH, "cps.csv"), index=False)
    subprocess.check_call(["gzip", "-nf", "cps.csv"])


def validation(raw_cps, units, year):
    """
    Function to handle all of the validation logic
    """
    print(f"Validating for {year}")
    gdf = units.groupby("h_seq")
    errors = gdf.progress_apply(validate.compare, cps=raw_cps, year=year)
    num_errors = errors.sum()
    if num_errors > 0:
        save_path = Path(CUR_PATH, f"errors{year}.csv")
        save_path.write_text(validate.output_str)
        print(f"Number of errors for {year}: {num_errors}")
        print(f"A CSV file with these errors can be found in {save_path}")
        raise RuntimeError(
                        f"Errors found in the tax unit creation for {year}"
                    )
    else:
        print(f"No errors for {year}")


if __name__ == "__main__":
    create(export_raw=True, validate=True)
