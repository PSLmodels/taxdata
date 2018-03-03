# Current Population Survey Tax Unit File Documentation

Microsimulation models, such as
[Tax-Calculator](https://github.com/open-source-economics/Tax-Calculator),
rely on datasets comprising individual tax units. These datasets are available
through the IRS, but at substantial financial cost and are not permitted to be
shared. This document outlines the creation of a tax unit dataset created from
publicly available CPS files that is suitable for use with Tax-Calculator.

## Overview

The Annual Social and Economic Supplement (ASEC) to the Current Population
Survey (CPS) is an annual survey of US households conducted in March of every
year. The file contains information on prior-year income and current family
structure that can be used to create tax units comprised of those surveyed.
Our final file is created using the 2013, 2014, and 2015 March CPS supplements.
Dollar amounts in the 2013 and 2014 files are then aged to be compatible
with values in the 2015, making the file representative of tax year 2014.

We use an algorithm developed by John O'Hare at Quantria Strategies with slight
modifications to fit our needs to create the final file. The documentation will
provide a general overview of the algorithm
and our modifications.<sup>1</sup>

## Tax Unit Creation

The CPS consists of records at household, family, and person levels. We use this
structure to build each individual tax unit. We begin by assuming that each
household has at least one tax unit. For those who are single and living alone,
defining a tax unit is straightforward: they are assigned to be single filers
with no dependents and their income as reported in the CPS fills in tax
information. Similarly, individuals living in group quarters are assumed to each
represent individual filers. Households with multiple families or children who
also report income are slightly more complicated.

In these cases, an initial tax unit is created using the head of the household.
The algorithm then loops through the remaining members of the household to
determine if they are part of the first tax unit. If they are, their information
is added as either a spouse or dependent to the head of the household. If they
are not, or are deemed to be a dependent who must also file a return, a new tax
unit is constructed for that person. The search for a spouse and dependents is
repeated, unless they are a dependent filer themselves. Ultimately, all
individuals in the household will be assigned to a tax unit.

Our first modification to this process simply counted the number of people in
three age groups - under 18, 18 to 20, and over 20 years old - in each tax unit.

Our second uses the Open Source CPS Transfer Augmentation Model (C-TAM) to add
imputed benefit participation and amounts for Supplemental Security Income (SSI),
Supplemental Nutrition Assistance Program (SNAP), Medicare, Medicaid, Social
Security, and Veterans' Benefits and the total of several other benefits.
C-TAM imputes these benefits on an individual level using the CPS files before
they are converted into tax units. During the creation process, we modified the
code to add up these benefits so that we have the total benefits received by the
entire unit.

## Top-Coding and Imputation

### Top-Coding

Certain income items in the CPS are top-coded to protect the identity of the
individuals surveyed. Each tax unit with an individual who has been top-coded
is flagged for further processing to account for this.

For the records that have been flagged, the top-coded value is replaced with a
random variable whose mean is the top-coded amount. This process is repeated
15 times per flagged record, resulting in the record being represented 15 times
in the production file with a different value for the top-coded fields in each
and their weight divided by 15.

### Imputation

While the public availability of the CPS makes it ideal for transparency, it
lacks many of the variables found in IRS produced data that are key for tax
analysis. We again use methodology developed by Mr. O'Hare to impute a number
of variables.

#### Home Mortgage Interest Expense

Home owners are identified using the `tenure` variable found in the CPS.
The Federal Reserve Board's Survey of Consumer Finances (SCF) is then used to
impute home value, outstanding mortgage amount, and home equity. Mortgage
interest is then calculated as a fixed percentage of the outstanding mortgage.

#### State and Local Taxes

Mr. O'Hare used Quantria's state tax calculator to obtain state income taxes
paid. The local taxes portion of this deduction is ignored due to a lack of data.

#### Charitable and Miscellaneous Deductions

Charitable and miscellaneous deductions are imputed using regression coefficients
from the Public Use SOI file for all tax units. A tobit model is then used for
those with positive values for each item to estimate the final values.

#### Medical Expenses

Total medical expenses are imputed for all tax units using regression imputations
based on expenses reported in the Medical Expenditure Panel Survey.

#### Domestic Production Activity Deduction

Imputations for the Domestic Production Activity Deduction (DPAD) are only
conducted for tax units with positive or negative self-employment or rental
income. Both the estimated probability of claiming that deduction and its
value are then calculated based on the total income in each tax unit. Both
the probability of claiming the deduction and the total deduction estimated
increasing with total income.

#### Self-Employed Health Insurance Deduction

The CPS is used to identify sole proprietors, partners, and S-Corporation
shareholders eligible to claim the deduction. A two-step regression procedure
is then used to estimate the amount of premiums paid. The probability of a unit
claiming this deduction is estimated based on the SOI Public Use File (PUF), and
then the conditional amount claimed is then estimated as well.

#### Other Imputations

Capital gains/losses, taxable IRA distributions, adjusted IRA distributions,
KEOGH plans, and student loan interest deductions are all imputed using a
two-step approach based on the PUF. First, the probability of realizing a capital
gain/loss, claiming a deduction, etc. is estimated. Then, conditional amounts
for each field are imputed.

### Final Preparations

After adjusting for top-coding and imputations, we have a rough production file.
The first step in readying the file for use with Tax-Calculator is simply
renaming a number of variables so that they match the variable names in
Tax-Calculator.

Total wages, self-employment income, and farm income is found for each tax unit
by summing the values for the head of the tax unit and their spouse.

Interest income is split between taxable and nontaxable using the ratio between
the two found in the PUF. Total dividends is separated into ordinary and
qualified dividends in the same manner. Pensions and annuities included in AGI
are derived from total pensions and annuities reported in the CPS also in
proportion to the ratio in the PUF.

We also apply the limitations to certain itemized deductions as they are found
in current tax law. Total charitable contributions are capped at one half of AGI
and, after this limit is applied, split between cash and non-cash contributions
using the ratios found in the PUF.

The student loan interest deduction is capped at $2,500, and IRA contributions
are limited at either $6,500 or $5,500 depending on the age of the head of the
tax unit.

We then count the number of dependents under 5 and 13 or over 65 years old.
Finally, the number of children qualified for the child tax credit, childcare
credit, and earned income credit are counted for each tax unit.

The last step in the final preparations is adjusting the distribution of interest
income, ordinary and qualified dividends, and self-employment income using a
method developed by the Open Source Policy Center. Using data from the
Individual Statistical tables [made available by the IRS](https://www.irs.gov/uac/soi-tax-stats-individual-statistical-tables-by-size-of-adjusted-gross-income),
we determine the distribution of each targeted variable as reported for the
year 2014. The CPS records are then grouped into 19 bins based on total
income.<sub>2</sub> Using the distribution found in the IRS data, we determine
the ideal weighted sum in each income bin. This goal amount is then compared to
the actual amount in each bin and a ratio is established for each bin. The
records in each bin are then multiplied by their respective ratios so that the
distribution more closely matches what is seen in the IRS data.


<sup>1</sup>A more detailed explanation of the algorithm is available
on the [Quantria website](http://www.quantria.com/assets/img/TechnicalDocumentationV4-2.pdf))

<sup>2</sup> We use total income to create the groups because AGI in the CPS was
determined to not be a good fit for this.
