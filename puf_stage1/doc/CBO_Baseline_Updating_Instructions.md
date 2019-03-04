# Updating the CBO Baseline

This document provides instructions for updating the `CBO_baseline.csv` file
found in the Stage 1 folder.

Most of the projections can be found in the CBO's 10-year Economic Projections.
Those variables are listed under "Variables in the 10-Year CBO Projections."
Those that are not in that file are listed separately with instructions
on where/how to find/update them.

The year of the file/report the current numbers come from as well as the year
of the file/report used before the most recent update are listed for each
variable. These will needed to be updated with each update of `CBO_baseline.csv`.

Almost all of the updates to `CBO_baseline.csv` can be done by updating and
running `puf_stage1.py/updatecbo.py`. Instructions for how to update the file
can be found in the following sections:

1. [Variables in 10-Year CBO Projections](#Variables-in-10-Year-CBO-Projections)
2. [CGNS](#CGNS)
3. [CPIM (CPI Medical Care)](#CPIM-(CPI-Medical-Care))

The code in `puf_stage1.py/updatecbo.py` assumes that the format of the
spreadsheets provided by the CBO and the API provided by the BLS remain
unchanged. If the program throws an error or the results do not look correct,
it is likely that one of those assumptions is no longer true.

The only variables in `CBO_baseline.csv` that cannot be updated automatically
are `RETS`, `SOCSEC`, and `UCOMP`. Instructions for updating those manually
can be found below.

If the updates include projections for years that were not there previously,
`puf_stage1/stage1.py`, `cps_stage1/stage1.py`, `puf_stage2/stage2.py`, and
`cps_stage2/stage2.py` will also need to be updated. Instructions for doing so
are also included in this file.

## `CBO_baseline.csv`

This file contains all of the data used in our initial growth factors calculations.
Each row contains either a projected or actual value for the year associated
with that column. When updating the projections, update every year that
appears in the new file/report used.

## Variables in 10-Year CBO Projections

As previously mentioned, most of the variables we used can be found in the
[CBO 10-Year Economics Projections](https://www.cbo.gov/about/products/budget-economic-data#4).
To update these variables, replace the URL assigned to the `econ_url` variable
in `puf_stage1/updatecbo.py` with the link to the latest CBO economic projections
and run the file. Or you could download the file and copy/paste the specific
variables.

Previous Document: August 2016

Current Document: August 2018

| Variable | Name In CBO Document                                |
|----------|-----------------------------------------------------|
| GDP      | GDP                                                 |
| TPY      | Income, Personal                                    |
| Wages    | Wages and salaries                                  |
| SCHC     | Proprietors Income, Non Farm with IVA & CCAdj       |
| SCHF     | Proprietors Income, Farm with IVA & CCAdj           |
| INTS     | Interest Income, Personal                           |
| DIVS     | Dividend Income, Personal                           |
| RENTS    | Income, Rental, with CCAdj                          |
| BOOK     | Profits, Corporate with IVA & CCAdj                 |
| CPIU     | Consumer Pricing Index, All Urban Consumers (CPI-U) |

## Variables Not in 10-Year Projections

### CGNS

Source: [Revenue Projections, By Category (CBO)](https://www.cbo.gov/about/products/budget-economic-data#7)

Previous: January 2016

Current: April 2018

Notes: In the revenue projections file, the data is in the `Capital Gains Realizations`
tab under the `Capital Gains Realizations` column.

To update this variables, replace the URL assigned to the `cg_url` variable in
`puf_stage1/updatecbo.py` with the link to the most recent CBO revenue
projections and run the file. Or download the spreadsheet and manually update
the projections.

### RETS

Source: [IRS Publication 6187 Table 1B](https://www.irs.gov/statistics/projections-of-federal-tax-return-filings)

Previous: [Fall 2016 Update](https://www.irs.gov/pub/irs-pdf/p6187.pdf)

Current: [Fall 2018 Update](https://www.irs.gov/pub/irs-soi/Pub6187.pdf)

Notes: The projections in the publication typically end a few years before the
10-year projections do. We use the growth rate from the final year in the
projections to extrapolate into the additional years that are needed.

### SOCSEC

Source: [OASI Trust Fund Annual Trustees Report](https://www.ssa.gov/oact/TR/)

Table VI.C4. Operations of the OASI Trust Fund, Table VI.C4, Column:
`Scheduled Benefits: Intermediate Level`

Previous: [2016 Report](https://www.ssa.gov/oact/TR/2016/VI_C_SRfyproj.html#306103)

Current: [2018 Report](https://www.ssa.gov/oact/tr/2018/VI_C_SRfyproj.html#306103)

Notes: Projections are taken directly from this table.

### CPIM (CPI Medical Care)

Source: [BLS Database](http://data.bls.gov/timeseries/CUSR0000SAM?output_view=pct_1mth)

Series ID: CUSR0000SAM

Instructions:

1. From the above link, click on "More Formatting Options"
2. Under "Select view of the data," select "Original Data Value"
3. Click "Retrieve Data"
4. Download the table at the bottom of the page
5. Take the 12 month average for each year in the data
6. Find the average difference between CPI-U from the CBO 10-Year projections
7. Add this average difference to the CBO CPI-U projections

OR: Simply run `puf_stage1/updatecbo.py`, which will use the BLS provided API
to pull the latest data.

### UCOMP

Source: [CBO Unemployment Compensation projections](https://www.cbo.gov/about/products/baseline-projections-selected-programs#24)

Previous: [June 2017](https://www.cbo.gov/sites/default/files/recurringdata/51316-2017-06-unemployment.pdf)

Current: [April 2018](https://www.cbo.gov/system/files?file=2018-06/51316-2018-04-unemployment.pdf)

Note: Change the `Total Benefits` number from the table to be in terms of
billions rather than millions of dollars

## Adding a New Year to the Projections

If the updates you are making also add an additional year to the extrapolation,
you will need to make a few additional changes.

### Stage 1 Updates

In `puf_stage1/stage1.py` and `cps_stage1/stage1.py`, you need to increment
the `EYR` variable at the top of the file to reflect the new end year.

### Stage 2 Updates

In `puf_stage2/stage2.py` and `cps_stage2/stage2.py`, you need to create a new
column in the `z` and `weights` data frames, respectively, for the new year.
This will call the `solve_lp_for_year` function in the exact same way as the
previous years.