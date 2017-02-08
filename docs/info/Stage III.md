# Stage III Documentation
#### February 2017

Stage I and Stage II of OSPC’s extrapolation procedure blow up and re-weight
each variable in the PUF-CPS matched data file (PUF) in order to match
macroeconomic projections of growth rates and aggregate totals. Stage I
determines per capita blow-up factors using both macro targets and
population growth rates. In Stage II, a linear programming algorithm is applied
in order to adjust the weight given to each record so that all targeted
variables will sum up to their respective targets, while non-targeted variables
also stay in reasonable ranges.

While Stage II does target wage distribution, only the aggregate totals for
all other income variables are targeted and the resulting distributions of
those variables can be inconsistent with what publicly available tax data
shows. Stage III fixes this error by applying an adjustment factor to each
record in the PUF based on the level of AGI in the PUF. The factor is
calculated so that the aggregate value of the variable targeted does not
change, but the distribution more accurately reflects the data.

### Procedure

For the targeted variable, Stage III uses information from
[SOI Tax Stats ](https://www.irs.gov/uac/soi-tax-stats-individual-statistical-tables-by-size-of-adjusted-gross-income)
tables to determine what percent of its total is in each AGI bin for 2009-2014
(see appendix for the bin breakdown). The distribution is assumed to hold at
2014 levels for the years 2015-2026. These are the goal distributions.

For each year adjustment factors are needed, the targeted variable is
extrapolated to that year using the same routine as in Tax-Calculator. The goal
bin amounts are then found using the goal distributions and aggregate total
found in the PUF.

The goal bin amounts are divided by the actual bin amounts, which are
calculated using the AGI variable found in the PUF before final processing, in
order to find a set of adjustment factors that can be multiplied by each
record in each AGI bin so that bin totals reach their targeted levels. 

While this process does benefit from its simplicity, there are some
trade-offs: 

* Because AGI bin is determined using 2009 AGI levels, it does not account for
any change in AGI overtime that could result in a tax unit moving into a
different AGI bin. Thus, the final distribution will not be identical to what
is found in IRS tax data.
* Because the factor is only being applied to one element of income, any
possible relationship between two types of income will be lost. However, in the
case of interest income, there do not appear to be any strong correlations with
other income items (see appendix).

### Results 
Despite relying on AGI level found in the original PUF rather than
recalculating AGI each year to account for growth as Tax-Calc does, the final
distribution when including the adjustment is much more representative of the
distribution found in SOI data, as seen in figure A.

*fig. A*
![Distribution image](https://github.com/andersonfrailey/Notebook-Uploads/blob/master/intincomedistribution.png)

### Tax-Calculator Implementation
Running `stage3.py` in the `stage3` directory will output a file called
`pufadj_factors.csv`. This file is placed in the `taxcalc` directory within the
larger Tax-Calculator package. To apply the proper adjustment factor, Tax-Calc
uses the variable `agi_bin` in `PUF.csv`. This variable is added during the 
final preparation of `PUF.csv` and is between 0 and 18 for each tax unit
dependent on which AGI bin they fall in. Tax-Calc reads in `pufadj_factors.csv`
in the Records class and applies the adjustment factors based on the value of
`agi_bin` for each tax unit.

### Appendix

AGI Level Bins:

| AGI Level              | 
|------------------------| 
| Less than zero         | 
| $1-$5,000              | 
| $5,000 -$10,000        | 
| $10,000-$15,000        | 
| $15,000-$20,000        | 
| $20,000-$25,000        | 
| $25,000-$30,000        | 
| $30,000-$40,000        | 
| $40,000-$50,000        | 
| $50,000-$75,000        | 
| $75,000-$100,000       | 
| $100,000-$200,000      | 
| $200,000-$500,000      | 
| $500,000-$1,000,000    | 
| $1,000,000-$1,500,000  | 
| $1,500,000-$2,000,000  | 
| $2,000,000-$5,000,000  | 
| $5,000,000-$10,000,000 | 
| $10,000,000 and over   | 

Correlations:

| Income Item         | No Adjustment | Adjustment | 
|---------------------|---------------|------------| 
| Wages and Salaries  | 0.091         | 0.089      | 
| Ordinary Dividends  | 0.217         | 0.206      | 
| Qualified Dividends | 0.162         | 0.154      | 
| Business Income     | -0.005        | 0.002      | 
| Capital Gains       | 0.171         | 0.170      | 



