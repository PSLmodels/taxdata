import subprocess
import pandas as pd
import pickle
import validation
from pathlib import Path
from tqdm import tqdm
from pycps import pycps
from splitincome import split_income
from targeting import target
from finalprep import final_prep
from impute import imputation
from benefits import distribute_benefits
from cps_meta import CPS_META_DATA


CUR_PATH = Path(__file__).resolve().parent
DATA_PATH = Path(CUR_PATH, "data")
# list of which CPS file to actually use
CPS_FILES = [2013, 2014, 2015]


def create(exportcsv: bool = False, exportpkl: bool = False,
           exportraw: bool = True, validate: bool = False,
           benefits: bool = True, verbose: bool = False,
           cps_files=CPS_FILES):
    """
    Logic for creating tax units from the CPS
    Parameters
    ----------
    exportcsv: if True, the raw CPS file will be exported as a CSV
    exportpkl: if True, the list version of the CPS used to create the tax
               units will be saved as a pickle file
    exportraw: if True, the CPS file that has not been modified will be
               saved as a CSV
    validate: if True, validation tests will be run on the tax units to ensure
              all household income, benefits, and people are accounted for
    benefits: if True, benefits imputed by C-TAM will be included in the tax
              units
    verbose: if True, additional progress information will be printed as the
             scripts run
    cps_files: list containing which years of the CPS you want to use
    """
    # add progress_apply to pandas if user wants to validate
    if validate:
        tqdm.pandas()
    # look for pickled versions of the converted CPS files
    cps_dfs = {}
    for year in cps_files:
        try:
            meta = CPS_META_DATA[year]
        except KeyError:
            msg = f"Using the {year} CPS is not yet supported."
            raise KeyError(msg)
        # potential path to pickled CPS file
        pkl_path = Path(DATA_PATH, f"cpsmar{year}.pkl")
        # check and see if pickled version of this year's CPS has been created
        if pkl_path.exists():
            print("Reading Pickled File")
            cps_dfs[year] = pickle.load(pkl_path.open("rb"))
        else:
            # convert the DAT file
            cps_dfs[year] = meta["create_func"](
                Path(DATA_PATH, meta["dat_file"]), year=year,
                benefits=benefits, exportpkl=exportpkl, exportcsv=exportcsv
            )

    # create tax units
    _units = []
    for year in cps_files:
        print(f"Creating Tax Units for {year}")
        _yr_units = pycps(cps_dfs[year], year, verbose)
        if validate:
            validate_cps_units(cps_dfs[year], _yr_units, year)
        _units.append(_yr_units)

    # create a single DataFrame
    print("Combining tax units")
    units = pd.concat(_units, sort=False)
    # divinde weight by number of CPS files
    num_cps = len(cps_files)
    units["s006"] = units["s006"] / num_cps

    # export raw CPS file
    if exportraw:
        print("Exporting raw file")
        units.to_csv(Path(DATA_PATH, "raw_cps.csv"), index=False)
    # split up income
    print("Splitting up income")
    data = split_income(units)

    # imputations
    print("Imputing Variables")
    logit_betas = pd.read_csv(Path(DATA_PATH, "logit_betas.csv"), index_col=0)
    ols_betas = pd.read_csv(Path(DATA_PATH, "ols_betas.csv"), index_col=0)
    data = imputation(data, logit_betas, ols_betas)
    # target state totals
    print("Targeting State Level Data")
    STATE_DATA_LINK = "https://www.irs.gov/pub/irs-soi/14in54cmcsv.csv"
    data = target(data, STATE_DATA_LINK)
    # add other benefit data
    print("Adding Benefits")
    other_ben = pd.read_csv(Path(DATA_PATH, "otherbenefitprograms.csv"),
                            index_col="Program")
    data = distribute_benefits(data, other_ben)
    print("Exporting Raw File")
    data.to_csv(Path(CUR_PATH, "cps_raw.csv"), index=False)
    subprocess.check_call(["gzip", "-nf", "cps_raw.csv"])
    # final prep
    print("Cleaning file")
    final_cps = final_prep(data)
    print("Exporting final file")
    final_cps.to_csv(Path(CUR_PATH, "cps.csv"), index=False)
    subprocess.check_call(["gzip", "-nf", "cps.csv"])


def validate_cps_units(raw_cps, units, year):
    """
    Function to handle all of the validation logic
    """
    print(f"Validating for {year}")
    gdf = units.groupby("h_seq")
    # errors = gdf.progress_apply(validation.compare, cps=raw_cps, year=year)
    num_errors = 0
    # Loop through each household
    for hh in tqdm(raw_cps):
        h_seq = hh[0]["h_seq"]
        hh_units = gdf.get_group(h_seq)
        num_errors += validation.compare(hh_units, hh, h_seq, year)
    if num_errors > 0:
        save_path = Path(CUR_PATH, f"errors{year}.csv")
        save_path.write_text(validation.output_str)
        print(f"Number of errors for {year}: {num_errors}")
        print(f"A CSV file with these errors can be found in {save_path}")
        raise RuntimeError(
                        f"Errors found in the tax unit creation for {year}"
                    )
    else:
        print(f"No errors for {year}")


if __name__ == "__main__":
    create(
        exportcsv=False, exportpkl=True, exportraw=False, validate=False,
        benefits=True, verbose=True
    )
