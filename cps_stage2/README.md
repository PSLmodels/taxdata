About cps_stage2
================

This directory contains the following script:

* Python script `finalprep.py`, which reads/writes:

  Input files:
    - `cps_weights_raw.csv.gz`

  Output files:
    - `cps_weights.csv.gz`


Documentation
-------------

`cps_weights_raw.csv.gz` was provided to us by John O'Hare of
[Quantria Strategies](http://www.quantria.com). `finalprep.py`
reads in this file, multiplies each record by 100, and changes each weight from
a floating point to an integer in order to reduce file size.
