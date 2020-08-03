"""
Utility functions used by report.py
"""
import pypandoc
import pandas as pd
import numpy as np
import altair as alt
from jinja2 import Template


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


def add_bins(dframe, income_measure, num_bins, wt='s006',
             decile_details=False,
             weight_by_income_measure=False,):
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
        msg = 'decile_details is True when num_quantiles is {}'
        raise ValueError(msg.format(num_bins))
    dframe.sort_values(by=income_measure, inplace=True)
    if weight_by_income_measure:
        dframe['cumsum_temp'] = np.cumsum(
            np.multiply(dframe[income_measure].values, dframe[wt].values)
        )
        min_cumsum = dframe['cumsum_temp'].values[0]
    else:
        dframe['cumsum_temp'] = np.cumsum(dframe[wt].values)
        min_cumsum = 0.  # because s006 values are non-negative
    max_cumsum = dframe['cumsum_temp'].values[-1]
    cumsum_range = max_cumsum - min_cumsum
    bin_width = cumsum_range / float(num_bins)
    bin_edges = list(min_cumsum +
                     np.arange(0, (num_bins + 1)) * bin_width)
    bin_edges[-1] = 9e99  # raise top of last bin to include all observations
    bin_edges[0] = -9e99  # lower bottom of 1st bin to include all observations
    if decile_details:
        assert bin_edges[1] > 1e-9  # bin_edges[1] is top of bottom decile
        bin_edges.insert(1, 1e-9)  # top of zeros
        bin_edges.insert(1, -1e-9)  # top of negatives
        bin_edges.insert(-1, bin_edges[-2] + 0.5 * bin_width)  # top of 90-95
        bin_edges.insert(-1, bin_edges[-2] + 0.4 * bin_width)  # top of 95-99
        num_bins += 4
    labels = range(1, (num_bins + 1))
    dframe['bins'] = pd.cut(dframe['cumsum_temp'], bin_edges,
                            right=False, labels=labels)
    dframe.drop('cumsum_temp', axis=1, inplace=True)
    return dframe


def weighted_mean(pdf, col_name, wt_name='s006'):
    """
    Return weighted mean of col_name

    Parameters
    ----------
    pdf: Pandas DataFrame object
    col_name: variable to be averaged
    wt_name: weight
    """
    return (float((pdf[col_name] * pdf[wt_name]).sum()) /
            float(pdf[wt_name].sum() + EPSILON))


def weighted_sum(pdf, col_name, wt_name='s006'):
    """
    Return weighted sum of col_name

    Parameters
    ----------
    pdf: Pandas DataFrame object
    col_name: variable to be averaged
    wt_name: weight
    """
    return (float((pdf[col_name] * pdf[wt_name]).sum()))


def percentile(pdf, col_name, num_bins, income_measure,
               wt='s006', income_wt=False,
               result_type='avg',
               decile_details=False):
    """
    """
    qpdf = add_bins(pdf, income_measure=income_measure, num_bins=num_bins,
                    wt=wt, decile_details=decile_details,
                    weight_by_income_measure=income_wt)
    gpdf = qpdf.groupby('bins', as_index=False)
    if result_type == 'avg':
        wpdf = gpdf.apply(weighted_mean, col_name)
    elif result_type == 'sum':
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
    agi_1 = ((item[agi < 0] * weight[agi < 0]).sum())
    pct1 = round(agi_1 / total, 2)
    agi_2 = ((item[(agi > 1) & (agi < 5000)] *
              weight[(agi > 1) & (agi < 5000)]).sum())
    pct2 = round(agi_1 / total, 2)
    agi_3 = ((item[(agi > 5000) & (agi < 10000)] *
              weight[(agi > 5000) & (agi < 10000)]).sum())
    pct3 = round(agi_3 / total, 2)
    agi_4 = ((item[(agi > 10000) & (agi < 15000)] *
              weight[(agi > 10000) & (agi < 15000)]).sum())
    pct4 = round(agi_4 / total, 2)
    agi_5 = ((item[(agi > 15000) & (agi < 20000)] *
              weight[(agi > 15000) & (agi < 20000)]).sum())
    pct5 = round(agi_5 / total, 2)
    agi_6 = ((item[(agi > 20000) & (agi < 25000)] *
              weight[(agi > 20000) & (agi < 25000)]).sum())
    pct6 = round(agi_6 / total, 2)
    agi_7 = ((item[(agi > 25000) & (agi < 30000)] *
              weight[(agi > 25000) & (agi < 30000)]).sum())
    pct7 = round(agi_7 / total, 2)
    agi_8 = ((item[(agi > 30000) & (agi < 40000)] *
              weight[(agi > 30000) & (agi < 40000)]).sum())
    pct8 = round(agi_8 / total, 2)
    agi_9 = ((item[(agi > 40000) & (agi < 50000)] *
              weight[(agi > 40000) & (agi < 50000)]).sum())
    pct9 = round(agi_9 / total, 2)
    agi_10 = ((item[(agi > 50000) & (agi < 75000)] *
               weight[(agi > 50000) & (agi < 75000)]).sum())
    pct10 = round(agi_10 / total, 2)
    agi_11 = ((item[(agi > 75000) & (agi < 100000)] *
               weight[(agi > 75000) & (agi < 100000)]).sum())
    pct11 = round(agi_11 / total, 2)
    agi_12 = ((item[(agi > 100000) & (agi < 200000)] *
               weight[(agi > 100000) & (agi < 200000)]).sum())
    pct12 = round(agi_12 / total, 2)
    agi_13 = ((item[(agi > 200000) & (agi < 500000)] *
               weight[(agi > 200000) & (agi < 500000)]).sum())
    pct13 = round(agi_13 / total, 2)
    agi_14 = ((item[(agi > 500000) & (agi < 1000000)] *
               weight[(agi > 500000) & (agi < 1000000)]).sum())
    pct14 = round(agi_14 / total, 2)
    agi_15 = ((item[(agi > 1000000) & (agi < 1500000)] *
               weight[(agi > 1000000) & (agi < 1500000)]).sum())
    pct15 = round(agi_15 / total, 2)
    agi_16 = ((item[(agi > 1500000) & (agi < 2000000)] *
               weight[(agi > 1500000) & (agi < 2000000)]).sum())
    pct16 = round(agi_16 / total, 2)
    agi_17 = ((item[(agi > 2000000) & (agi < 5000000)] *
               weight[(agi > 2000000) & (agi < 5000000)]).sum())
    pct17 = round(agi_17 / total, 2)
    agi_18 = ((item[(agi > 5000000) & (agi < 10000000)] *
               weight[(agi > 5000000) & (agi < 10000000)]).sum())
    pct18 = round(agi_18 / total, 2)
    agi_19 = (item[agi > 10000000] * weight[agi > 10000000]).sum()
    pct19 = round(agi_19 / total, 2)
    df = [agi_1, agi_2, agi_3, agi_4, agi_5, agi_6, agi_7, agi_8, agi_9,
          agi_10, agi_11, agi_12, agi_13, agi_14, agi_15, agi_16, agi_17,
          agi_18, agi_19]
    pct = [pct1, pct2, pct3, pct4, pct5, pct6, pct7, pct8, pct9, pct10, pct11,
           pct12, pct13, pct14, pct15, pct16, pct17, pct18, pct19]
    index = ['Zero or Negative', '$1-$5K', '$5K-$10K', '$10K-$15K',
             '$15K-$20K', '$20K-$25K', '$25K-$30K', '$30K-$40K',
             '$40K-$50K', '$50K-$75K', '$75K-$100K', '$100K-$200K',
             '$200K-$500K', '$500K-$1M', '$1M-$1.5M', '$1.5M-$2M',
             '$2M-$5M', '$5M-$10M', '$10M and over']
    return df, pct, index


def distplot(calcs: list, calc_labels: list, var: str,
             income_measure: str = 'expanded_income',
             result_type: str = 'pct', width=800, height=350, title=""):
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
            calc.array(var), calc.array('s006'), calc.array(income_measure)
        )
        return agg, pct, index
    assert result_type in ['pct', 'sum']
    pltdata = pd.DataFrame()
    for (calc, label) in zip(calcs, calc_labels):
        agg, pct, index = getdata(calc, var, income_measure)
        if result_type == 'pct':
            pltdata[label] = pct
        else:
            pltdata[label] = [_ * 1e-9 for _ in agg]
    pltdata['index'] = index
    melted = pd.melt(pltdata, id_vars='index')
    if result_type == 'pct':
        y_label = 'Percent of Total'
        y_format = "%"
    else:
        y_label = 'Total (billions)'
        y_format = '$.3f'
    plt = alt.Chart(
        melted, title=title
    ).mark_circle(size=50).encode(
        alt.X(
            'index:O', sort=index,
            axis=alt.Axis(
                title="Expanded Income Bin", labelAngle=-90,
                labelFontSize=15, titleFontSize=20
            )
            ),
        alt.Y(
            'value',
            axis=alt.Axis(
                format=y_format, title=y_label, labelFontSize=15,
                titleFontSize=20
            )
            ),
        color=alt.Color(
            'variable',
            legend=alt.Legend(
                title="File", symbolSize=150, labelFontSize=15,
                titleFontSize=20,
            )
        )
    ).properties(
        width=width,
        height=height
    ).configure_title(
        fontSize=24
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
        rendered, "pdf", format="md", outputfile=str(pathout),
        extra_args=[
            '-V', 'geometry:margin=1in'
        ]
    )


def cbo_bar_chart(cbo_data, var, title, bar_width=30,
                  width=600, height=250):
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
    chart = alt.Chart(cbo_data, title=title).mark_bar(width=bar_width).encode(
        x=alt.X(
            "Projections",
            axis=alt.Axis(
                title=None, labels=False, ticks=False, labelFontSize=15
            )
        ),
        y=alt.Y(
            var, axis=alt.Axis(labelFontSize=10, titleFontSize=15)
        ),
        color=alt.Color("Projections"),
        column=alt.Column(
            "index", header=alt.Header(title=None, labelOrient="bottom")
        )
    ).properties(height=height, width=_width).configure_view(
        stroke="transparent"
    ).configure_facet(
        spacing=0
    ).configure_title(
        fontSize=20
    )
    return chart


def compare_vars(cur_meta, new_meta, file):
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

    if file not in ["puf", "cps"]:
        msg = "'file' must be either 'cps' or 'puf'"
        raise ValueError(msg)
    _file = f"taxdata_{file}"
    cur_avail = set(
        cur_meta[cur_meta["availability"].str.contains(_file)].index
    )
    new_avail = set(
        new_meta[cur_meta["availability"].str.contains(_file)].index
    )
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


def growth_scatter_plot(data, rows, point_size=150, width=600,
                        height=300, columns=2):
    """
    Create a scatter plot to show changes in growth factors
    Parameters
    ----------
    data: growth factor data
    factor: factor we"re plotting
    """
    max_val = data.max().drop(index=["YEAR", "Growth Factors"]).max()
    min_val = data.min().drop(index=["YEAR", "Growth Factors"]).min()
    chart = alt.Chart(data).mark_circle(size=point_size, filled=True).encode(
        x=alt.X(
            "YEAR", type="ordinal",
            axis=alt.Axis(labelAngle=-45, labelFontSize=25, titleFontSize=30)
        ),
        y=alt.Y(
            alt.repeat(), type="quantitative",
            scale=alt.Scale(domain=[min_val, max_val]),
            axis=alt.Axis(labelFontSize=25, titleFontSize=30)
        ),
        color=alt.Color(
            "Growth Factors", legend=alt.Legend(
                symbolSize=300, labelFontSize=20, titleFontSize=25,
                direction="horizontal", orient="top"
            )
        )
    ).properties(
        width=width,
        height=height
    ).repeat(
        rows, columns=columns
    ).configure_legend(
        labelLimit=0, titleLimit=0
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
    diff = final_df.loc["Current"] - final_df.loc["New"]
    final_df.loc["Change"] = diff.round(1)
    pct_change = diff / final_df.loc["Current"] * 100
    final_df.loc["Pct Change"] = pct_change.round(2)
    return final_df.to_markdown()
