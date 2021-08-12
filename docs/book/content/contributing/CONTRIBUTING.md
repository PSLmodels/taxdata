(content:contributing)=
# TaxData Contributor Guide

Contributions to TaxData are always welcome. This document aims to serve as a
guide to setting up your developer environment, and requesting
and contributing new features, and reporting bugs. It assumes familiarity with
the Conda package manager, Git, and GitHub.

More information on Git and GitHub can be found [here](https://docs.github.com/en/github/getting-started-with-github).
More information about Conda can be found [here](https://docs.conda.io/en/latest/).

**Contents**

- [TaxData Contributor Guide](#taxdata-contributor-guide)
  - [Feature Requests](#feature-requests)
  - [Bug Reports](#bug-reports)
  - [Developer Set Up](#developer-set-up)
  - [About the Data](#about-the-data)
  - [Common Contributions](#common-contributions)
    - [Updating CBO Projections](#updating-cbo-projections)
    - [Updating SOI Estimates](#updating-soi-estimates)
    - [Adding and Removing Variables](#adding-and-removing-variables)
  - [Testing](#testing)
  - [Workflow](#workflow)
  - [Issuing New Releases](#issuing-new-releases)
  - [IMPORTANT NOTE](#important-note)

## Feature Requests

To request a new feature, variable, etc. in TaxData, open up an [issue](https://github.com/PSLmodels/taxdata)
detailing your request. If your request is to include a new variable in either
`cps.csv.gz` or `puf.csv`, please include a description of how that variable will
be used.

## Bug Reports

If you find an error in the final datasets or in the code used to produce our
datasets, please open up an [issue](https://github.com/PSLmodels/taxdata) with
details about the bug and what you believe the solution should be.

## Developer Set Up

All development must be done in the `taxdata-dev` conda environment. To set up
the environment, first [install conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
locally. Next, fork the TaxData repository and activate the conda environment:

```bash
$ cd taxdata
$ conda env create -f environment.yml
$ conda activate taxdata-dev
```

Once you have successfully created and activated the `taxdata-dev` conda
environment, you're ready to start contributing.

## About the Data

The two data sources we currently use are the [CPS March Supplements](https://data.nber.org/data/current-population-survey-data.html)
and [IRS SOI Public Use File (PUF)](https://www.irs.gov/statistics/soi-tax-stats-individual-public-use-microdata-files).
The CPS supplements are publicly available while the PUF must be purchased from
the IRS. We cannot provide our copy to anyone who has not signed the necessary
documents from the IRS.

TaxData produces two microdata files: `puf.csv` and `cps.csv.gz`. More information
about these files can be found [here](https://github.com/PSLmodels/taxdata/blob/master/datasets.md). Each file has a corresponding weights file, `puf_weights.csv.gz`
and `cps_weights.csv.gz`, respectively. Additionally, TaxData creates `grow_factors.csv`
and `puf_ratios.csv`. These two files are used to extrapolate the microdata in
the future. Documentation on our extrapolation methods can be found [here](https://github.com/PSLmodels/taxdata/tree/master/doc).
Documentation on `puf_ratios.csv` can be found [here](https://github.com/PSLmodels/taxdata/blob/master/puf_stage3/doc/puf_stage3.md).

## Common Contributions

Contributions typically fall into two categories:
1. Updating the CBO forecasts and IRS-SOI estimates that we use during our extrapolation
routines.
2. Adding or removing variables from `puf.csv` and `cps.csv.gz`.

### Updating CBO Projections

We use data from the CBO 10-Year economic projections, revenue projections, and
unemployment compensation projections, in conjunction with data from IRS
publication 6187, OASI Trust Fund Annual Trustees Report, and BLS and the basis
of our extrapolations. The entire update process has been automated and instructions
on how to do it can be found [here](https://github.com/PSLmodels/taxdata/blob/master/doc/CBO_Baseline_Updating_Instructions.md).

NOTE: If you want to change the content contained in the CBO update documentation,
you must change the template used to create the documentation, otherwise your
changes will be written over. The template can be found at
`taxdata/puf_stage1/doc/cbo_instructions_template.md`.

### Updating SOI Estimates

Documentation for updating the SOI estimates can be found [here](https://github.com/PSLmodels/taxdata/blob/master/doc/SOI_Estimates_Updating_Instructions.md).

### Adding and Removing Variables

Before you start to add new variables, open up an [issue](https://github.com/PSLmodels/taxdata)
to explain what the new variables is, why it's needed, how it will be used by
Tax-Calculator, etc. Once you've done that, all of the code used to create the
microdata files can be found in the `cps_data` and `puf_data` directories. The
exact changes you will need to make depend on the nature of the variable you're
adding. We're working on documentation to provide more details on the internal
workings of these files. In the meantime, please include any questions you
have in the issue related to the new variable.

You will also need to add that variable to `taxdata/tests/records_metadata.json`.
For example, the metadata for the variable `e00200` is
```json
"e00200": {
    "type": "float",
    "desc": "Wages, salaries, and tips for filing unit",
    "form": {
      "2013-2016": "1040 line 7"
    },
    "availability": "taxdata_puf, taxdata_cps",
    "range": {
      "min": 0,
      "max": 9e+99
    }
}
```
- `type` is typically `float` for monetary variables such as wages and `int` for
categorical or boolean variables e.g. `MARS` and `MIDR`
```json
"MARS": {
    "required": true,
    "type": "int",
    "desc": "Filing (marital) status: line number of the checked box [1=single, 2=joint, 3=separate, 4=household-head, 5=widow(er)]",
    "form": {
      "2013-2016": "1040 lines 1-5"
    },
    "availability": "taxdata_puf, taxdata_cps",
    "range": {
      "min": 1,
      "max": 5
    }
},
"MIDR": {
    "type": "int",
    "desc": "1 if separately filing spouse itemizes; otherwise 0",
    "form": {
      "2013-2016": "1040 line 39b"
    },
    "availability": "taxdata_puf",
    "range": {
      "min": 0,
      "max": 1
    }
}
```

- `desc` is a short description of the variable.
- `form` is the IRS form where the variable would be found (if applicable).
- `availability` indicated which files the variable will be available in.
- `range` gives the minimum and maximum allowable values for that variable.

You can (and should) make any additions to the test suite you feel are necessary
to ensure that any mistakes related to this new variable are caught before they
are merged into the master branch.

All of the above also applies to removing variables. You will need to open up an
issue to explain exactly why that variable is no longer needed and to remove
its metadata from `records_metadata.json`.

## Testing

TaxData has a robust test suite used to validate all of the data it produces
before it is merged into Tax-Calculator. All of these tests are run from the
commmand line by navigating to the top of the `taxdata` directory and entering
```bash
$ pytest
```
Depending on what changes you made multiple tests may initially fail. This is
completely expected at first. Each failed test's error message will contain
instruction for resolving the failure.

A common failure occurs if you cause any changes to the microdata files. We track
the expected aggregate totals for each variable in `taxdata/tests/cps_agg_expected.txt`
and `taxdata/tests/puf_agg_expected.txt`. If the new microdata files do not match
those aggregate numbers, new files called `cps_agg_actual.txt` and `puf_agg_actual.txt`
will be created. If the changes are expected and explainable, simply copy the
contents of the `{file}_actual.txt` file into `{file}_expected.txt` file. Do
not include the `{file}_actual.txt` files to your Git commits.

## Workflow

A typical workflow is
1. Update your local master branch
```bash
$ git checkout master
$ git fetch upstream
$ git merge upstream/master
$ git push origin master
```

2. Activate `taxdata-dev` and create a new branch to work on
```bash
$ cd taxdata
$ conda activate taxdata-dev
$ git checkout -b {branchname}
```
Creating a new branch instead of working on your master branch will prevent your
master branch from getting ahead or behing of the central repository and save
you a massive headache down the line.

3. Make all of the changes you need following the general guidelines laid out
above.

4. Run the Makefile to create all of the files by navigating to the top of the
directory and running one of the following commands:
```bash
$ make all
$ make puf-files
$ make cps-files
```
`make puf-filles` will run only the scripts used to make files associated with
the PUF file. `make cps-files` will run only the scripts ued to make files
associated with the CPS file. `make all` will run everything.

To minimize changes caught by version control, it is vital that you use these
`make` commands rather than running each python file manually.

5. Test your changes using pytest.
```bash
$ pytest
```

6. Resolving any test failures.

7. Push your changes to GitHub and open a PR.

## Issuing New Releases

As of now, all TaxData releases will only be stored on GitHub. To create a new
release simply navigate to the [releases page](https://github.com/PSLmodels/taxdata/releases)
and click "Draft a new release". When you issue a new release, be sure to include
a link and short description to each of the PRs that have been merged in since
the last release. These release notes will serve as our change log.

TaxData uses a semantic versioning system with the following criteria:

**Major Release**
* Removing the capability to use PUF or CPS versions

**Minor Release**
* Significant methodology enhancements e.g. adding a new linear programming model,
updating statistical matching or tax unit creation, new imputation methods, etc.
* Adding new variables
* Minor changes to tax unit creation logic that don't break the API
* Adding support for creating files from different years of the PUF and CPS,
assuming this doesn't break backward compatibility
* Adding new imputation methods for new variables w/o breaking the existing API
* Updating which CBO projections we use to calculate growth rates (until we can
parameterize the choice of cbo projections, after which removing an option would
necessitate a major release)

**Patch Release**
* Standard bug patches

Eventually, we would like to generalize the TaxData API enough to create a fully
fleshed out python package. We will revist our release procedures when this
happens.

## IMPORTANT NOTE

Never ever ever include `puf.csv`, `cps_matched_puf.csv`, or any other file
containing non-aggregated data from the PUF in your Git commits. We have
included them in the `.gitignore` file to help prevent this from happening. Do
not change that. Ever.