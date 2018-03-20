# Available Datasets

## Summary

TaxData now offers two datasets created to run in the open source Tax-Calculator:
`PUF.csv` and `CPS.csv`. Both files are representative micro-datasets containing
tax unit level data. The key differences are the sources used to create each file
and the aggregate results and distributions.

The PUF is created using a statistical match between the
IRS-SOI Public Use File and the Census Current Population Survey. The use of
IRS-SOI data is restricted and therefore we cannot provide access to them to
the general public.

The CPS is created using the Census Current Population Survey, Annual Social
and Economic Supplement data for March 2013, 2014, and 2015. Household and family
information from the surveys are used to create tax units based on income and
relationship data. Because the CPS is not designed for tax reporting purposes,
results from constructed tax units are expected to be different from PUF in
term of both aggregates and distribution. In addition, the CPS includes very
limited high income households and has under-coverage issues in lower income
households. Therefore, the wage distribution of CPS is different from that of PUF.
Additional data on welfare and transfer program participation and benefits is
added to the CPS using the open source CPS Transfer Augmentation Model (C-TAM).
C-TAM is used to impute benefit values for SNAP, SSI, Social Security,
Medicare, Medicaid, veterans benefits, housing assistance, TANF, and WIC.

## Variable Availability

Because benefit data is imputed onto the CPS, it is not available in the PUF.
Similarly, the CPS is missing some income and deduction variables only available
in the PUF.

A full list of variables available in each file can be found in
[`records_variables.json`](https://github.com/open-source-economics/Tax-Calculator/blob/master/taxcalc/records_variables.json)
in the Tax-Calculator repository. The availability of each variable is specified
in the `availability` section. PUF availability is indicated by `taxdata_puf`,
CPS availability by `taxdata_cps`.

Due to missing variables, certain policy parameters will be ineffective depending
on which file you're using. These will be greyed out in TaxBrain. The policy
parameters available in Tax-Calculator can be found in
[`current_law_policy.json`](https://github.com/open-source-economics/Tax-Calculator/blob/master/taxcalc/current_law_policy.json)
in the Tax-Calculator repository. The dataset(s) compatible with each parameter
are indicated by boolean values in the `compatible_data` field.

## Aggregate Totals

The weighted totals of each variable will differ between the two datasets.
Totals by year for the CPS can be found [here](https://github.com/open-source-economics/Tax-Calculator/blob/master/taxcalc/tests/cpscsv_agg_expect.txt).
For the PUF, [here](https://github.com/open-source-economics/Tax-Calculator/blob/master/taxcalc/tests/pufcsv_agg_expect.txt).
