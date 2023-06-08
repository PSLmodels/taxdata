% TaxData Updates
% Generated on {{ date }}

This report summarizes changes made in the TaxData repository that affect
tax liability projections made by [Tax-Calculator](https://pslmodels.github.io/Tax-Calculator/).
All tables and graphs in this report are automatically generated.

{{ desc }}

# Pull Requests and Issues

This report corresponds with the issues and pull requests listed below.

{% for item in prs %}
{{ item }}
{% endfor %}

# Changes in Variable Availability

### PUF

##### _Added Variables_  

{% for item in puf_added %}
{{ item }}
{% endfor %}

##### _Removed Variables_  

{% for item in puf_removed %}
{{ item }}
{% endfor %}

### CPS

##### _Added Variables_  

{% for item in cps_added %}
{{ item }}
{% endfor %}

##### _Removed Variables_  

{% for item in cps_removed %}
{{ item }}
{% endfor %}

# CBO Projections

{% for item in cbo_projections %}
{{ item }}
{% endfor %}

\pagebreak

# Growth Rate Projections

{% for item in growth_rate_projections %}
{{ item }}
{% endfor %}

\pagebreak

# Distribution of Select Variables (year: first year in the projection tables)

## CPS

{% for item in cps_dist_plots %}
{{ item }}
{% endfor %}

## PUF

{% for item in puf_dist_plots %}
{{ item }}
{% endfor %}

# Aggregate Tax Liability

## CPS 

{{ cps_agg_plot }}

## Combined Tax Liability by Year (Billions)

{{ cps_combined_table }}

## Income Tax Liability by Year (Billions)

{{ cps_income_table }}

## Payroll Tax Liability by Year (Billions)

{{ cps_payroll_table }}

# Projection

## CPS

## Salaries and Wages by Year (Billions)

{{ cps_salaries_and_wages_table }}

## Taxable interest and ordinary dividends (excludes qualified dividends) by Year (Billions)

{{ cps_taxable_interest_and_ordinary_dividends_table }}

## Qualified dividends by Year (Billions)

{{ cps_qualified_dividends_table }}

## Capital gain or loss by Year (Billions)

{{ cps_capital_table }}

## Net business income (all income and loss reported on Schedules C, E, and F) by Year (Billions)

{{ cps_business_table }}

## Taxable pensions and annuities and IRA distributions by Year (Billions)

{{ cps_pensions_annuities_IRA_distributions_table }}

## Taxable Social Security benefits by Year (Billions)

{{ cps_Social_Security_benefits_table }}

## All other sources of income by Year (Billions)

{{ cps_all_other_income_table }}

## Total income by Year (Billions)

{{ cps_total_income_table }}

## Statutory Adjustments by Year (Billions)

{{ cps_statutory_Adjustments_table }}

## Total AGI by Year (Billions)

{{ cps_total_AGI_table }}

## Subtract Personal exemption amount (after limit) by Year (Billions)

{{ cps_sub_peronal_expt_table }}

## Subtract Standard deduction (non-itemizers only) by Year (Billions)

{{ cps_sub_std_table }}

## Subtract Total itemized deductions (itemizers only) after limits by Year (Billions)

{{ cps_sub_tot_item_table }}

## Subtract Qualified business income deduction by Year (Billions)

{{ cps_sub_qbid_table }}

## Total exemptions and deductions after limits by Year (Billions)

{{ cps_sub_tot_expt_table }}

## Taxable income by Year (Billions)

{{ cps_taxable_inc_table }}

## Total Income Tax by Year (Billions)

{{ cps_tot_inctax_table }}

## Total credits (refundable and nonrefundable) by Year (Billions)

{{ cps_tot_cdt_table }}

## Income tax after credits (Excluding refundable tax credits) by Year (Billions)

{{ cps_inctax_af_credit_table }}

## Top 1% income group shares of AGI (percent)

{{ cps_Top1_percent_income_group_shares_of_AGI_table }}

## Top 5% income group shares of AGI (percent)

{{ cps_Top5_percent_income_group_shares_of_AGI_table }}

## Top 10% income group shares of AGI (percent)

{{ cps_Top10_percent_income_group_shares_of_AGI_table }}

## Top 25% income group shares of AGI (percent)

{{ cps_Top25_percent_income_group_shares_of_AGI_table }}

## Top 50% income group shares of AGI (percent)

{{ cps_Top50_percent_income_group_shares_of_AGI_table }}


\pagebreak

# Aggregate Tax Liability 

## PUF

{{ puf_msg }}

{{ puf_agg_plot }}

## Combined Tax Liability by Year (Billions)

{{ puf_combined_table }}

## Income Tax Liability by Year (Billions)

{{ puf_income_table }}

## Payroll Tax Liability by Year (Billions)

{{ puf_payroll_table }}

# Projection

## PUF

## Salaries and Wages by Year (Billions)

{{ puf_salaries_and_wages_table }}

## Taxable interest and ordinary dividends (excludes qualified dividends) by Year (Billions)

{{ puf_taxable_interest_and_ordinary_dividends_table }}

## Qualified dividends by Year (Billions)

{{ puf_qualified_dividends_table }}

## Capital gain or loss by Year (Billions)

{{ puf_capital_table }}

## Net business income (all income and loss reported on Schedules C, E, and F) by Year (Billions)

{{ puf_business_table }}

## Taxable pensions and annuities and IRA distributions by Year (Billions)

{{ puf_pensions_annuities_IRA_distributions_table }}

## Taxable Social Security benefits by Year (Billions)

{{ puf_Social_Security_benefits_table }}

## All other sources of income by Year (Billions)

{{ puf_all_other_income_table }}

## Total income by Year (Billions)

{{ puf_total_income_table }}

## Statutory Adjustments by Year (Billions)

{{ puf_statutory_Adjustments_table }}

## Total AGI by Year (Billions)

{{ puf_total_AGI_table }}

## Subtract Personal exemption amount (after limit) by Year (Billions)

{{ puf_sub_peronal_expt_table }}

## Subtract Standard deduction (non-itemizers only) by Year (Billions)

{{ puf_sub_std_table }}

## Subtract Total itemized deductions (itemizers only) after limits by Year (Billions)

{{ puf_sub_tot_item_table }}

## Subtract Qualified business income deduction by Year (Billions)

{{ puf_sub_qbid_table }}

## Total exemptions and deductions after limits by Year (Billions)

{{ puf_sub_tot_expt_table }}

## Taxable income by Year (Billions)

{{ puf_taxable_inc_table }}

## Total Income Tax by Year (Billions)

{{ puf_tot_inctax_table }}

## Total credits (refundable and nonrefundable) by Year (Billions)

{{ puf_tot_cdt_table }}

## Income tax after credits (Excluding refundable tax credits) by Year (Billions)

{{ puf_inctax_af_credit_table }}


## Top 1% income group shares of AGI (percent)

{{ puf_Top1_percent_income_group_shares_of_AGI_table }}

## Top 5% income group shares of AGI (percent)

{{ puf_Top5_percent_income_group_shares_of_AGI_table }}

## Top 10% income group shares of AGI (percent)

{{ puf_Top10_percent_income_group_shares_of_AGI_table }}

## Top 25% income group shares of AGI (percent)

{{ puf_Top25_percent_income_group_shares_of_AGI_table }}

## Top 50% income group shares of AGI (percent)

{{ puf_Top50_percent_income_group_shares_of_AGI_table }}



\pagebreak

# Validation 

## CPS

## Salaries and Wages by Year (Billions)

{{ cps_validation_salaries_and_wages_table }}

## Taxable interest and ordinary dividends (excludes qualified dividends) by Year (Billions)

{{ cps_validation_taxable_interest_and_ordinary_dividends_table }}

## Qualified dividends by Year (Billions)

{{ cps_validation_qualified_dividends_table }}

## Capital gain or loss by Year (Billions)

{{ cps_validation_capital_table }}

## Net business income (all income and loss reported on Schedules C, E, and F) by Year (Billions)

{{ cps_validation_business_table }}

## Taxable pensions and annuities and IRA distributions by Year (Billions)

{{ cps_validation_pensions_annuities_IRA_distributions_table }}

## Taxable Social Security benefits by Year (Billions)

{{ cps_validation_Social_Security_benefits_table }}

## All other sources of income by Year (Billions)

{{ cps_validation_all_other_income_table }}

## Total income by Year (Billions)

{{ cps_validation_total_income_table }}

## Statutory Adjustments by Year (Billions)

{{ cps_validation_statutory_Adjustments_table }}

## Total AGI by Year (Billions)

{{ cps_validation_total_AGI_table }}

## Subtract Personal exemption amount (after limit) by Year (Billions)

{{ cps_validation_sub_peronal_expt_table }}

## Subtract Standard deduction (non-itemizers only) by Year (Billions)

{{ cps_validation_sub_std_table }}

## Subtract Total itemized deductions (itemizers only) after limits by Year (Billions)

{{ cps_validation_sub_tot_item_table }}

## Subtract Qualified business income deduction by Year (Billions)

{{ cps_validation_sub_qbid_table }}

## Total exemptions and deductions after limits by Year (Billions)

{{ cps_validation_sub_tot_expt_table }}

## Taxable income by Year (Billions)

{{ cps_validation_taxable_inc_table }}

## Total Income Tax by Year (Billions)

{{ cps_validation_tot_inctax_table }}

## Total credits (refundable and nonrefundable) by Year (Billions)

{{ cps_validation_tot_cdt_table }}

## Income tax after credits (Excluding refundable tax credits) by Year (Billions)

{{ cps_validation_inctax_af_credit_table }}

## Top 1% income group shares of AGI (percent)

{{ cps_validation_Top1_percent_income_group_shares_of_AGI_table }}

## Top 5% income group shares of AGI (percent)

{{ cps_validation_Top5_percent_income_group_shares_of_AGI_table }}

## Top 10% income group shares of AGI (percent)

{{ cps_validation_Top10_percent_income_group_shares_of_AGI_table }}

## Top 25% income group shares of AGI (percent)

{{ cps_validation_Top25_percent_income_group_shares_of_AGI_table }}

## Top 50% income group shares of AGI (percent)

{{ cps_validation_Top50_percent_income_group_shares_of_AGI_table }}



## PUF

## Salaries and Wages by Year (Billions)

{{ puf_validation_salaries_and_wages_table }}

## Taxable interest and ordinary dividends (excludes qualified dividends) by Year (Billions)

{{ puf_validation_taxable_interest_and_ordinary_dividends_table }}

## Qualified dividends by Year (Billions)

{{ puf_validation_qualified_dividends_table }}

## Capital gain or loss by Year (Billions)

{{ puf_validation_capital_table }}

## Net business income (all income and loss reported on Schedules C, E, and F) by Year (Billions)

{{ puf_validation_business_table }}

## Taxable pensions and annuities and IRA distributions by Year (Billions)

{{ puf_validation_pensions_annuities_IRA_distributions_table }}

## Taxable Social Security benefits by Year (Billions)

{{ puf_validation_Social_Security_benefits_table }}

## All other sources of income by Year (Billions)

{{ puf_validation_all_other_income_table }}

## Total income by Year (Billions)

{{ puf_validation_total_income_table }}

## Statutory Adjustments by Year (Billions)

{{ puf_validation_statutory_Adjustments_table }}

## Total AGI by Year (Billions)

{{ puf_validation_total_AGI_table }}

## Subtract Personal exemption amount (after limit) by Year (Billions)

{{ puf_validation_sub_peronal_expt_table }}

## Subtract Standard deduction (non-itemizers only) by Year (Billions)

{{ puf_validation_sub_std_table }}

## Subtract Total itemized deductions (itemizers only) after limits by Year (Billions)

{{ puf_validation_sub_tot_item_table }}

## Subtract Qualified business income deduction by Year (Billions)

{{ puf_validation_sub_qbid_table }}

## Total exemptions and deductions after limits by Year (Billions)

{{ puf_validation_sub_tot_expt_table }}

## Taxable income by Year (Billions)

{{ puf_validation_taxable_inc_table }}

## Total Income Tax by Year (Billions)

{{ puf_validation_tot_inctax_table }}

## Total credits (refundable and nonrefundable) by Year (Billions)

{{ puf_validation_tot_cdt_table }}

## Income tax after credits (Excluding refundable tax credits) by Year (Billions)

{{ puf_validation_inctax_af_credit_table }}


## Top 1% income group shares of AGI (percent)

{{ puf_validation_Top1_percent_income_group_shares_of_AGI_table }}

## Top 5% income group shares of AGI (percent)

{{ puf_validation_Top5_percent_income_group_shares_of_AGI_table }}

## Top 10% income group shares of AGI (percent)

{{ puf_validation_Top10_percent_income_group_shares_of_AGI_table }}

## Top 25% income group shares of AGI (percent)

{{ puf_validation_Top25_percent_income_group_shares_of_AGI_table }}

## Top 50% income group shares of AGI (percent)

{{ puf_validation_Top50_percent_income_group_shares_of_AGI_table }}






