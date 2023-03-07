"""
This module contains all of the code needed to update the CBO baseline
projections and documentation and instructions automatically. This code assumes
that format of the websites, spreadsheets, and API we access don't change. If
there is a bug, it's probably because that assumption no longer holds true.
When this happens, modify the code as needed to account for this.
"""
import re
import requests
import pandas as pd
from requests_html import HTMLSession
from pathlib import Path
from datetime import datetime
from jinja2 import Template


CUR_PATH = Path(__file__).resolve().parent


def update_cpim(baseline, text_args):
    """
    Update the CPI-M values in the CBO baseline using the BLS API
    Parameters
    ----------
    baseline: CBO baseline we're updaint
    text_args: Dictionary containing the arguments that will be passed to
        the documentation template
    Returns
    -------
    baseline: Updated baseline numbers
    text_args: Updated dictionary with text aruments to fill in the template
    """
    print("Updating CPI-M Values")
    url = "https://api.bls.gov/publicAPI/v1/timeseries/data/CUSR0000SAM"
    # fetch BLS data from about url
    r = requests.get(url)
    # raise and error if the request fails
    assert r.status_code == 200
    result_json = r.json()
    # raise error if request was not successful
    assert result_json["status"] == "REQUEST_SUCCEEDED"
    # extract the data from the results
    data = result_json["Results"]["series"][0]["data"]
    df = pd.DataFrame(data)
    # convert the values to floats so that the groupby mean only returns
    # the mean for the value
    df["value"] = df["value"].astype(float)
    cpi_mean = df.groupby("year").mean().transpose().round(1)
    cpi_mean.index = ["CPIM"]

    # open the current baseline to replace the values for the years pulled
    # from BLS
    baseline.update(cpi_mean)

    # find the average difference between CPIM and CPIU for available years
    last_year = max(cpi_mean.columns)
    first_year = min(baseline.columns)
    # retrieve subset of the DataFrame containing actual CPIM values
    split_col = int(last_year) - int(first_year) + 1
    sub_baseline = baseline[baseline.columns[:split_col]]

    # find the difference
    mean_diff = (sub_baseline.loc["CPIM"] - sub_baseline.loc["CPIU"]).mean()

    # update the future values to reflect the difference between
    new_vals = {}
    for col in baseline.columns[split_col:]:
        cpiu = baseline[col].loc["CPIU"]
        new_val = cpiu + mean_diff
        new_vals[col] = [new_val]
    future_df = pd.DataFrame(new_vals, index=["CPIM"]).round(1)
    baseline.update(future_df)
    today = datetime.today()
    text_args["cpim_date"] = today.strftime("%B %d %Y")

    return baseline, text_args


def update_econproj(url, baseline, text_args):
    """
    Function that will read new CBO economic projections and update
    CBO_baseline.csv accordingly
    Parameters
    ----------
    url: URL linking to IRS website with projections of federal tax filings
    baseline: CBO baseline we're updaint
    text_args: Dictionary containing the arguments that will be passed to
        the documentation template
    Returns
    -------
    baseline: Updated baseline numbers
    text_args: Updated dictionary with text aruments to fill in the template
    """
    print("Updating CBO Economic Projections")
    # pull all of the latest CBO reports and use them for needed updates
    session = HTMLSession()
    r = session.get(url)
    cbo_pre_url = "https://www.cbo.gov"
    divs = r.html.find("div.view.view-recurring-data")
    revprojections = divs[4]
    # both assertions are there to throw errors if the order of sections change
    # revenue projections used for capital gains projections
    assert "Revenue Projections" in revprojections.text
    latest_revprojections = revprojections.find("div.views-col.col-1")[0]
    rev_link = latest_revprojections.find("a")[0]
    _rev_report = datetime.strptime(rev_link.text, "%b %Y")
    rev_report = datetime.strftime(_rev_report, "%B %Y")
    rev_file_url = rev_link.attrs["href"]
    rev_url = "".join([cbo_pre_url, rev_file_url])

    econprojections = divs[8]
    assert "10-Year Economic Projections" in econprojections.text
    latest_econprojections = econprojections.find("div.views-col.col-1")[0]
    econ_link = latest_econprojections.find("a")[0]
    _cbo_report = datetime.strptime(econ_link.text, "%b %Y")
    cbo_report = datetime.strftime(_cbo_report, "%B %Y")
    econ_file_url = econ_link.attrs["href"]
    econ_url = "".join([cbo_pre_url, econ_file_url])

    if cbo_report == text_args["current_cbo"]:
        print("\tNo new data since last update")
    else:
        # read in economic projections
        econ_proj = pd.read_excel(
            econ_url, sheet_name="2. Calendar Year", skiprows=6, index_col=[0, 1, 2, 3]
        )
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
        var_list = [gdp, tpy, wages, schc, schf, ints, divs, rents, book, cpiu]
        var_names = [
            "GDP",
            "TPY",
            "Wages",
            "SCHC",
            "SCHF",
            "INTS",
            "DIVS",
            "RENTS",
            "BOOK",
            "CPIU",
        ]
        df = pd.DataFrame(var_list, index=var_names).round(1)
        df.columns = df.columns.astype(str)
        df_cols = set(df.columns)
        baseline_cols = set(baseline.columns)
        for col in df_cols - baseline_cols:
            baseline[col] = None
        baseline.update(df)

        text_args["previous_cbo"] = text_args["current_cbo"]
        text_args["current_cbo"] = cbo_report

    if rev_report == text_args["cgns_prev_report"]:
        print("\tNo new data since last update")
        return baseline, text_args
    elif rev_link.text == "Mar 2020":
        msg = (
            "\nCapital gains realizations are not included in CBO's March 2020"
            " revenue projections publication. It's unclear if this is a "
            "permanent change or due to the pandemic. For now, we will skip "
            "this update and re-evaluate when they release their next "
            "projections.\n"
        )
        print(msg)
        return baseline, text_args
    else:
        # Extract capital gains data
        cg_proj = pd.read_excel(
            rev_url,
            sheet_name="6. Capital Gains Realizations",
            skiprows=7,
            header=[0, 1],
        )
        cg_proj.index = cg_proj[cg_proj.columns[0]]
        var = "Capital Gains Realizationsa"
        # increase the CBO final year to (the last year + 1) for each update.
        # e.g. when the CBO final year from CBO is 2033, make the update as range(2017,2034)
        cgns = cg_proj[var]["Billions of Dollars"].loc[list(range(2017, 2034))]
        var_list = [cgns]
        var_names = ["CGNS"]
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

        text_args["cgns_prev_report"] = text_args["cgns_cur_report"]
        text_args["cgns_prev_url"] = text_args["cgns_cur_url"]
        text_args["cgns_cur_report"] = rev_report
        text_args["cgns_cur_url"] = rev_url

    return baseline, text_args


def update_socsec(url, baseline, text_args):
    """
    Function that will read the table with OASI Social Security Projections
    Parameters
    ----------
    url: URL linking to IRS website with projections of federal tax filings
    baseline: CBO baseline we're updaint
    text_args: Dictionary containing the arguments that will be passed to
        the documentation template
    Returns
    -------
    baseline: Updated baseline numbers
    text_args: Updated dictionary with text aruments to fill in the template
    """
    print("Updating Social Security Projections")
    session = HTMLSession()
    r = session.get(url)
    # we can determine the latest year by looking at all of the years availeble
    # in the first drop down and adding one.
    selector = r.html.find("select#yh1")[0]
    latest_yr = max([int(yr) for yr in selector.text.split()]) + 1
    report = f"{latest_yr} Report"
    if report == text_args["socsec_cur_report"]:
        print("\tNo new data since last update")
        return baseline, text_args

    socsec_url = f"https://www.ssa.gov/oact/TR/{latest_yr}/VI_C_SRfyproj.html"
    match_txt = "Operations of the OASI Trust Fund, Fiscal Years"
    html = pd.read_html(socsec_url, match=match_txt)[0]
    # merge the columns with years and data into one
    sub_data = pd.concat(
        [html["Fiscal year", "Fiscal year.1"], html["Cost", "Sched-uled benefits"]],
        axis=1,
    )
    sub_data.columns = ["year", "cost"]
    # further slim down data so that we have the intermediate costs only
    start = sub_data.index[sub_data["year"] == "Intermediate:"][0]
    end = sub_data.index[sub_data["year"] == "Low-cost:"][0]
    cost_data = sub_data.iloc[start + 1 : end].dropna()
    cost_data["cost"] = cost_data["cost"].astype(float)
    # rate we'll use to extrapolate costs to final year we'll need
    pct_change = cost_data["cost"].pct_change() + 1
    cost_data.set_index("year", inplace=True)
    cost_data = cost_data.transpose()
    cost_data.index = ["SOCSEC"]
    # create values for years not included in the report
    factor = pct_change.iloc[-1]
    last_year = int(max(cost_data.columns))
    cbo_last_year = int(max(baseline.columns))
    for year in range(last_year + 1, cbo_last_year + 1):
        cost_data[str(year)] = cost_data[str(year - 1)] * factor
    cost_data = cost_data.round(1)
    # finally update CBO projections
    baseline.update(cost_data)

    text_args["socsec_prev_report"] = text_args["socsec_cur_report"]
    text_args["socsec_prev_url"] = text_args["socsec_cur_url"]
    text_args["socsec_cur_report"] = report
    text_args["socsec_cur_url"] = socsec_url

    return baseline, text_args


def update_rets(url, baseline, text_args):
    """
    Update projected tax returns
    Parameters
    ----------
    url: URL linking to IRS website with projections of federal tax filings
    baseline: CBO baseline we're updaint
    text_args: Dictionary containing the arguments that will be passed to
        the documentation template
    Returns
    -------
    baseline: Updated baseline numbers
    text_args: Updated dictionary with text aruments to fill in the template
    """
    print("Updating Return Projections")
    session = HTMLSession()
    r = session.get(url)
    # find year of new reports
    title = (
        "Calendar Year Projections of Individual Returns by Major Processing "
        "Categories, Selected Years and Areas, {} {} "
    )
    search = r.html.search(title)
    report_name = f"{search[0]} {search[1][:4]}"
    report = f"{report_name} Report"
    if report == text_args["rets_cur_report"]:
        print("\tNo new data since last update")
        return baseline, text_args

    links = r.html.links
    pattern = r"[\W\w]+6187[\w\W]+xls"
    for link in links:
        if re.match(pattern, link):
            spreadsheet_url = link
            break
    data = pd.read_excel(spreadsheet_url, sheet_name="1B-BOD", index_col=0, header=2)
    projections = data.loc["Forms 1040, 1040-SR, and 1040-SP, Total"]
    projections /= 1_000_000  # convert units
    pct_change = projections.pct_change() + 1
    # extrapolate out to final year of other CBO projections
    factor = pct_change.iloc[-1]
    last_year = int(max(projections.index))
    cbo_last_year = int(max(baseline.columns))
    df_projections = pd.DataFrame(projections).transpose()
    df_projections.columns = df_projections.columns.astype(str)
    for year in range(last_year + 1, cbo_last_year + 1):
        df_projections[str(year)] = df_projections[str(year - 1)] * factor
    df_projections.index = ["RETS"]
    df_projections = df_projections.round(1)
    baseline.update(df_projections)

    text_args["rets_prev_report"] = text_args["rets_cur_report"]
    text_args["rets_prev_url"] = text_args["rets_cur_url"]
    text_args["rets_cur_report"] = report
    text_args["rets_cur_url"] = spreadsheet_url
    return baseline, text_args


def update_ucomp(url, baseline, text_args):
    """
    Update unemployment compensation projections
    Parameters
    ----------
    url: URL linking to IRS website with projections of federal tax filings
    baseline: CBO baseline we're updaint
    text_args: Dictionary containing the arguments that will be passed to
        the documentation template
    Returns
    -------
    baseline: Updated baseline numbers
    text_args: Updated dictionary with text aruments to fill in the template
    """
    print("Updating Unemployment Projections")
    session = HTMLSession()
    r = session.get(url)
    links = r.html.links
    ucomp_links = []
    ucomp_years = []
    for link in links:
        if "unemployment" in link.lower() and link.endswith("xlsx"):
            date = re.search(r"20\d\d-\d\d", link).group()
            ucomp_links.append(link)
            ucomp_years.append(datetime.strptime(date, "%Y-%m"))
    latest_year = max(ucomp_years)
    ucomp_url = ucomp_links[ucomp_years.index(latest_year)]
    report = datetime.strftime(latest_year, "%B %Y")
    if report == text_args["ucomp_cur_report"]:
        print("\tNo new data since last update")
        return baseline, text_args
    elif report == "February 2021":
        print("Latest data is from pandemic. Enter by hand")
        return baseline, text_args
    data = pd.read_excel(ucomp_url, skiprows=3, index_col=0, thousands=",")
    try:
        benefits = data.loc["Budget Authority"].dropna().astype(int) / 1000
    except KeyError:
        benefits = data.loc["Budget Authority"].dropna().astype(int) / 1000
    benefits = benefits.round(1)
    df = pd.DataFrame(benefits).transpose()
    df.index = ["UCOMP"]
    df.columns = df.columns.astype(str)
    baseline.update(df)

    text_args["ucomp_prev_report"] = text_args["ucomp_cur_report"]
    text_args["ucomp_prev_url"] = text_args["ucomp_cur_url"]
    text_args["ucomp_cur_report"] = report
    text_args["ucomp_cur_url"] = ucomp_url

    return baseline, text_args


def fill_text_args(text):
    """
    Provide initial values for all text arguments
    """
    text_args = {}
    previous_cbo_doc = re.search(r"Previous Document: ([\w \d]+)", text).groups()[0]
    cur_cbo_doc = re.search(r"Current Document: ([\w \d]+)", text).groups()[0]
    text_args["previous_cbo"] = previous_cbo_doc
    text_args["current_cbo"] = cur_cbo_doc

    section_pattern = r"### {}[\d\w \n:\[\]\(\)/\.\-,`\?=\"#]+"
    sections = ["CGNS", "RETS", "SOCSEC", "UCOMP"]
    url_pattern = r"{}: [\w\[\] \d\(\)://\.\-#]+"
    for section in sections:
        sub_txt = re.search(section_pattern.format(section), text).group()
        prev = re.search(url_pattern.format("Previous"), sub_txt).group()
        cur = re.search(url_pattern.format("Current"), sub_txt).group()
        text_args[f"{section.lower()}_prev_report"] = re.search(
            r"\[[\w \d]+\]", prev
        ).group()[1:-1]
        text_args[f"{section.lower()}_cur_report"] = re.search(
            r"\[[\w \d]+\]", cur
        ).group()[1:-1]
        text_args[f"{section.lower()}_prev_url"] = re.search(
            r"\([\w\W]+\)", prev
        ).group()[1:-1]
        text_args[f"{section.lower()}_cur_url"] = re.search(
            r"\([\w\W]+\)", cur
        ).group()[1:-1]

    return text_args


def update_cbo():
    out_path = Path(
        CUR_PATH,
        "..",
        "docs",
        "book",
        "content",
        "methods",
        "CBO_Baseline_Updating_Instructions.md",
    )
    template_str = Path(CUR_PATH, "doc", "cbo_instructions_template.md").open().read()
    current_text = out_path.open().read()
    text_args = fill_text_args(current_text)
    baseline = pd.read_csv(Path(CUR_PATH, "CBO_baseline.csv"), index_col=0)
    CBO_URL = "https://www.cbo.gov/about/products/budget-economic-data"
    SOCSEC_URL = "https://www.ssa.gov/oact/TR/"
    RETS_URL = "https://www.irs.gov/statistics/soi-tax-stats-calendar-year-projections-publication-6187"
    UCOMP_URL = (
        "https://www.cbo.gov/about/products/baseline-projections-selected-programs"
    )

    baseline, text_args = update_econproj(CBO_URL, baseline, text_args)
    baseline, text_args = update_cpim(baseline, text_args)
    baseline, text_args = update_socsec(SOCSEC_URL, baseline, text_args)
    baseline, text_args = update_rets(RETS_URL, baseline, text_args)
    baseline, text_args = update_ucomp(UCOMP_URL, baseline, text_args)

    template = Template(template_str)
    rendered = template.render(**text_args)
    out_path.write_text(rendered)

    return baseline


if __name__ == "__main__":
    baseline = update_cbo()
    baseline.to_csv(Path(CUR_PATH, "CBO_baseline.csv"))
