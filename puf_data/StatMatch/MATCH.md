# CPS Match File documentation

The file `cps-matched-puf.csv` is the result of a statistical match performed between the 2016 Current Population Annual Social and Economic Supplement (see the [Datasets documentation](../datasets.md#input-files) for more information).


## Process

Data from the 2016 CPS data is first collected and organized, then tax filing units are constructed from this CPS data, missing data is imputed from similar data through [Predictive Mean Matching](https://stefvanbuuren.name/fimd/sec-pmm.html) (using Euclidean-based nearest neighbor distance as the performance metric) and compiles a final production file. [`runmatch.py`](Matching/runmatch.py) is responsible for the compilation of this final production file. This file is used in [`stage2.py`](../puf_stage2/stage2.py) and [`stage3.py`](../puf_stage3/stage3.py).

More information on the Stage 2 and Stage 3 files can be found in [this document](../puf_stage3/doc/puf_stage3.md), and the statistical matching process is outlined in detail in [this document](docs/MatchingDocumentationRevised.pdf).



## Files Used

The matched file `cps-matched-puf.csv` is created by running [`runmatch.py`](Matching/runmatch.py). See the [README](README.md) for more information on the dependencies of [`runmatch.py`](Matching/runmatch.py).



## Contributors

- Matt Jensen
- Peter Metz
- Anderson Frailey
- Martin Holmer



**TODO**:

- strengths and weaknesses of matching


