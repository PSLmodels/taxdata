"""
Utility functions used by report.py
"""
import pypandoc
import pandas as pd
import numpy as np
import altair as alt
import taxcalc as tc
from jinja2 import Template
from pathlib import Path
from collections import defaultdict


CUR_PATH = Path(__file__).resolve().parent
EPSILON = 1e-9


def run_calc(calc, year, var_list):
    """
    Parameters
    ----------
    calc: tax calculator object
    year: year to run calculator for
    var_list: list of variables to return waited total of
    """
    calc.advance_to_year(year)
    calc.calc_all()
    totals = {}
    for var in var_list:
        totals[var] = calc.weighted_total(var) * 1e-9
    return totals


def run_calc_var(calc, year, var):
    """
    Parameters
    ----------
    calc: tax calculator object
    year: year to run calculator for
    var: the variable to return waited total of
    """
    calc.advance_to_year(year)
    calc.calc_all()
    total = calc.weighted_total(var) * 1e-9
    return total


def add_bins(
    dframe,
    income_measure,
    num_bins,
    wt="s006",
    decile_details=False,
    weight_by_income_measure=False,
):
    """
    Add a variable to specified Pandas DataFrame, dframe, that specifies the
    table row and is called 'table_row'.  The rows hold equal number of
    filing units when weight_by_income_measure=False or equal number of
    income dollars when weight_by_income_measure=True.  Assumes that
    specified dframe contains columns for the specified income_measure and
    for sample weights, s006.  When num_quantiles is 10 and decile_details
    is True, the bottom decile is broken up into three subgroups (neg, zero,
    and pos income_measure ) and the top decile is broken into three subgroups
    (90-95, 95-99, and top 1%).
    """
    assert isinstance(dframe, pd.DataFrame)
    assert income_measure in dframe
    if decile_details and num_bins != 10:
        msg = "decile_details is True when num_quantiles is {}"
        raise ValueError(msg.format(num_bins))
    dframe.sort_values(by=income_measure, inplace=True)
    if weight_by_income_measure:
        dframe["cumsum_temp"] = np.cumsum(
            np.multiply(dframe[income_measure].values, dframe[wt].values)
        )
        min_cumsum = dframe["cumsum_temp"].values[0]
    else:
        dframe["cumsum_temp"] = np.cumsum(dframe[wt].values)
        min_cumsum = 0.0  # because s006 values are non-negative
    max_cumsum = dframe["cumsum_temp"].values[-1]
    cumsum_range = max_cumsum - min_cumsum
    bin_width = cumsum_range / float(num_bins)
    bin_edges = list(min_cumsum + np.arange(0, (num_bins + 1)) * bin_width)
    bin_edges[-1] = 9e99  # raise top of last bin to include all observations
    bin_edges[0] = -9e99  # lower bottom of 1st bin to include all observation00s
    if decile_details:
        assert bin_edges[1] > 1e-9  # bin_edges[1] is top of bottom decile
        bin_edges.insert(1, 1e-9)  # top of zeros
        bin_edges.insert(1, -1e-9)  # top of negatives
        bin_edges.insert(-1, bin_edges[-2] + 0.5 * bin_width)  # top of 90-95
        bin_edges.insert(-1, bin_edges[-2] + 0.4 * bin_width)  # top of 95-99
        num_bins += 4
    labels = range(1, (num_bins + 1))
    dframe["bins"] = pd.cut(
        dframe["cumsum_temp"], bin_edges, right=False, labels=labels
    )
    dframe.drop("cumsum_temp", axis=1, inplace=True)
    return dframe


def weighted_mean(pdf, col_name, wt_name="s006"):
    """
    Return weighted mean of col_name

    Parameters
    ----------
    pdf: Pandas DataFrame object
    col_name: variable to be averaged
    wt_name: weight
    """
    return float((pdf[col_name] * pdf[wt_name]).sum()) / float(
        pdf[wt_name].sum() + EPSILON
    )


def weighted_sum(pdf, col_name, wt_name="s006"):
    """
    Return weighted sum of col_name

    Parameters
    ----------
    pdf: Pandas DataFrame object
    col_name: variable to be averaged
    wt_name: weight
    """
    return float((pdf[col_name] * pdf[wt_name]).sum())


def percentile(
    pdf,
    col_name,
    num_bins,
    income_measure,
    wt="s006",
    income_wt=False,
    result_type="avg",
    decile_details=False,
):
    """ """
    qpdf = add_bins(
        pdf,
        income_measure=income_measure,
        num_bins=num_bins,
        wt=wt,
        decile_details=decile_details,
        weight_by_income_measure=income_wt,
    )
    gpdf = qpdf.groupby("bins", as_index=False)
    if result_type == "avg":
        wpdf = gpdf.apply(weighted_mean, col_name)
    elif result_type == "sum":
        wpdf = gpdf.apply(weighted_sum, col_name)
    else:
        msg = 'result_type must be "avg" or "sum"'
        raise ValueError(msg)
    return wpdf


def distribution(item, weight, agi):
    """
    Return distribution of item by AGI level
    """
    total = (item * weight).sum()
    agi_1 = (item[agi < 0] * weight[agi < 0]).sum()
    pct1 = round(agi_1 / total, 2)
    agi_2 = (item[(agi > 1) & (agi < 5000)] * weight[(agi > 1) & (agi < 5000)]).sum()
    pct2 = round(agi_1 / total, 2)
    agi_3 = (
        item[(agi > 5000) & (agi < 10000)] * weight[(agi > 5000) & (agi < 10000)]
    ).sum()
    pct3 = round(agi_3 / total, 2)
    agi_4 = (
        item[(agi > 10000) & (agi < 15000)] * weight[(agi > 10000) & (agi < 15000)]
    ).sum()
    pct4 = round(agi_4 / total, 2)
    agi_5 = (
        item[(agi > 15000) & (agi < 20000)] * weight[(agi > 15000) & (agi < 20000)]
    ).sum()
    pct5 = round(agi_5 / total, 2)
    agi_6 = (
        item[(agi > 20000) & (agi < 25000)] * weight[(agi > 20000) & (agi < 25000)]
    ).sum()
    pct6 = round(agi_6 / total, 2)
    agi_7 = (
        item[(agi > 25000) & (agi < 30000)] * weight[(agi > 25000) & (agi < 30000)]
    ).sum()
    pct7 = round(agi_7 / total, 2)
    agi_8 = (
        item[(agi > 30000) & (agi < 40000)] * weight[(agi > 30000) & (agi < 40000)]
    ).sum()
    pct8 = round(agi_8 / total, 2)
    agi_9 = (
        item[(agi > 40000) & (agi < 50000)] * weight[(agi > 40000) & (agi < 50000)]
    ).sum()
    pct9 = round(agi_9 / total, 2)
    agi_10 = (
        item[(agi > 50000) & (agi < 75000)] * weight[(agi > 50000) & (agi < 75000)]
    ).sum()
    pct10 = round(agi_10 / total, 2)
    agi_11 = (
        item[(agi > 75000) & (agi < 100_000)] * weight[(agi > 75000) & (agi < 100_000)]
    ).sum()
    pct11 = round(agi_11 / total, 2)
    agi_12 = (
        item[(agi > 100_000) & (agi < 200_000)]
        * weight[(agi > 100_000) & (agi < 200_000)]
    ).sum()
    pct12 = round(agi_12 / total, 2)
    agi_13 = (
        item[(agi > 200_000) & (agi < 500_000)]
        * weight[(agi > 200_000) & (agi < 500_000)]
    ).sum()
    pct13 = round(agi_13 / total, 2)
    agi_14 = (
        item[(agi > 500_000) & (agi < 1_000_000)]
        * weight[(agi > 500_000) & (agi < 1_000_000)]
    ).sum()
    pct14 = round(agi_14 / total, 2)
    agi_15 = (
        item[(agi > 1_000_000) & (agi < 1_500_000)]
        * weight[(agi > 1_000_000) & (agi < 1_500_000)]
    ).sum()
    pct15 = round(agi_15 / total, 2)
    agi_16 = (
        item[(agi > 1_500_000) & (agi < 2_000_000)]
        * weight[(agi > 1_500_000) & (agi < 2_000_000)]
    ).sum()
    pct16 = round(agi_16 / total, 2)
    agi_17 = (
        item[(agi > 2_000_000) & (agi < 5_000_000)]
        * weight[(agi > 2_000_000) & (agi < 5_000_000)]
    ).sum()
    pct17 = round(agi_17 / total, 2)
    agi_18 = (
        item[(agi > 5_000_000) & (agi < 10_000_000)]
        * weight[(agi > 5_000_000) & (agi < 10_000_000)]
    ).sum()
    pct18 = round(agi_18 / total, 2)
    agi_19 = (item[agi > 10_000_000] * weight[agi > 10_000_000]).sum()
    pct19 = round(agi_19 / total, 2)
    df = [
        agi_1,
        agi_2,
        agi_3,
        agi_4,
        agi_5,
        agi_6,
        agi_7,
        agi_8,
        agi_9,
        agi_10,
        agi_11,
        agi_12,
        agi_13,
        agi_14,
        agi_15,
        agi_16,
        agi_17,
        agi_18,
        agi_19,
    ]
    pct = [
        pct1,
        pct2,
        pct3,
        pct4,
        pct5,
        pct6,
        pct7,
        pct8,
        pct9,
        pct10,
        pct11,
        pct12,
        pct13,
        pct14,
        pct15,
        pct16,
        pct17,
        pct18,
        pct19,
    ]
    index = [
        "Zero or Negative",
        "$1-$5K",
        "$5K-$10K",
        "$10K-$15K",
        "$15K-$20K",
        "$20K-$25K",
        "$25K-$30K",
        "$30K-$40K",
        "$40K-$50K",
        "$50K-$75K",
        "$75K-$100K",
        "$100K-$200K",
        "$200K-$500K",
        "$500K-$1M",
        "$1M-$1.5M",
        "$1.5M-$2M",
        "$2M-$5M",
        "$5M-$10M",
        "$10M and over",
    ]
    return df, pct, index


def distplot(
    calcs: list,
    calc_labels: list,
    var: str,
    income_measure: str = "expanded_income",
    result_type: str = "pct",
    width=800,
    height=350,
    title="",
):
    """
    Parameters
    ----------
    calcs: list of tax calculator objects
    calc_labels: labels for each calculator
    var: variable whose distribution we're plotting
    income_measure: income measure used to create bins
    result_type: pct or sum
    """

    def getdata(calc, var, income_measure):
        agg, pct, index = distribution(
            calc.array(var), calc.array("s006"), calc.array(income_measure)
        )
        return agg, pct, index

    assert result_type in ["pct", "sum"]
    pltdata = pd.DataFrame()
    for calc, label in zip(calcs, calc_labels):
        agg, pct, index = getdata(calc, var, income_measure)
        if result_type == "pct":
            pltdata[label] = pct
        else:
            pltdata[label] = [_ * 1e-9 for _ in agg]
    pltdata["index"] = index
    melted = pd.melt(pltdata, id_vars="index")
    if result_type == "pct":
        y_label = "Percent of Total"
        y_format = "%"
    else:
        y_label = "Total (billions)"
        y_format = "$.3f"
    plt = (
        alt.Chart(melted, title=title)
        .mark_circle(size=50)
        .encode(
            alt.X(
                "index:O",
                sort=index,
                axis=alt.Axis(
                    title="Expanded Income Bin",
                    labelAngle=-90,
                    labelFontSize=15,
                    titleFontSize=20,
                ),
            ),
            alt.Y(
                "value",
                axis=alt.Axis(
                    format=y_format, title=y_label, labelFontSize=15, titleFontSize=20
                ),
            ),
            color=alt.Color(
                "variable",
                legend=alt.Legend(
                    title="File", symbolSize=150, labelFontSize=15, titleFontSize=20
                ),
            ),
        )
        .properties(width=width, height=height)
        .configure_title(fontSize=24)
    )
    return plt


def write_page(pathout, template_path, **kwargs):
    """
    Render the HTML template with the markdown text
    Parameters
    ----------
    pathout: path where the HTML file will be saved
    template_path: path for the HTML template
    Returns
    -------
    None
    """
    # read and render HTML template
    template_str = template_path.open("r").read()
    template = Template(template_str)
    rendered = template.render(**kwargs)
    pypandoc.convert_text(
        rendered,
        "pdf",
        format="md",
        outputfile=str(pathout),
        extra_args=["-V", "geometry:margin=1in"],
    )


def cbo_bar_chart(cbo_data, var, title, bar_width=30, width=600, height=250):
    """
    Creates a bar chart comparing the current and new CBO projections
    Parameters
    ----------
    cbo_data: data containing both current and new CBO projections
        concatenated together
    var: Y-axis variable
    title: title of the chart
    bar_width: width of the bars in the plot
    width: width of the chart
    height: height of the chart
    """
    # we divide up total width equally among facets of the chart
    _width = width / len(cbo_data["index"].value_counts())
    chart = (
        alt.Chart(cbo_data, title=title)
        .mark_bar(width=bar_width)
        .encode(
            x=alt.X(
                "Projections",
                axis=alt.Axis(title=None, labels=False, ticks=False, labelFontSize=15),
            ),
            y=alt.Y(var, axis=alt.Axis(labelFontSize=10, titleFontSize=15)),
            color=alt.Color("Projections"),
            column=alt.Column(
                "index", header=alt.Header(title=None, labelOrient="bottom")
            ),
        )
        .properties(height=height, width=_width)
        .configure_view(stroke="transparent")
        .configure_facet(spacing=0)
        .configure_title(fontSize=20)
    )
    return chart


def compare_vars(cur_meta, new_meta, file_):
    """
    Searches for differences in variable availability
    Parameters
    ----------
    url: URL to current records metadata
    path: Path to updated records metadata
    availability: Which files availability to search. Either puf or cps
    """

    def form_output(meta, var_list):
        """
        Return formatted output
        """
        output = []
        meta_dict = meta.to_dict("index")
        for var in var_list:
            desc = meta_dict[var]["desc"]
            output.append(f"* {var}: {desc}")
        return output

    if file_ not in ["puf", "cps"]:
        msg = "'file' must be either 'cps' or 'puf'"
        raise ValueError(msg)
    _file = f"taxdata_{file_}"
    cur_avail = set(cur_meta[cur_meta["availability"].str.contains(_file)].index)
    new_avail = set(new_meta[new_meta["availability"].str.contains(_file)].index)
    _added_vars = new_avail - cur_avail
    _removed_vars = cur_avail - new_avail
    # get detailed information
    if _added_vars:
        added_vars = form_output(new_meta, _added_vars)
    else:
        added_vars = ["None"]
    if _removed_vars:
        removed_vars = form_output(cur_meta, _removed_vars)
    else:
        removed_vars = ["None"]
    return added_vars, removed_vars


def growth_scatter_plot(data, rows, point_size=150, width=600, height=300, columns=2):
    """
    Create a scatter plot to show changes in growth factors
    Parameters
    ----------
    data: growth factor data
    factor: factor we"re plotting
    """
    max_val = data.max().drop(index=["YEAR", "Growth Factors"]).max()
    min_val = data.min().drop(index=["YEAR", "Growth Factors"]).min()
    chart = (
        alt.Chart(data)
        .mark_circle(size=point_size, filled=True)
        .encode(
            x=alt.X(
                "YEAR",
                type="ordinal",
                axis=alt.Axis(labelAngle=-45, labelFontSize=25, titleFontSize=30),
            ),
            y=alt.Y(
                alt.repeat(),
                type="quantitative",
                scale=alt.Scale(domain=[min_val, max_val]),
                axis=alt.Axis(labelFontSize=25, titleFontSize=30),
            ),
            color=alt.Color(
                "Growth Factors",
                legend=alt.Legend(
                    symbolSize=300,
                    labelFontSize=20,
                    titleFontSize=25,
                    direction="horizontal",
                    orient="top",
                ),
            ),
        )
        .properties(width=width, height=height)
        .repeat(rows, columns=columns)
        .configure_legend(labelLimit=0, titleLimit=0)
    )
    return chart


def agg_liability_table(data, tax):
    """
    Creates a markdown table to display aggregate tax liability
    """
    df = data[data["Tax"].str.contains(tax)].copy()
    cur_df = df[df["Tax"] == f"Current {tax}"].copy()
    new_df = df[df["Tax"] == f"New {tax}"].copy()
    cur_df.drop(columns=["Tax"], inplace=True)
    new_df.drop(columns=["Tax"], inplace=True)
    cur_df = cur_df.set_index("Year").transpose().round(1)
    new_df = new_df.set_index("Year").transpose().round(1)
    cur_df.index = ["Current"]
    new_df.index = ["New"]
    final_df = pd.concat([cur_df, new_df])
    diff = final_df.loc["New"] - final_df.loc["Current"]
    final_df.loc["Change"] = diff.round(1)
    pct_change = diff / final_df.loc["Current"] * 100
    final_df.loc["Pct Change"] = pct_change.round(2)
    return final_df.to_markdown()


def projection_table(data, category):
    """
    Creates a markdown table to display detailed projections
    """
    df = data[data["Category"].str.contains(category)].copy()
    cur_df = df[df["Category"] == f"Current {category}"].copy()
    new_df = df[df["Category"] == f"New {category}"].copy()
    cur_df.drop("Category", axis=1, inplace=True)
    new_df.drop("Category", axis=1, inplace=True)
    cur_df = cur_df.set_index("Year").transpose().round(1)
    new_df = new_df.set_index("Year").transpose().round(1)
    diff = new_df - cur_df
    diff = diff.round(1)
    pct_change = diff / cur_df * 100
    pct_change = pct_change.round(2)
    cur_df.index = ["Current"]
    new_df.index = ["New"]
    diff.index = ["Change"]
    pct_change.index = ["Pct Change"]
    final_df = pd.concat([cur_df, new_df, diff, pct_change])

    return final_df.to_markdown()


def calculate_agi_share(calc, year):
    calc.advance_to_year(year)
    calc.calc_all()

    vdf = calc.dataframe(["s006", "c00100", "expanded_income"]).sort_values(
        by="expanded_income", ascending=False
    )
    vdf = tc.add_quantile_table_row_variable(
        vdf,
        "expanded_income",
        num_quantiles=100,
        pop_quantiles=False,
        decile_details=False,
        weight_by_income_measure=False,
    )
    gbydf = vdf.groupby("table_row", as_index=False)

    agi_share = 0
    tot_agi = float((vdf["c00100"] * vdf["s006"]).sum())
    idx = 1
    agi_brk = []

    for grp_interval, grp in gbydf:
        agi_item = (grp["c00100"] * grp["s006"]).sum()
        agi_brk.append(agi_item)
        idx += 1

    agi_brk.reverse()

    agi_q1 = 0
    agi_q5 = 0
    agi_q10 = 0
    agi_q25 = 0
    agi_q50 = 0

    for i in range(0, 1):
        agi_q1 = agi_q1 + agi_brk[i]
    for i in range(0, 5):
        agi_q5 = agi_q5 + agi_brk[i]
    for i in range(0, 10):
        agi_q10 = agi_q10 + agi_brk[i]
    for i in range(0, 25):
        agi_q25 = agi_q25 + agi_brk[i]
    for i in range(0, 50):
        agi_q50 = agi_q50 + agi_brk[i]

    agi_s1 = (agi_q1 / tot_agi) * 100
    agi_s5 = (agi_q5 / tot_agi) * 100
    agi_s10 = (agi_q10 / tot_agi) * 100
    agi_s25 = (agi_q25 / tot_agi) * 100
    agi_s50 = (agi_q50 / tot_agi) * 100

    return agi_s1, agi_s5, agi_s10, agi_s25, agi_s50


def agi_share_table(data, incomegroup):
    """
    Creates a markdown table to display detailed agi share
    """
    df = data[data["Incomegroup"].str.contains(incomegroup)]
    cur_df = df[df["Incomegroup"] == f"Current {incomegroup}"]
    new_df = df[df["Incomegroup"] == f"New {incomegroup}"]
    cur_df.drop("Incomegroup", axis=1, inplace=True)
    new_df.drop("Incomegroup", axis=1, inplace=True)
    cur_df = cur_df.set_index("Year").transpose().round(2)
    new_df = new_df.set_index("Year").transpose().round(2)

    diff = new_df - cur_df
    diff = diff.round(1)
    pct_change = diff / cur_df * 100
    pct_change = pct_change.round(2)

    cur_df.index = ["Current"]
    new_df.index = ["New"]
    diff.index = ["Change"]
    pct_change.index = ["Pct Change"]
    final_df = pd.concat([cur_df, new_df, diff, pct_change])

    return final_df.to_markdown()


def CBO_projections(rev_proj):
    """
    Read CBO published projections values from the webpage
    "https://www.cbo.gov/about/products/budget-economic-data"
    """

    # extract values for AGI rows in the excel file
    salary_wage = rev_proj.loc["Calculation of Adjusted Gross Income (AGI)"].loc[
        "Salaries and wages"
    ]
    taxable_interest_ordinary_divid = rev_proj.loc[
        "Calculation of Adjusted Gross Income (AGI)"
    ].loc["Taxable interest and ordinary dividends (excludes qualified dividends)"]
    q_div = rev_proj.loc["Calculation of Adjusted Gross Income (AGI)"].loc[
        "Qualified dividends                                         "
    ]
    capital_g_l = rev_proj.loc["Calculation of Adjusted Gross Income (AGI)"].loc[
        "Capital gain or lossa"
    ]
    business_inc = rev_proj.loc["Calculation of Adjusted Gross Income (AGI)"].loc[
        "Net business income (all income and loss reported on Schedules C, E, and F)b"
    ]
    pension_annuities_IRAdis = rev_proj.loc[
        "Calculation of Adjusted Gross Income (AGI)"
    ].loc["Taxable pensions and annuities and IRA distributions"]
    ssb = rev_proj.loc["Calculation of Adjusted Gross Income (AGI)"].loc[
        "Taxable Social Security benefits                  "
    ]
    other_inc = rev_proj.loc["Calculation of Adjusted Gross Income (AGI)"].loc[
        "All other sources of incomec"
    ]
    total_inc = rev_proj.loc["Calculation of Adjusted Gross Income (AGI)"].loc[
        "Total income"
    ]
    stat_adj = rev_proj.loc["Calculation of Adjusted Gross Income (AGI)"].loc[
        "Subtract Statutory adjustments                       "
    ]
    total_agi = rev_proj.loc["Calculation of Adjusted Gross Income (AGI)"].loc[
        "Adjusted gross income               "
    ]
    sub_peronal_expt = rev_proj.loc["Calculation of Taxable Income"].loc[
        "Subtract Personal exemption amount (after limit)"
    ]
    sub_std = rev_proj.loc["Calculation of Taxable Income"].loc[
        "Subtract Standard deduction (non-itemizers only)"
    ]
    sub_tot_item = rev_proj.loc["Calculation of Taxable Income"].loc[
        "Subtract Total itemized deductions (itemizers only) after limitsd"
    ]
    sub_qbid = rev_proj.loc["Calculation of Taxable Income"].loc[
        "Subtract Qualified business income deduction"
    ]
    sub_tot_expt = rev_proj.loc["Calculation of Taxable Income"].loc[
        "Total exemptions and deductions after limitse"
    ]
    taxable_inc = rev_proj.loc["Calculation of Taxable Income"].loc["Taxable incomef"]
    tot_inctax = rev_proj.loc["Calculation of Income Tax Liability"].loc[
        "Total income tax (including AMT) before credits"
    ]
    tot_cdt = rev_proj.loc["Calculation of Income Tax Liability"].loc[
        "Total credits (refundable and nonrefundable)i"
    ]
    inctax_af_credit = rev_proj.loc["Calculation of Income Tax Liability"].loc[
        "Income tax after creditsj"
    ]
    Top1p = rev_proj.loc["Shares of AGI by Income Group (Percent)o"].loc[
        "Top 1 percent"
    ]
    Top5p = rev_proj.loc["Shares of AGI by Income Group (Percent)o"].loc[
        "Top 5 percent"
    ]
    Top10p = rev_proj.loc["Shares of AGI by Income Group (Percent)o"].loc[
        "Top 10 percent"
    ]
    Top25p = rev_proj.loc["Shares of AGI by Income Group (Percent)o"].loc[
        "Top 25 percent"
    ]
    Top50p = rev_proj.loc["Shares of AGI by Income Group (Percent)o"].loc[
        "Top 50 percent"
    ]

    var_list = [
        salary_wage,
        taxable_interest_ordinary_divid,
        q_div,
        capital_g_l,
        business_inc,
        pension_annuities_IRAdis,
        ssb,
        other_inc,
        total_inc,
        stat_adj,
        total_agi,
        sub_peronal_expt,
        sub_std,
        sub_tot_item,
        sub_qbid,
        sub_tot_expt,
        taxable_inc,
        tot_inctax,
        tot_cdt,
        inctax_af_credit,
        Top1p,
        Top5p,
        Top10p,
        Top25p,
        Top50p,
    ]
    var_names = [
        "Salaries",
        "Interests",
        "Qdividends",
        "Capital",
        "Business",
        "Pensions",
        "Security",
        "Other",
        "Totalincome",
        "Statutory",
        "AGI",
        "Pexpt",
        "Standardded",
        "totitem",
        "qbid",
        "totalexpt",
        "taxincome",
        "totalinctax",
        "totalcredit",
        "aftercdttax",
        "Top1p",
        "Top5p",
        "Top10p",
        "Top25p",
        "Top50p",
    ]
    df = pd.DataFrame(var_list, index=var_names).round(1)
    df.columns = df.columns.astype(str)
    df_cols = set(df.columns)
    return df


def validation_table(df_tax_data, df_cbo, category):
    """
    Creates a markdown table to display detailed validation between
    taxdata new projections and CBO projections
    """

    df = df_tax_data[df_tax_data["Category"].str.contains(category)].copy()
    new_df = df[df["Category"] == f"New {category}"].copy()
    new_df.drop("Category", axis=1, inplace=True)
    new_df = new_df.set_index("Year").round(1)
    new_df = new_df.rename_axis(index=None).squeeze()
    new_df.index = new_df.index.astype(str)
    df_cbo = df_cbo.drop(
        columns=["2019", "2020", "2021", "2022", "2033"], axis=1, inplace=False
    )
    df_cbo = df_cbo.transpose()
    df_cbo_sal = df_cbo.loc[:, df_cbo.columns.str.contains(category)].squeeze()
    df_cbo_sal = df_cbo_sal.astype(float)
    diff = new_df - df_cbo_sal
    pct_change = diff / new_df * 100
    pct_change = pct_change.round(2)
    final_df = pd.DataFrame(
        dict(
            TaxData_projection=new_df,
            CBO_projection=df_cbo_sal,
            difference=diff,
            percent_difference=pct_change,
        )
    )

    return final_df.to_markdown()


def compare_calcs(base, new, name, template_args, plot_paths):
    """
    Function for comparing the results from tax-calculator using the old and
    new data

    Parameters
    ----------
    base : Calculator object
        Tax-Calculator object using the old data
    new : Calculator object
        Tax-Calculator object using the new data
    name : str
        string name for which dataset is being compared. Must be `puf` or `cps`
    """
    if name not in ["puf", "cps"]:
        raise ValueError(f"{name} is not valid. Must be `puf` or `cps`.")
    calcs = [base, new]
    calc_labels = [f"Current {name.upper()}", f"New {name.upper()}"]
    # distribution plots
    dist_vars = [
        ("c00100", "AGI Distribution"),
        ("combined", "Tax Liability Distribution"),
    ]
    dist_plots = []
    for var, title in dist_vars:
        plot = distplot(calcs, calc_labels, var, title=title)
        img_path = Path(CUR_PATH, f"{name}_{var}_dist.png")
        plot.save(str(img_path))
        plot_paths.append(img_path)
        dist_plots.append(f"![]({str(img_path)})" + "{.center}")
    template_args[f"{name}_dist_plots"] = dist_plots

    # aggregate totals
    aggs = defaultdict(list)
    aggs2 = defaultdict(list)
    aggs3 = defaultdict(list)
    var_list = ["payrolltax", "iitax", "combined", "standard", "c04470"]
    for year in range(base.current_year, tc.Policy.LAST_BUDGET_YEAR + 1):
        base_aggs = run_calc(base, year, var_list)
        new_aggs = run_calc(new, year, var_list)
        cur_salary_wage = run_calc_var(base, year, "e00200")
        cur_taxable_interest_ordinary_divid = (
            run_calc_var(base, year, "e00300")
            + run_calc_var(base, year, "e00600")
            - run_calc_var(base, year, "e00650")
        )
        cur_q_div = run_calc_var(base, year, "e00650")
        cur_capital_g_l = (
            run_calc_var(base, year, "e01100")
            + run_calc_var(base, year, "e01200")
            + run_calc_var(base, year, "c23650")
        )
        cur_business_inc = (
            run_calc_var(base, year, "e00900")
            + run_calc_var(base, year, "e02000")
            + run_calc_var(base, year, "e02100")
        )
        cur_pension_annuities_IRAdis = run_calc_var(
            base, year, "e01400"
        ) + run_calc_var(base, year, "e01700")
        cur_ssb = run_calc_var(base, year, "c02500")
        cur_total_inc = run_calc_var(base, year, "c00100") + run_calc_var(
            base, year, "c02900"
        )
        cur_stat_adj = run_calc_var(base, year, "c02900")
        cur_total_agi = run_calc_var(base, year, "c00100")
        cur_other_inc = (
            cur_total_inc
            - cur_salary_wage
            - cur_taxable_interest_ordinary_divid
            - cur_capital_g_l
            - cur_pension_annuities_IRAdis
            - cur_ssb
        )
        cur_sub_personal_expt = run_calc_var(base, year, "c04600")
        cur_sub_std = run_calc_var(base, year, "standard")
        cur_sub_tot_item = run_calc_var(base, year, "c04470")
        cur_sub_qbid = run_calc_var(base, year, "qbided")
        cur_sub_tot_expt = (
            run_calc_var(base, year, "c04600")
            + run_calc_var(base, year, "standard")
            + run_calc_var(base, year, "c04470")
            + run_calc_var(base, year, "qbided")
        )
        cur_taxable_inc = run_calc_var(base, year, "c04800")
        cur_tot_inctax = run_calc_var(base, year, "c05800")
        cur_tot_cdt = run_calc_var(base, year, "c07100")
        cur_inctax_af_credit = run_calc_var(base, year, "c05800") - run_calc_var(
            base, year, "c07100"
        )
        new_salary_wage = run_calc_var(new, year, "e00200")
        new_taxable_interest_ordinary_divid = (
            run_calc_var(new, year, "e00300")
            + run_calc_var(new, year, "e00600")
            - run_calc_var(new, year, "e00650")
        )
        new_q_div = run_calc_var(new, year, "e00650")
        new_capital_g_l = (
            run_calc_var(new, year, "e01100")
            + run_calc_var(new, year, "e01200")
            + run_calc_var(new, year, "c23650")
        )
        new_business_inc = (
            run_calc_var(new, year, "e00900")
            + run_calc_var(new, year, "e02000")
            + run_calc_var(new, year, "e02100")
        )
        new_pension_annuities_IRAdis = run_calc_var(new, year, "e01400") + run_calc_var(
            new, year, "e01700"
        )
        new_ssb = run_calc_var(new, year, "c02500")
        new_total_inc = run_calc_var(new, year, "c00100") + run_calc_var(
            new, year, "c02900"
        )
        new_stat_adj = run_calc_var(new, year, "c02900")
        new_total_agi = run_calc_var(new, year, "c00100")
        new_other_inc = (
            new_total_inc
            - new_salary_wage
            - new_taxable_interest_ordinary_divid
            - new_capital_g_l
            - new_pension_annuities_IRAdis
            - new_ssb
        )
        new_sub_personal_expt = run_calc_var(new, year, "c04600")
        new_sub_std = run_calc_var(new, year, "standard")
        new_sub_tot_item = run_calc_var(new, year, "c04470")
        new_sub_qbid = run_calc_var(new, year, "qbided")
        new_sub_tot_expt = (
            run_calc_var(new, year, "c04600")
            + run_calc_var(new, year, "standard")
            + run_calc_var(new, year, "c04470")
            + run_calc_var(new, year, "qbided")
        )
        new_taxable_inc = run_calc_var(new, year, "c04800")
        new_tot_inctax = run_calc_var(new, year, "c05800")
        new_tot_cdt = run_calc_var(new, year, "c07100")
        new_inctax_af_credit = run_calc_var(new, year, "c05800") - run_calc_var(
            new, year, "c07100"
        )
        aggs["Tax Liability"].append(base_aggs["payrolltax"])
        aggs["Tax"].append("Current Payroll")
        aggs["Year"].append(year)
        aggs["Tax Liability"].append(new_aggs["payrolltax"])
        aggs["Tax"].append("New Payroll")
        aggs["Year"].append(year)
        aggs["Tax Liability"].append(base_aggs["iitax"])
        aggs["Tax"].append("Current Income")
        aggs["Year"].append(year)
        aggs["Tax Liability"].append(new_aggs["iitax"])
        aggs["Tax"].append("New Income")
        aggs["Year"].append(year)
        aggs["Tax Liability"].append(base_aggs["combined"])
        aggs["Tax"].append("Current Combined")
        aggs["Year"].append(year)
        aggs["Tax Liability"].append(new_aggs["combined"])
        aggs["Tax"].append("New Combined")
        aggs["Year"].append(year)

        agi_list = [
            cur_salary_wage,
            new_salary_wage,
            cur_taxable_interest_ordinary_divid,
            new_taxable_interest_ordinary_divid,
            cur_q_div,
            new_q_div,
            cur_capital_g_l,
            new_capital_g_l,
            cur_business_inc,
            new_business_inc,
            cur_pension_annuities_IRAdis,
            new_pension_annuities_IRAdis,
            cur_ssb,
            new_ssb,
            cur_other_inc,
            new_other_inc,
            cur_total_inc,
            new_total_inc,
            cur_stat_adj,
            new_stat_adj,
            cur_total_agi,
            new_total_agi,
            cur_sub_personal_expt,
            new_sub_personal_expt,
            cur_sub_std,
            new_sub_std,
            cur_sub_tot_item,
            new_sub_tot_item,
            cur_sub_qbid,
            new_sub_qbid,
            cur_sub_tot_expt,
            new_sub_tot_expt,
            cur_taxable_inc,
            new_taxable_inc,
            cur_tot_inctax,
            new_tot_inctax,
            cur_tot_cdt,
            new_tot_cdt,
            cur_inctax_af_credit,
            new_inctax_af_credit,
        ]
        agi_nlist = [
            "Current Salaries",
            "New Salaries",
            "Current Interests",
            "New Interests",
            "Current Qdividends",
            "New Qdividends",
            "Current Capital",
            "New Capital",
            "Current Business",
            "New Business",
            "Current Pensions",
            "New Pensions",
            "Current Security",
            "New Security",
            "Current Other",
            "New Other",
            "Current Totalincome",
            "New Totalincome",
            "Current Statutory",
            "New Statutory",
            "Current AGI",
            "New AGI",
            "Current Pexpt",
            "New Pexpt",
            "Current Standardded",
            "New Standardded",
            "Current totitem",
            "New totitem",
            "Current qbid",
            "New qbid",
            "Current totalexpt",
            "New totalexpt",
            "Current taxincome",
            "New taxincome",
            "Current totalinctax",
            "New totalinctax",
            "Current totalcredit",
            "New totalcredit",
            "Current aftercdttax",
            "New aftercdttax",
        ]
        for ae, an in zip(agi_list, agi_nlist):
            aggs2["Value"].append(ae)
            aggs2["Category"].append(an)
            aggs2["Year"].append(year)

        base_agi_aggs = calculate_agi_share(base, year)
        new_agi_aggs = calculate_agi_share(new, year)
        share_list = [
            base_agi_aggs[0],
            new_agi_aggs[0],
            base_agi_aggs[1],
            new_agi_aggs[1],
            base_agi_aggs[2],
            new_agi_aggs[2],
            base_agi_aggs[3],
            new_agi_aggs[3],
            base_agi_aggs[4],
            new_agi_aggs[4],
        ]
        share_nlist = [
            "Current Top1p",
            "New Top1p",
            "Current Top5p",
            "New Top5p",
            "Current Top10p",
            "New Top10p",
            "Current Top25p",
            "New Top25p",
            "Current Top50p",
            "New Top50p",
        ]

        for se, sn in zip(share_list, share_nlist):
            aggs3["Shares of AGI"].append(se)
            aggs3["Incomegroup"].append(sn)
            aggs3["Year"].append(year)

    agg_df = pd.DataFrame(aggs)
    agg2_df = pd.DataFrame(aggs2)
    agg3_df = pd.DataFrame(aggs3)

    title = "Aggregate Tax Liability by Year"
    agg_chart = (
        alt.Chart(agg_df, title=title)
        .mark_line()
        .encode(
            x=alt.X(
                "Year:O",
                axis=alt.Axis(labelAngle=0, titleFontSize=20, labelFontSize=15),
            ),
            y=alt.Y(
                "Tax Liability",
                title="Tax Liability (Billions)",
                axis=alt.Axis(titleFontSize=20, labelFontSize=15),
            ),
            color=alt.Color(
                "Tax",
                legend=alt.Legend(symbolSize=150, labelFontSize=15, titleFontSize=20),
            ),
        )
        .properties(width=800, height=350)
        .configure_title(fontSize=24)
    )
    img_path = Path(CUR_PATH, f"{name}_agg_plot.png")
    agg_chart.save(str(img_path))
    plot_paths.append(img_path)
    template_args[f"{name}_agg_plot"] = f"![]({str(img_path)})" + "{.center}"

    # create tax liability and projection tables
    template_args[f"{name}_combined_table"] = agg_liability_table(agg_df, "Combined")
    template_args[f"{name}_payroll_table"] = agg_liability_table(agg_df, "Payroll")
    template_args[f"{name}_income_table"] = agg_liability_table(agg_df, "Income")

    agi_table_name_list = [
        f"{name}_salaries_and_wages_table",
        f"{name}_taxable_interest_and_ordinary_dividends_table",
        f"{name}_qualified_dividends_table",
        f"{name}_capital_table",
        f"{name}_business_table",
        f"{name}_pensions_annuities_IRA_distributions_table",
        f"{name}_Social_Security_benefits_table",
        f"{name}_all_other_income_table",
        f"{name}_total_income_table",
        f"{name}_statutory_Adjustments_table",
        f"{name}_total_AGI_table",
        f"{name}_sub_peronal_expt_table",
        f"{name}_sub_std_table",
        f"{name}_sub_tot_item_table",
        f"{name}_sub_qbid_table",
        f"{name}_sub_tot_expt_table",
        f"{name}_taxable_inc_table",
        f"{name}_tot_inctax_table",
        f"{name}_tot_cdt_table",
        f"{name}_inctax_af_credit_table",
    ]
    agi_keyword_list = [
        "Salaries",
        "Interests",
        "Qdividends",
        "Capital",
        "Business",
        "Pensions",
        "Security",
        "Other",
        "Totalincome",
        "Statutory",
        "AGI",
        "Pexpt",
        "Standardded",
        "totitem",
        "qbid",
        "totalexpt",
        "taxincome",
        "totalinctax",
        "totalcredit",
        "aftercdttax",
    ]
    for table_name, keyword in zip(agi_table_name_list, agi_keyword_list):
        template_args[table_name] = projection_table(agg2_df, keyword)

    share_table_name_list = [
        f"{name}_Top1_percent_income_group_shares_of_AGI_table",
        f"{name}_Top5_percent_income_group_shares_of_AGI_table",
        f"{name}_Top10_percent_income_group_shares_of_AGI_table",
        f"{name}_Top25_percent_income_group_shares_of_AGI_table",
        f"{name}_Top50_percent_income_group_shares_of_AGI_table",
    ]
    share_keyword_list = ["Top1p", "Top5p", "Top10p", "Top25p", "Top50p"]
    for table_name, keyword in zip(share_table_name_list, share_keyword_list):
        template_args[table_name] = agi_share_table(agg3_df, keyword)

    return template_args, plot_paths


def CBO_validation(cbo_df, new, name, template_args):
    """
    Function for comparing the results from tax-calculator using the old and
    new data

    Parameters
    ----------
    new : Calculator object
        Tax-Calculator object using the new data
    name : str
        string name for which dataset is being compared. Must be `puf` or `cps`
    """
    if name not in ["puf", "cps"]:
        raise ValueError(f"{name} is not valid. Must be `puf` or `cps`.")
    calcs = [new]
    calc_labels = [f"New {name.upper()}"]

    # Tax Data projections
    aggs2 = defaultdict(list)
    aggs3 = defaultdict(list)
    var_list = ["payrolltax", "iitax", "combined", "standard", "c04470"]

    for year in range(new.current_year, tc.Policy.LAST_BUDGET_YEAR + 1):
        new_salary_wage = run_calc_var(new, year, "e00200")
        new_taxable_interest_ordinary_divid = (
            run_calc_var(new, year, "e00300")
            + run_calc_var(new, year, "e00600")
            - run_calc_var(new, year, "e00650")
        )
        new_q_div = run_calc_var(new, year, "e00650")
        new_capital_g_l = (
            run_calc_var(new, year, "e01100")
            + run_calc_var(new, year, "e01200")
            + run_calc_var(new, year, "c23650")
        )
        new_business_inc = (
            run_calc_var(new, year, "e00900")
            + run_calc_var(new, year, "e02000")
            + run_calc_var(new, year, "e02100")
        )
        new_pension_annuities_IRAdis = run_calc_var(new, year, "e01400") + run_calc_var(
            new, year, "e01700"
        )
        new_ssb = run_calc_var(new, year, "c02500")
        new_total_inc = run_calc_var(new, year, "c00100") + run_calc_var(
            new, year, "c02900"
        )
        new_stat_adj = run_calc_var(new, year, "c02900")
        new_total_agi = run_calc_var(new, year, "c00100")
        new_other_inc = (
            new_total_inc
            - new_salary_wage
            - new_taxable_interest_ordinary_divid
            - new_capital_g_l
            - new_pension_annuities_IRAdis
            - new_ssb
        )
        new_sub_personal_expt = run_calc_var(new, year, "c04600")
        new_sub_std = run_calc_var(new, year, "standard")
        new_sub_tot_item = run_calc_var(new, year, "c04470")
        new_sub_qbid = run_calc_var(new, year, "qbided")
        new_sub_tot_expt = (
            run_calc_var(new, year, "c04600")
            + run_calc_var(new, year, "standard")
            + run_calc_var(new, year, "c04470")
            + run_calc_var(new, year, "qbided")
        )
        new_taxable_inc = run_calc_var(new, year, "c04800")
        new_tot_inctax = run_calc_var(new, year, "c05800")
        new_tot_cdt = run_calc_var(new, year, "c07100") + run_calc_var(
            new, year, "refund"
        )
        new_inctax_af_credit = run_calc_var(new, year, "c05800") - run_calc_var(
            new, year, "c07100"
        )

        agi_list = [
            new_salary_wage,
            new_taxable_interest_ordinary_divid,
            new_q_div,
            new_capital_g_l,
            new_business_inc,
            new_pension_annuities_IRAdis,
            new_ssb,
            new_other_inc,
            new_total_inc,
            new_stat_adj,
            new_total_agi,
            new_sub_personal_expt,
            new_sub_std,
            new_sub_tot_item,
            new_sub_qbid,
            new_sub_tot_expt,
            new_taxable_inc,
            new_tot_inctax,
            new_tot_cdt,
            new_inctax_af_credit,
        ]
        agi_nlist = [
            "New Salaries",
            "New Interests",
            "New Qdividends",
            "New Capital",
            "New Business",
            "New Pensions",
            "New Security",
            "New Other",
            "New Totalincome",
            "New Statutory",
            "New AGI",
            "New Pexpt",
            "New Standardded",
            "New totitem",
            "New qbid",
            "New totalexpt",
            "New taxincome",
            "New totalinctax",
            "New totalcredit",
            "New aftercdttax",
        ]
        for ae, an in zip(agi_list, agi_nlist):
            aggs2["Value"].append(ae)
            aggs2["Category"].append(an)
            aggs2["Year"].append(year)

        new_agi_aggs = calculate_agi_share(new, year)
        share_list = [
            new_agi_aggs[0],
            new_agi_aggs[1],
            new_agi_aggs[2],
            new_agi_aggs[3],
            new_agi_aggs[4],
        ]
        share_nlist = [
            "New Top1p",
            "New Top5p",
            "New Top10p",
            "New Top25p",
            "New Top50p",
        ]

        for se, sn in zip(share_list, share_nlist):
            aggs3["Shares of AGI"].append(se)
            aggs3["Category"].append(sn)
            aggs3["Year"].append(year)

    agg2_df = pd.DataFrame(aggs2)
    agg3_df = pd.DataFrame(aggs3)

    # create validation tables
    agival_table_name_list = [
        f"{name}_validation_salaries_and_wages_table",
        f"{name}_validation_taxable_interest_and_ordinary_dividends_table",
        f"{name}_validation_qualified_dividends_table",
        f"{name}_validation_capital_table",
        f"{name}_validation_business_table",
        f"{name}_validation_pensions_annuities_IRA_distributions_table",
        f"{name}_validation_Social_Security_benefits_table",
        f"{name}_validation_all_other_income_table",
        f"{name}_validation_total_income_table",
        f"{name}_validation_statutory_Adjustments_table",
        f"{name}_validation_total_AGI_table",
        f"{name}_validation_sub_peronal_expt_table",
        f"{name}_validation_sub_std_table",
        f"{name}_validation_sub_tot_item_table",
        f"{name}_validation_sub_qbid_table",
        f"{name}_validation_sub_tot_expt_table",
        f"{name}_validation_taxable_inc_table",
        f"{name}_validation_tot_inctax_table",
        f"{name}_validation_tot_cdt_table",
        f"{name}_validation_inctax_af_credit_table",
    ]
    agi_keyword_list = [
        "Salaries",
        "Interests",
        "Qdividends",
        "Capital",
        "Business",
        "Pensions",
        "Security",
        "Other",
        "Totalincome",
        "Statutory",
        "AGI",
        "Pexpt",
        "Standardded",
        "totitem",
        "qbid",
        "totalexpt",
        "taxincome",
        "totalinctax",
        "totalcredit",
        "aftercdttax",
    ]

    for table_name, keyword in zip(agival_table_name_list, agi_keyword_list):
        template_args[table_name] = validation_table(agg2_df, cbo_df, keyword)

    shareval_table_name_list = [
        f"{name}_validation_Top1_percent_income_group_shares_of_AGI_table",
        f"{name}_validation_Top5_percent_income_group_shares_of_AGI_table",
        f"{name}_validation_Top10_percent_income_group_shares_of_AGI_table",
        f"{name}_validation_Top25_percent_income_group_shares_of_AGI_table",
        f"{name}_validation_Top50_percent_income_group_shares_of_AGI_table",
    ]
    share_keyword_list = ["Top1p", "Top5p", "Top10p", "Top25p", "Top50p"]
    for table_name, keyword in zip(shareval_table_name_list, share_keyword_list):
        template_args[table_name] = validation_table(agg3_df, cbo_df, keyword)

    return template_args
