% TaxData Updates
% Generated on {{ date }}

This report summarizes changes made in the TaxData repository that affect
tax liability projections made by [Tax-Calculator](https://pslmodels.github.io/Tax-Calculator/).
All tables and graphs in this report are automatically generated.

{{ desc }}

# Pull Requests

The pull requests listed below were merged before this report was generated:

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

{% for item in dist_plots %}
{{ item }}
{% endfor %}

# Aggregate Tax Liability

{{ agg_plot }}

## Combined Tax Liability by Year (Billions)

{{ combined_table }}

## Income Tax Liability by Year (Billions)

{{ income_table }}

## Payroll Tax Liability by Year (Billions)

{{ payroll_table }}