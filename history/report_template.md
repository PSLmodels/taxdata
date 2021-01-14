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

# Distribution of Select Variables

## CPS

{% for item in cps_dist_plots %}
{{ item }}
{% endfor %}

## PUF

# Aggregate Tax Liability

## CPS

{{ cps_agg_plot }}

## Combined Tax Liability by Year (Billions)

{{ cps_combined_table }}

## Income Tax Liability by Year (Billions)

{{ cps_income_table }}

## Payroll Tax Liability by Year (Billions)

{{ cps_payroll_table }}

\pagebreak

## PUF

{{ puf_msg }}

{{ puf_agg_plot }}

## Combined Tax Liability by Year (Billions)

{{ puf_combined_table }}

## Income Tax Liability by Year (Billions)

{{ puf_income_table }}

## Payroll Tax Liability by Year (Billions)

{{ puf_payroll_table }}