import cpsmar2013
import cpsmar2014
import cpsmar2015
import subprocess
import pandas as pd
from pathlib import Path
from pycps import main
from finalprep import final_prep


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


def create(export_raw: bool = False):
    """
    Logic for creating tax units from the CPS
    """
    cps_dfs = {}  # dictionary to hold each CPS DataFrame
    for year in CPS_META_DATA.keys():
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
    units = []
    for year in CPS_META_DATA.keys():
        print(f"Creating tax units for {year}")
        units.append(main(cps_dfs[year], year))

    # create single DataFrame
    print("Combining tax units")
    units = pd.concat(units)
    # divide weight by number of CPS files
    num_cps = len(CPS_META_DATA)
    units["s006"] = units["s006"] / num_cps
    # export raw CPS file
    if export_raw:
        print("Exporting raw file")
        units.to_csv(Path(CUR_PATH, "raw_cps.csv"), index=False)
    # final prep
    print("Cleaning file")
    final_cps = final_prep(units)
    print("Exporting final file")
    final_cps.to_csv(Path(CUR_PATH, "cps.csv"))
    subprocess.check_call(["gzip", "-nf", "cps.csv"])


if __name__ == "__main__":
    create()
