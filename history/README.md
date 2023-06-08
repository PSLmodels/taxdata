# TaxData History

This directory contains PDF files that detail the evolution of the TaxData
outputs as we update the CBO projections and IRS SOI estimates used to create
weights and growth factors as well as the underlying code that produce these
outputs.

Use this command to create your reports

```bash
python report.py "{list of PRs}" --desc sampletxt.txt --basepuf ../puf.csv
```
As the text implies, `{list of PRS}` is be a list of the PRs being summarized
in the report. The `--desc` argument allows you to add some additional information
to the reports by pointing to a text or markdown file that will appear at the
beginning of the report. The `--basepuf` argument only needs to be used if you'd
like to include information about changes to the PUF in the report.