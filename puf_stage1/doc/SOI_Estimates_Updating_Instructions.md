# Updating the SOI Estimates

This document provides instructions for updating `SOI_estimates.csv` in the
`puf_stage1` and `cps_stage1` directories. Updating the SOI estimates will also
require you to update `stage1.py` in both directories.

All of the data used comes from the
[SOI Tax Stats - Individual Statistical Tables by Size of Adjusted Gross Income](https://www.irs.gov/statistics/soi-tax-stats-individual-statistical-tables-by-size-of-adjusted-gross-income)
and updates should occur every time new data is released.

Each table bellow contains the row variables found in the `SOI_estimates.csv`
files, a brief description, the SOI table where that data can be found, and the
table column from which the data is pulled. To update the two files, use both
tables to find the relevant information and insert it as a new column in the
associated file.

## PUF

| Row Variable | Description                                                            | Table | Table Column Name                                                                                                         |
|--------------|------------------------------------------------------------------------|-------|---------------------------------------------------------------------------------------------------------------------------|
| Single       | Number of single filers                                                | 1.2   | Returns of single persons - Number of returns                                                                             |
| Joint        | Number of joint filers                                                 | 1.2   | Sum of the number of returns for married persons filing jointly and surviving spouses, married persons filing separately |
| HH           | Number of head of household filers                                     | 1.2   | Returns of head of households - Number of returns                                                                         |
| SS_return    | Number of returns with Social Security income                          | 1.4   | Social security benefits - Total - Number of returns                                                                               |
| Dep_return   | Number of dependent exemptions                                         | 2.3   | Exemptions for dependents - Number of exemptions                                                                          |
| INTS         | Taxable Interest Income                                                | 1.4   | Taxable interest - Amount                                                                                                 |
| DIVS         | Ordinary dividends                                                     | 1.4   | Ordinary Dividends - Amount                                                                                              |
| SCHCI        | Business Income (Schedule C)                                           | 1.4   | Business or profession - Net income                                                                                       |
| SCHCL        | Business Loss (Schedule C)                                             | 1.4   | Business or profession - Net loss                                                                                         |
| CGNS         | Net Capital Gains in AGI                                               | 1.4   | Sales of capital assets reported on Form 1040, Schedule D [2] - Taxable net gain - Amount                                 |
| Pension      | Taxable Pensions and Annuities                                         | 1.4   | Pensions and annuities - Taxable - Amount                                                                                 |
| SCHEI        | Supplemental Income (Schedule E)                                       | 1.4   | Sum of the net income amount for Total rent and royalty, Partnership and S corporation, and Estate and trust              |
| SCHEL        | Supplemental Loss (Schedule E)                                         | 1.4   | Sum of the net loss amount for Total rent and royalty, Partnership and S corporation, and Estate and trust                |
| SS           | Gross Social Security Income                                          | 1.4   | Social security benefits - Total - Amount                                                                                 |
| UCOMP        | Unemployment Compensation                                              | 1.4   | Unemployment compensation - Amount                                                                                        |
| IPD          | Interest Paid Deduction                                                | 2.1   | Itemized Deductions - Interest paid - Total - Amount                                                                      |
| WAGE_1       | Wages and Salaries for AGI Less than Zero                              | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_2       | Wages and Salaries for AGI greater than $1 and less than $10K            | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_3       | Wages and Salaries for AGI greater than $10K and less than $20K        | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_4       | Wages and Salaries for AGI greater than $20K and less than $30K        | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_5       | Wages and Salaries for AGI greater than $30K and less than $40K        | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_6       | Wages and Salaries for AGI greater than $40K and less than $50K        | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_7       | Wages and Salaries for AGI greater than $50K and less than $75K        | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_8       | Wages and Salaries for AGI greater than $75K and less than $100K       | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_9       | Wages and Salaries for AGI greater than $100K and less than $200K      | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_10      | Wages and Salaries for AGI greater than $200K and less than $500K      | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_11      | Wages and Salaries for AGI greater than $500K and less than $1 million | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| WAGE_12      | Wages and Salaries for AGI greater than $1 million                     | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |

## CPS

| Row Variable | Description                                                      | Table | Table Column Name                                                                                                         |
|--------------|------------------------------------------------------------------|-------|---------------------------------------------------------------------------------------------------------------------------|
| Single       | Number of single filers                                          | 1.2   | Returns of single persons - Number of returns                                                                             |
| Joint        | Number of joint filers                                           | 1.2   | Sum of the number of returns for married persons filing jointly, married persons filing separately, and surviving spouses |
| HH           | Number of head of household filers                               | 1.2   | Returns of head of households - Number of returns                                                                         |
| SS_return    | Number of returns with Social Security income                    | 1.4   | Social security benefits - Number of returns                                                                               |
| Dep_return   | Number of dependent exemptions                                   | 2.3   | Exemptions for dependents - Number of exemptions                                                                         |
| INTS         | Taxable Interest Income                                          | 1.4   | Taxable interest - Amount                                                                                                 |
| DIVS         | Ordinary dividends                                               | 1.4   | Ordinary Dividends - Amount                                                                                              |
| SCHCI        | Business Income (Schedule C)                                     | 1.4   | Business or profession - Net income                                                                                       |
| SCHCL        | Business Loss (Schedule C)                                       | 1.4   | Business or profession - Net loss                                                                                         |
| CGNS         | Net Capital Gains in AGI                                         | 1.4   | Sales of capital assets reported on Form 1040, Schedule D [2] - Taxable net gain - Amount                                 |
| Pension      | Taxable Pensions and Annuities                                   | 1.4   | Pensions and annuities - Taxable - Amount                                                                                 |
| SCHEI        | Supplemental Income (Schedule E)                                 | 1.4   | Sum of the net income amount for Total rent and royalty, Partnership and S corporation, and Estate and trust              |
| SCHEL        | Supplemental Loss (Schedule E)                                   | 1.4   | Sum of the net loss amount for Total rent and royalty, Partnership and S corporation, and Estate and trust                |
| SS           | Gross Social Security Income                                    | 1.4   | Social security benefits - Total - Amount                                                                                 |
| UCOMP        | Unemployment Compensation                                        | 1.4   | Unemployment compensation - Amount                                                                                        |
| wage1        | Wages and Salaries for AGI less that $10K                        | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| wage2        | Wages and Salaries for AGI greater than $10K and less than $20K  | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| wage3        | Wages and Salaries for AGI greater than $20K and less than $30K  | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| wage4        | Wages and Salaries for AGI greater than $30K and less than $40K  | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| wage5        | Wages and Salaries for AGI greater than $40K and less than $50K  | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| wage6        | Wages and Salaries for AGI greater than $50K and less than $75K  | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| wage7        | Wages and Salaries for AGI greater than $75K and less than $100K | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |
| wage8        | Wages and Salaries for AGI greater than $100K                     | 1.4   | Sum of Salaries and wages - Amount for specified AGI group                                                                |

## Changes Required in `stage1.py`

### PUF

The only change needed in `puf_stage1/stage1.py` is to update the
`SOI_YR` variable to match the year of the new SOI estimates.

### CPS

The only change needed in `cps_stage1/stage1.py` is to update `SYR` to match the
year of the new SOI estimates.

## Adding a new target

If you are adding a new target to the list in `SOI_estimates`, be sure to
backfill its values for all years in the file.

### Changes required to `stage1.py`

- Add the new target to the list of targets calculated in the `for` loop that extrapolated the SOI estimates
- Add the new target to the `current_year` DataFrame.

### Changes to `solve_lp_for_year.py`

These instructions apply to both the CPS and PUF stage 2 scripts.

- Add code to calculate the target like all other targets currently estimated
- Add the target to the `One_half_LHS` and `temp` lists