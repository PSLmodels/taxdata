About cps_data
==============

This directory contains the python scripts used to create `cps.csv.gz`. You
can run all of the scripts with the command `python create.py`. By default,
you will get a CPS file composed of the 2013, 2014, and 2015 March CPS Supplemental
files. If you would like to use another combination of the 2013, 2014, 2015,
2016, 2017, and 2018 files, there are two ways to do so.

1. You can modify `create.py` by adding the `cps_files` argument to the `create()`
function call at the bottom of the file to specify which files you would like to
use. For example, to use the 2016, 2017, and 2018 files, the function call would
now be
```python
if __name__ == "__main__":
    create(
        exportcsv=False, exportpkl=True, exportraw=False, validate=False,
        benefits=True, verbose=True, cps_files=[2016, 2017, 2018]
    )
```

2. You could write a separate python file that imports the `create()` function
and calls it in the same way as above.

## Input files:
With the exception of the CPS March Supplements, all input files can be found
in the `pycps/data` directory.

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

These parameters are used in the imputations found in `pycps/impute.py`
* logit_beta.csv
* ols_betas.csv

## Output Files

Only `cps.csv.gz` is included in the repository due to the size of `cps_raw.csv.gz`.
* cps.csv.gz
* cps_raw.csv.gz


Documentation
-------------

More information about the data in the `cps_raw.csv.gz` file is
available in [this document](cps_file_doc.md).

All of the benefit costs listed in `benefitprograms.csv` can be found
in tables 3.2 and 11.3 of the archived [Historical
tables](https://obamawhitehouse.archives.gov/omb/budget/Historicals)
of the Office of Management and Budget. All costs are in millions of
dollars.
