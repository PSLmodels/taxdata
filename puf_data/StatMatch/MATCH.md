# CPS Match File documentation

The `cps-matched-puf.csv` file is the result of a statistical match performed between the 2016 Current Population Annual Social and Economic Supplement and the 2011 IRS-SOI Public Use File. See the [Datasets documentation](../datasets.md#input-files) for more information.


## Process

Data from the 2016 CPS data is first collected and organized. Tax filing units are then constructed from this CPS data, missing data is imputed from similar data through [Predictive Mean Matching](https://stefvanbuuren.name/fimd/sec-pmm.html) and the statistical match is performed using nearest neighbor distance as the criterion for matching filing units. [`runmatch.py`](Matching/runmatch.py) is responsible for running the match and compiling a final production file.



#### Pros/Cons of Matching Methodology

The statistical match performed to create this document is a "constrained" match. This is a process that matches similar filing units from the CPS and PUF such that the weights on individual filing units within a document aggregate (sum up) to match the total weight of said document (e.x. all individual weights in the CPS document sum up to the weight of the CPS document itself). The benefit of this constrained matching approach is it retains original disributions of variables from within the CPS and PUF files. There are 2 principal drawbacks to this method: (1) The solver may sometimes max filing units that are not very similar statistically, and (2) the method is computationally expensive.



## Files Used

`cps-matched-puf.csv` is created by running [`runmatch.py`](Matching/runmatch.py). See the [README](README.md) for more information on the scripts used by [`runmatch.py`](Matching/runmatch.py).

The output of [`runmatch.py`](Matching/runmatch.py) is used in [`stage2.py`](../puf_stage2/stage2.py) and [`stage3.py`](../puf_stage3/stage3.py). More information on the Stage 2 and Stage 3 files can be found in [this document](../puf_stage3/doc/puf_stage3.md), and the statistical matching process is outlined in detail in [this document](doc/MatchingDocumentationRevised.pdf).



## Contributors

- Matt Jensen
- Peter Metz
- Anderson Frailey
- Martin Holmer
- Max Ghenis


