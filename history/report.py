"""
Script used to automatically generate PDF report comparing TaxData outputs
after updates
"""
# flake8: noqa: E501
import argparse
import pandas as pd
import taxcalc as tc
import altair as alt
from report_utils import (
    run_calc,
    distplot,
    write_page,
    growth_scatter_plot,
    compare_vars,
    cbo_bar_chart,
    agg_liability_table,
    compare_calcs,
)
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from requests_html import HTMLSession

CUR_PATH = Path(__file__).resolve().parent
STAGE1_PATH = Path(CUR_PATH, "..", "puf_stage1")
CBO_PATH = Path(STAGE1_PATH, "CBO_baseline.csv")
SOI_PATH = Path(STAGE1_PATH, "SOI_estimates.csv")
GROW_FACTORS_PATH = Path(STAGE1_PATH, "growfactors.csv")
META_PATH = Path(CUR_PATH, "..", "tests", "records_metadata.json")
CBO_URL = "https://raw.githubusercontent.com/PSLmodels/taxdata/master/puf_stage1/CBO_baseline.csv"
SOI_URL = "https://raw.githubusercontent.com/PSLmodels/taxdata/master/puf_stage1/SOI_estimates.csv"
META_URL = "https://raw.githubusercontent.com/PSLmodels/taxdata/master/tests/records_metadata.json"
GROW_FACTORS_URL = "https://raw.githubusercontent.com/PSLmodels/taxdata/master/puf_stage1/growfactors.csv"

PUF_PATH = Path(CUR_PATH, "..", "data", "puf.csv")
PUF_AVAILABLE = PUF_PATH.exists()

TEMPLATE_PATH = Path(CUR_PATH, "report_template.md")

CBO_LABELS = {
    "GDP": "GDP (Billions)",
    "TPY": "Personal Income (Billions)",
    "Wages": "Wages and Salaries (Billions)",
    "SCHC": "Proprietors Income, Non Farm with IVA & CCAdj (Billions)",
    "SCHF": "Proprietors Income, Farm with IVA & CCAdj (Billions)",
    "INTS": "Personal Interest Income (Billions)",
    "DIVS": "Personal Dividend Income (Billions)",
    "RENTS": "Rental Income with CCADJ (Billions)",
    "BOOK": "Corporate Profits with IVA & CCADJ (Billions)",
    "CPIU": "Consumer Pricing Index, All Urban Consumers (CPI-U) - 1982-84=100",
    "CGNS": "Capital Gains Realizations",
    "RETS": "IRS Projections of Individual Returns (Millions)",
    "SOCSEC": "Scheduled Social Security Benefits",
    "CPIM": "CPI Medical Care",
    "UCOMP": "Unemployment Compensation (Billions)",
}


def report():
    """
    Generate TaxData history report
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "prs",
        help=(
            "prs is a list of prs that were used for this report. "
            "Enter them as a string separated by commas"
        ),
        default="",
        type=str,
    )
    parser.add_argument(
        "--desc",
        help=(
            "File path to a text or markdown file with additonal information "
            "that will appear at the beginning of the report"
        ),
        default="",
        type=str,
    )
    parser.add_argument(
        "--basepuf",
        help=(
            "File path to the previous puf.csv file. Use when the proposed "
            "changes affect puf.csv"
        ),
    )
    args = parser.parse_args()
    desc = args.desc
    base_puf_path = args.basepuf
    if desc:
        desc = Path(args.desc).open("r").read()
    plot_paths = []
    date = datetime.today().date()
    template_args = {"date": date, "desc": desc}
    pull_str = "* [#{}: {}]({})"
    _prs = args.prs.split(",")
    session = HTMLSession()
    prs = []
    for pr in _prs:
        url = f"https://github.com/PSLmodels/taxdata/pull/{pr}"
        # extract PR title
        r = session.get(url)
        elm = r.html.find("span.js-issue-title")[0]
        title = elm.text
        prs.append(pull_str.format(pr, title, url))
    template_args["prs"] = prs
    # CBO projection comparisons
    cbo_projections = []
    cur_cbo = pd.read_csv(CBO_URL, index_col=0)
    new_cbo = pd.read_csv(CBO_PATH, index_col=0)
    cbo_years = new_cbo.columns.astype(int)
    last_year = cbo_years.max()
    first_year = last_year - 9
    if new_cbo.equals(cur_cbo):
        cbo_projections.append("No changes to CBO projections.")
    else:
        # we're only going to include the final ten years in our bar chart
        keep_years = [str(year) for year in range(first_year, last_year + 1)]
        cur_cbo = cur_cbo.filter(keep_years, axis=1).transpose().reset_index()
        cur_cbo["Projections"] = "Current"
        new_cbo = new_cbo.filter(keep_years, axis=1).transpose().reset_index()
        new_cbo["Projections"] = "New"
        cbo_data = pd.concat([cur_cbo, new_cbo], axis=0)
        for col in cbo_data.columns:
            if col == "index" or col == "Projections":
                continue
            chart = cbo_bar_chart(cbo_data, col, CBO_LABELS[col])
            img_path = Path(CUR_PATH, f"{col}.png")
            chart.save(str(img_path))
            plot_paths.append(img_path)
            cbo_projections.append(f"![]({str(img_path)})" + "{.center}")
    template_args["cbo_projections"] = cbo_projections

    # changes in data availability
    cur_meta = pd.read_json(META_URL, orient="index")
    new_meta = pd.read_json(META_PATH, orient="index")
    puf_added, puf_removed = compare_vars(cur_meta, new_meta, "puf")
    cps_added, cps_removed = compare_vars(cur_meta, new_meta, "cps")
    template_args["puf_added"] = puf_added
    template_args["puf_removed"] = puf_removed
    template_args["cps_added"] = cps_added
    template_args["cps_removed"] = cps_removed

    # growth rate changes
    growth_rate_projections = []
    cur_grow = pd.read_csv(GROW_FACTORS_URL)
    new_grow = pd.read_csv(GROW_FACTORS_PATH)
    if new_grow.equals(cur_grow):
        growth_rate_projections.append("No changes to growth rate projections")
    else:
        new_grow = new_grow[
            (new_grow["YEAR"] >= first_year) & (new_grow["YEAR"] <= last_year)
        ]
        cur_grow = cur_grow[
            (cur_grow["YEAR"] >= first_year) & (cur_grow["YEAR"] <= last_year)
        ]
        new_grow["Growth Factors"] = "New"
        cur_grow["Growth Factors"] = "Current"
        growth_data = pd.concat([new_grow, cur_grow])
        rows = list(growth_data.columns)
        rows.remove("YEAR"),
        rows.remove("Growth Factors")
        n = len(rows) // 3
        chart1 = growth_scatter_plot(growth_data, rows[:n])
        img_path = Path(CUR_PATH, "growth_factors1.png")
        chart1.save(str(img_path))
        plot_paths.append(img_path)
        growth_rate_projections.append(f"![]({str(img_path)})" + "{.center}")
        chart2 = growth_scatter_plot(growth_data, rows[n : 2 * n])
        img_path = Path(CUR_PATH, "growth_factors2.png")
        chart2.save(str(img_path))
        plot_paths.append(img_path)
        growth_rate_projections.append(f"![]({str(img_path)})" + "{.center}")
        chart3 = growth_scatter_plot(growth_data, rows[2 * n :])
        img_path = Path(CUR_PATH, "growth_factors3.png")
        chart3.save(str(img_path))
        plot_paths.append(img_path)
        growth_rate_projections.append(f"![]({str(img_path)})" + "{.center}")
    template_args["growth_rate_projections"] = growth_rate_projections

    # compare tax calculator projections
    # baseline CPS calculator
    base_cps = tc.Calculator(records=tc.Records.cps_constructor(), policy=tc.Policy())
    base_cps.advance_to_year(first_year)
    base_cps.calc_all()
    # updated CPS calculator
    cps = pd.read_csv(Path(CUR_PATH, "..", "data", "cps.csv.gz"), index_col=None)
    cps_weights = pd.read_csv(
        Path(CUR_PATH, "..", "cps_stage2", "cps_weights.csv.gz"), index_col=None
    )
    new_cps = tc.Calculator(
        records=tc.Records(
            data=cps, weights=cps_weights, adjust_ratios=None, start_year=2014
        ),
        policy=tc.Policy(),
    )
    new_cps.advance_to_year(first_year)
    new_cps.calc_all()
    template_args, plot_paths = compare_calcs(
        base_cps, new_cps, "cps", template_args, plot_paths
    )

    # PUF comparison
    if base_puf_path and PUF_AVAILABLE:
        template_args["puf_msg"] = None
        # base puf calculator
        base_puf = tc.Calculator(
            records=tc.Records(data=base_puf_path), policy=tc.Policy()
        )
        base_puf.advance_to_year(first_year)
        base_puf.calc_all()
        # updated puf calculator
        puf_weights = pd.read_csv(
            Path(CUR_PATH, "..", "puf_stage2", "puf_weights.csv.gz"), index_col=None
        )
        puf_ratios = pd.read_csv(
            Path(CUR_PATH, "..", "puf_stage3", "puf_ratios.csv"), index_col=0
        ).transpose()
        new_records = tc.Records(
            data=str(PUF_PATH), weights=puf_weights, adjust_ratios=puf_ratios
        )
        new_puf = tc.Calculator(records=new_records, policy=tc.Policy())
        new_puf.advance_to_year(first_year)
        new_puf.calc_all()
        template_args, plot_paths = compare_calcs(
            base_puf, new_puf, "puf", template_args, plot_paths
        )
    else:
        msg = "PUF comparisons are not included in this report."
        template_args["puf_msg"] = msg
        template_args["puf_agg_plot"] = None
        template_args["puf_combined_table"] = None
        template_args["puf_income_table"] = None
        template_args["puf_payroll_table"] = None

    # # distribution plots
    # dist_vars = [
    #     ("c00100", "AGI Distribution"),
    #     ("combined", "Tax Liability Distribution"),
    # ]
    # dist_plots = []
    # for var, title in dist_vars:
    #     plot = distplot(calcs, calc_labels, var, title=title)
    #     img_path = Path(CUR_PATH, f"{var}_dist.png")
    #     plot.save(str(img_path))
    #     plot_paths.append(img_path)
    #     dist_plots.append(f"![]({str(img_path)})" + "{.center}")
    # template_args["cps_dist_plots"] = dist_plots

    # # aggregate totals
    # aggs = defaultdict(list)
    # var_list = ["payrolltax", "iitax", "combined", "standard", "c04470"]
    # for year in range(first_year, tc.Policy.LAST_BUDGET_YEAR + 1):
    #     base_aggs = run_calc(base_cps, year, var_list)
    #     new_aggs = run_calc(new_cps, year, var_list)
    #     aggs["Tax Liability"].append(base_aggs["payrolltax"])
    #     aggs["Tax"].append("Current Payroll")
    #     aggs["Year"].append(year)
    #     aggs["Tax Liability"].append(new_aggs["payrolltax"])
    #     aggs["Tax"].append("New Payroll")
    #     aggs["Year"].append(year)
    #     aggs["Tax Liability"].append(base_aggs["iitax"])
    #     aggs["Tax"].append("Current Income")
    #     aggs["Year"].append(year)
    #     aggs["Tax Liability"].append(new_aggs["iitax"])
    #     aggs["Tax"].append("New Income")
    #     aggs["Year"].append(year)
    #     aggs["Tax Liability"].append(base_aggs["combined"])
    #     aggs["Tax"].append("Current Combined")
    #     aggs["Year"].append(year)
    #     aggs["Tax Liability"].append(new_aggs["combined"])
    #     aggs["Tax"].append("New Combined")
    #     aggs["Year"].append(year)
    # agg_df = pd.DataFrame(aggs)

    # title = "Aggregate Tax Liability by Year"
    # agg_chart = (
    #     alt.Chart(agg_df, title=title)
    #     .mark_line()
    #     .encode(
    #         x=alt.X(
    #             "Year:O",
    #             axis=alt.Axis(labelAngle=0, titleFontSize=20, labelFontSize=15),
    #         ),
    #         y=alt.Y(
    #             "Tax Liability",
    #             title="Tax Liability (Billions)",
    #             axis=alt.Axis(titleFontSize=20, labelFontSize=15),
    #         ),
    #         color=alt.Color(
    #             "Tax",
    #             legend=alt.Legend(symbolSize=150, labelFontSize=15, titleFontSize=20),
    #         ),
    #     )
    #     .properties(width=800, height=350)
    #     .configure_title(fontSize=24)
    # )
    # img_path = Path(CUR_PATH, "agg_plot.png")
    # agg_chart.save(str(img_path))
    # plot_paths.append(img_path)
    # template_args["agg_plot"] = f"![]({str(img_path)})" + "{.center}"

    # # create tax liability tables
    # template_args["combined_table"] = agg_liability_table(agg_df, "Combined")
    # template_args["payroll_table"] = agg_liability_table(agg_df, "Payroll")
    # template_args["income_table"] = agg_liability_table(agg_df, "Income")

    # write report and delete images used
    output_path = Path(CUR_PATH, "reports", f"taxdata_report_{date}.pdf")
    write_page(output_path, TEMPLATE_PATH, **template_args)
    for path in plot_paths:
        path.unlink()


if __name__ == "__main__":
    report()
