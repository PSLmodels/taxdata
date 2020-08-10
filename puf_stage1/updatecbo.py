import os
import requests
import pandas as pd


CUR_PATH = os.path.abspath(os.path.dirname(__file__))


def update_cpim(baseline):
    """
    Update the CPI-M values in the CBO baseline using the BLS API
    """
    print("Updating CPI-M Values")
    url = 'https://api.bls.gov/publicAPI/v1/timeseries/data/CUSR0000SAM'
    # fetch BLS data from about url
    r = requests.get(url)
    # raise and error if the request fails
    assert r.status_code == 200
    result_json = r.json()
    # raise error if request was not successful
    assert result_json['status'] == 'REQUEST_SUCCEEDED'
    # extract the data from the results
    data = result_json['Results']['series'][0]['data']
    df = pd.DataFrame(data)
    # convert the values to floats so that the groupby mean only returns
    # the mean for the value
    df['value'] = df['value'].astype(float)
    cpi_mean = df.groupby('year').mean().transpose().round(1)
    cpi_mean.index = ["CPIM"]

    # open the current baseline to replace the values for the years pulled
    # from BLS
    baseline.update(cpi_mean)

    # find the average difference between CPIM and CPIU for available years
    last_year = max(cpi_mean.columns)
    first_year = min(baseline.columns)
    # retrieve subset of the DataFrame containing actual CPIM values
    split_col = int(last_year) - int(first_year) + 1
    sub_baseline = baseline[baseline.columns[: split_col]]

    # find the difference
    mean_diff = (sub_baseline.loc['CPIM'] - sub_baseline.loc['CPIU']).mean()

    # update the future values to reflect the difference between
    new_vals = {}
    for col in baseline.columns[split_col:]:
        cpiu = baseline[col].loc['CPIU']
        new_val = cpiu + mean_diff
        new_vals[col] = [new_val]
    future_df = pd.DataFrame(new_vals, index=["CPIM"]).round(1)
    baseline.update(future_df)

    return baseline


def update_econproj(econ_url, cg_url, baseline):
    """
    Function that will read new CBO economic projections and update
    CBO_baseline.csv accordingly
    """
    print("Updating CBO Economic Projections")
    # read in economic projections
    econ_proj = pd.read_excel(econ_url, sheet_name="2. Calendar Year",
                              skiprows=6, index_col=[0, 1, 2, 3])
    # extract values for needed rows in the excel file
    # some variables have a missing value in the multi-index. Use iloc
    # to extract needed variables from them.
    gdp = econ_proj.loc["Output"].loc["Gross Domestic Product (GDP)"].iloc[0]
    income = econ_proj.loc["Income"]
    tpy = income.loc["Income, Personal"].iloc[0]
    wages = income.loc["Wages and Salaries"].iloc[0]
    billions = "Billions of dollars"
    var = "Proprietors' income, nonfarm, with IVA & CCAdj"
    schc = income.loc["Nonwage Income"].loc[var].loc[billions]
    var = "Proprietors' income, farm, with IVA & CCAdj"
    schf = income.loc["Nonwage Income"].loc[var].loc[billions]
    var = "Interest income, personal"
    ints = income.loc["Nonwage Income"].loc[var].loc[billions]
    var = "Dividend income, personal"
    divs = income.loc["Nonwage Income"].loc[var].loc[billions]
    var = "Income, rental, with CCAdj"
    rents = income.loc["Nonwage Income"].loc[var].loc[billions]
    book = income.loc["Profits, Corporate, With IVA & CCAdj"].iloc[0]
    var = "Consumer Price Index, All Urban Consumers (CPI-U)"
    cpiu = econ_proj.loc["Prices"].loc[var].iloc[0]

    # Extract capital gains data
    cg_proj = pd.read_excel(cg_url, sheet_name="6. Capital Gains Realizations",
                                skiprows=7, header=[0,1])

    dates = cg_proj['Unnamed: 0_level_0']['Unnamed: 0_level_1'].values
    cg = cg_proj['Capital Gains Realizationsa']['Billions of Dollars'].values

    dates = pd.to_numeric(dates, errors='coerce').astype('int64')
    cg = pd.to_numeric(cg, errors='coerce')

    cg_proj = pd.Series(data=cg,index=dates).dropna()

    cgns = cg_proj.loc[list(range(2017,2031))]

    # create one DataFrame from all of the data

    var_list = [gdp, tpy, wages, schc, schf, ints, divs, rents, book, cpiu,
                cgns]
    var_names = ["GDP", "TPY", "Wages", "SCHC", "SCHF", "INTS", "DIVS",
                 "RENTS", "BOOK", "CPIU", "CGNS"]
    df = pd.DataFrame(var_list, index=var_names).round(1)
    df.columns = df.columns.astype(str)

    # update baseline file with the new data

    # add a column for any years that are in the update but not yet in the
    # CBO baseline file before updating the values
    df_cols = set(df.columns)
    baseline_cols = set(baseline.columns)
    for col in df_cols - baseline_cols:
        baseline[col] = None
    baseline.update(df)

    return baseline


def update_cbo():
    econ_url = "https://www.cbo.gov/system/files/2020-07/51135-2020-07-economicprojections.xlsx"
    cg_url = "https://www.cbo.gov/system/files/2020-01/51138-2020-01-revenue-projections.xlsx"
    baseline = pd.read_csv(os.path.join(CUR_PATH, "CBO_baseline.csv"),
                           index_col=0)
    baseline = update_econproj(econ_url, cg_url, baseline)
    baseline = update_cpim(baseline)

    return baseline


if __name__ == "__main__":
    baseline = update_cbo()
    baseline.to_csv(os.path.join(CUR_PATH, "CBO_baseline.csv"))
    msg = ("NOTE: This program does not update every variable in the baseline."
           " Remember to update RETS, SOCSEC, and UCOMP by following the "
           "instructions found in CBO_Baseline_Updating_Instructions.md")
    print(msg)
