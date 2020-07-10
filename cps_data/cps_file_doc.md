# Current Population Survey Tax Unit File Documentation

Microsimulation models, such as
[Tax-Calculator](https://github.com/open-source-economics/Tax-Calculator),
rely on datasets comprised of individual tax units. These datasets are available
through the IRS, but at substantial financial cost and are not permitted to be
shared. This document outlines the creation of a tax unit dataset created from
publicly available CPS files that is suitable for use with Tax-Calculator.

## Overview

The Annual Social and Economic Supplement (ASEC) to the Current Population
Survey (CPS) is an annual survey of US households conducted in March of every
year. The file contains information on prior-year income and current family
structure that can be used to create tax units comprised of those surveyed. To
create our file, we use the 2013, 2014, and 2015 March CPS supplements, augmented
with transfer program data imputed by the CPS Transfer Augmentation Model (C-TAM).

## Tax Unit Creation

The CPS consists of records at household, family, and person levels. After
grouping indiviudals by household, we loop through each household to form tax
units. Starting with the reference person, we search the household for a
spouse or dependent that should be placed in that initial tax unit. If after
the first iteration there are individuals who were not determined to be part
of the first tax unit, we have them form their own and then search for their
spouse or dependents. This process is repeated until every individual in the
household has been assigned to a tax unit. Before moving to the next household,
we then check if any dependents should be dependent filers. All of the resulting
tax units will contain information on total income from wages, interest,
dividends, etc.; benefit program participation; and the composition of the unit.

## Splitting Income

Once the tax units have been created, we split total interest income into
taxable and tax exempt interest and dividend income into qualified and non-qualified
dividends.

## Imputations

To supplement the information contained in the CPS, we impute the following
variables:

* Capital Gains
* Taxable IRA Distributions
* Adjustable IRA payments
* KEOGH Plan contributions
* Self-Employed Health Insurance Deduction
* Student Loan Interest Payments
* Child and Dependent Care Credits
* Medical Expense Deduction
* Miscellaneous Itemized Deductions
* Charitable Giving
* Domestic Production Activity Deduction
* Mortgage Interest Payments

We use a two step process for these imputations. First, we use a logit model
to predict which households will have non-zero values. Second, we use a standard
OLS to predict the values for tax units determined to have a non-zero value.

## State Targeting

To ensure that our aggregate numbers line up with those reported by
the IRS, we derive factors to blow-up certain income and deduction
variables at the state level.<sup>1</sup> The state totals used to calculate the
factors can be found [here](https://www.irs.gov/statistics/soi-tax-stats-state-data-at-a-glance-fy-2014). The factors themselves
can be found in `cps_data/pycps/state_factors.csv`.

## Final Prep

The finishing touches put on the file are primarily cosmetic--renaming variables,
creating unique record IDs, and converting all floats to integers to make the
final file smaller.<sup>2</sup> The two more substinative changes made are to
apply caps on charitable giving, student loan interest payment, and IRA contribtions
and to adjust the distribution of interest, dividend, and business income.

The student loan interest deduction is capped at $2,500, and IRA contributions
are limited at either $6,500 or $5,500 depending on the age of the head of the
tax unit. Total charitable contributions are capped at one half of AGI
and, after this limit is applied, split between cash and non-cash contributions
using the ratios found in the PUF.

We adjust income distributions with a
method developed by the Open Source Policy Center. Using data from the
Individual Statistical tables [made available by the IRS](https://www.irs.gov/uac/soi-tax-stats-individual-statistical-tables-by-size-of-adjusted-gross-income),
we determine the distribution of each targeted variable as reported for the
year 2014. The CPS records are then grouped into 16 bins based on total
income.<sub>3</sub> Using the distribution found in the IRS data, we determine
the ideal weighted sum in each income bin. This goal amount is then compared to
the actual amount in each bin and a ratio is established for each bin. The
records in each bin are then multiplied by their respective ratios so that the
distribution more closely matches what is seen in the IRS data.

<sup>1</sup> factor = (targeted total)/(CPS weighted total)
<sup>2</sup> This rounding does not have a noticable effect on the projections
made by Tax-Calculator
<sup>3</sup> We use total income to create the groups because AGI in the CPS was
determined to not be a good fit for this.