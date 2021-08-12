 # Roadmap

 The `taxdata` project is in constant development.  Some of the key features that `taxdata` maintainers and contributors are targeting in upcoming releases are:

* Improve age variable imputations on the IRS Public Use File
* Refactor the repo to remove redundant code. We can use the same code to make the tax units for the CPS file to make them for the statistical matching and consolidate the Stage 2 scripts.
* Re-write the make files and documentation to reflect recent changes in python scripts used to create the CPS based files
* Revisit how we handle imputations for the CPS
* Possibly make parts of `taxdata` into a standalone package
* Put together some scripts to make a simple report detailing how projections change when we update the CBO projections our extrapolations are based on so that we can have a log of those changes
* Work on making it as easy as possible for others to use `taxdata` to prepare `taxcalc`-ready microdata files using other years of the PUF and CPS.
  * This could go hand in hand with making parts of taxdata a standalone package.
* Incorporate state targeting for the PUF
* Revisit whether we can combine Stage 3 with Stage 2 (and add other distributional targets) thanks to the adoption of new solvers for the federal problem, CVXOPT (already included in `taxdata`) or IPOPT (used in the state work)
* Revisit the PUF-CPS match and filer/non-filer distinction. In particular, Kevin Perese's approach is quite elegant and worth considering as an enhancement or alternative option.