About CPS Data
==============

The python scripts used to create `cps.csv.gz` can be found in `taxdata/cps`.
To create this file your self, import and run the `cps.create` function as
demonstrated below:
```python
from taxdata import cps

raw_cps = cps.create(
    datapath=DATA_PATH,
    exportcsv=False,
    exportpkl=True,
    exportraw=False,
    validate=False,
    benefits=True,
    verbose=True,
)
```
where `DATA_PATH` is a path to the directory where you store the original CPS
files. If you are only interested in using the default settings, you can just
run `createcps.py`.

By default, the CPS file will be composed of the 2013, 2014, and 2015 March CPS
Supplemental files. `taxdata` also supports using the 2016, 2017, and 2018 files.
Support for additional files will be added as they become available.

To use a non-default set of files, add the `cps_files` parameter to your function
call:

```python
raw_cps = cps.create(
    datapath=DATA_PATH,
    exportcsv=False,
    exportpkl=True,
    exportraw=False,
    validate=False,
    benefits=True,
    verbose=True,
    cps_files=[2016, 2017, 2018]
)
```

Once the raw file has been created, you will need to run it through the
`finalprep` function before it it ready to be used by Tax-Calculator.

```python
final_cps = cps.finalprep(raw_cps)
final_cps.to_csv(final_output_path, index=False)
```

## Input files:
With the exception of the CPS March Supplements, all input files can be found
in the `cps/data` directory.

### CPS March Supplements
* asec2013_pubuse.dat
* asec2014_pubuse_tax_fix_5x8_2017.dat
* asec2015_pubuse.dat
* asec2016_pubuse.dat
* asec2017_pubuse.dat
* asec2018_pubuse.dat

### C-TAM Benefit Imputations

Note that we only have C-TAM imputations for the 2013, 2014, and 2015 files.
For other years, we just use the benefit program information in the CPS
* Housing_Imputation_logreg_2013.csv
* Housing_Imputation_logreg_2014.csv
* Housing_Imputation_logreg_2015.csv
* medicaid2013.csv
* medicaid2014.csv
* medicaid2015.csv
* medicare2013.csv
* medicare2014.csv
* medicare2015.csv
* otherbenefitprograms.csv
* SNAP_Imputation_2013.csv
* SNAP_Imputation_2014.csv
* SNAP_Imputation_2015.csv
* SS_augmentation_2013.csv
* SS_augmentation_2014.csv
* SS_augmentation_2015.csv
* SSI_Imputation2013.csv
* SSI_Imputation2014.csv
* SSI_Imputation2015.csv
* TANF_Imputation_2013.csv
* TANF_Imputation_2014.csv
* TANF_Imputation_2015.csv
* UI_imputation_logreg_2013.csv
* UI_imputation_logreg_2014.csv
* UI_imputation_logreg_2015.csv
* VB_Imputation2013.csv
* VB_Imputation2014.csv
* VB_Imputation2015.csv
* WIC_imputation_children_logreg_2013.csv
* WIC_imputation_children_logreg_2014.csv
* WIC_imputation_children_logreg_2015.csv
* WIC_imputation_infants_logreg_2013.csv
* WIC_imputation_infants_logreg_2014.csv
* WIC_imputation_infants_logreg_2015.csv
* WIC_imputation_women_logreg_2013.csv
* WIC_imputation_women_logreg_2014.csv
* WIC_imputation_women_logreg_2015.csv

### Imputation Parameters

These parameters are used in the imputations found in `taxdata/cps/data/impute.py`
* logit_beta.csv
* ols_betas.csv

## Output Files

Only `cps.csv.gz` is included in the repository due to the size of `cps_raw.csv.gz`.
* cps.csv.gz
* cps_raw.csv.gz


Documentation
-------------

More information about the data in the `cps_raw.csv.gz` file is
available in [this document](https://github.com/PSLmodels/taxdata/blob/master/doc/cps_file_doc.md).

All of the benefit costs listed in `benefitprograms.csv` can be found
in tables 3.2 and 11.3 of the archived [Historical
tables](https://obamawhitehouse.archives.gov/omb/budget/Historicals)
of the Office of Management and Budget. All costs are in millions of
dollars.
