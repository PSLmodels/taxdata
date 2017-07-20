# Creating the CPS Database

This directory contains a set of SAS scripts that use the March 2013, 2014, and
2015 Current Population Survey to create a single tax unit dataset.

The three CPS files needed to start this process can be downloaded from the
[National Bureau of Economic Research website](http://www.nber.org/data/current-population-survey-data.html).
When downloaded, the files will be named `asec2013_pubuse.dat`,
`asec2014_pubuse_tax_fix_5x8_2017.dat`, and `asec2015_pubuse.dat`. They should
be saved at the following locations:

* `CPS Files/March 2013/asec2013_pubuse.dat`
* `CPS Files/March 2014/asec2014_pubuse_tax_fix_5x8_2017.dat`
* `CPS Files/March 2015/asec2015_pubuse.dat`

Before running anything, update the file path in each individual script to match
your system. From there, the scripts should be run in the following order:

1. `CPS Files/March 2013/cpsmar2013r.sas`
2. `CPS Files/March 2014/cpsmar2014.sas`
3. `CPS Files/March 2015/cpsmar2015.sas`
4. `CPS Tax Units/2013/Programs/CPS-RETS13V5.sas`
5. `CPS Tax Units/2013/Programs/AdjustFILSTV4_2013.sas`
6. `CPS Tax Units/2014/Programs/CPS-RETS14V5.sas`
7. `CPS Tax Units/2014/Programs/AdjustFILSTV4_2014.sas`
8. `CPS Tax Units/2015/Programs/CPS-RETS15V5.sas`
9. `CPS Tax Units/2015/Programs/AdjustFILSTV4_2015.sas`
10. `Production File/Programs/CreateProductionFile2015V1.sas`
11. `Production File/TopCoding/TopCodingV1.sas`
12. `Production File/Imputations/Impute3TobitV4.sas`
13. `Production File/Targeting/Targets1-V1.sas`
14. `Production File/Blank Slate Imputations/BlankSlate4-V1.sas`
15. `Production File/Blank Slate Imputations/MergeECPENSIONS.sas`
16. `Production File/Blank Slate Imputations/CleanUp.sas`
