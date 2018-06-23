# GNU Makefile that documents and automates common development operations
#              using the GNU make tool (version >= 3.81)
# Development is typically conducted on Linux or Max OS X (with the Xcode
#              command-line tools installed), so this Makefile is designed
#              to work in that environment (and not on Windows).
# USAGE: taxdata$ make [TARGET]

MADE_FILES = puf_data/puf.csv \
             puf_stage1/growfactors.csv \
             puf_stage1/Stage_I_factors.csv \
             puf_stage2/puf_weights.csv.gz \
             puf_stage3/puf_ratios.csv.gz \
             cps_data/cps.csv.gz \
             cps_stage1/stage_2_targets.csv \
             cps_stage2/cps_weights.csv.gz \
             cps_stage4/cps_benefits.csv.gz

.PHONY=help
help:
	@echo "USAGE: make [TARGET]"
	@echo "TARGETS:"
	@echo "help        : show help message"
	@echo "clean       : remove all .pyc files"
	@echo "clean CSV=x : remove all .pyc files and all made files listed in"
	@echo "                puf-files and cps-files targets"
	@echo "pytest      : generate report for and cleanup after pytest"
	@echo "cstest      : generate coding-style errors with pycodestyle"
	@echo "git-sync    : synchronize local, origin, and upstream Git repos"
	@echo "git-pr N=n  : create local pr-n branch containing upstream PR"
	@echo "puf-files   : make each of the following files:"
	@echo "                puf.csv"
	@echo "                growfactors.csv"
	@echo "                puf_weights.csv.gz"
	@echo "                puf_ratios.csv"
	@echo "cps-files   : make each of the following files:"
	@echo "                cps.csv.gz"
	@echo "                growfactors.csv"
	@echo "                cps_weights.csv.gz"
	@echo "                cps_benefits.csv.gz"
	@echo "all         : make both puf-files and cps-files"

.PHONY=clean
clean:
	@find . -name *pyc -exec rm {} \;
ifeq ($(CSV),x)
	@echo "The CSV=x option logic is not yet implemented"
#	@rm -f $(MADE_FILES)
else
	@echo "No CSV=x option used so skip removal of all made files"
endif

define pytest-cleanup
find . -name *cache -maxdepth 1 -exec rm -r {} \;
endef

.PHONY=pytest
pytest:
	@pytest -n4
	@$(pytest-cleanup)

.PHONY=cstest
cstest:
	pycodestyle .

.PHONY=git-sync
git-sync:
	@./gitsync

.PHONY=git-pr
git-pr:
	@./gitpr $(N)

.PHONY=puf-files
puf-files: puf_data/puf.csv \
           puf_stage1/growfactors.csv \
           puf_stage2/puf_weights.csv.gz \
           puf_stage3/puf_ratios.csv

puf_data/puf.csv: puf_data/finalprep.py \
                  puf_data/cps-matched-puf.csv
	cd puf_data ; python finalprep.py

puf_stage1/Stage_I_factors.csv: puf_stage1/stage1.py \
                                puf_stage1/CBO_baseline.csv \
                                puf_stage1/IRS_return_projection.csv \
                                puf_stage1/NC-EST2014-AGESEX-RES.csv \
                                puf_stage1/NP2014_D1.csv \
                                puf_stage1/SOI_estimates.csv \
                                puf_stage1/US-EST00INT-ALLDATA.csv
	cd puf_stage1 ; python stage1.py
# above recipe also makes puf_stage1/Stage_I_factors_transpose.csv
# above recipe also makes puf_stage1/Stage_II_targets.csv

puf_stage1/growfactors.csv: puf_stage1/factors_finalprep.py \
                            puf_stage1/Stage_I_factors.csv
	cd puf_stage1 ; python factors_finalprep.py

puf_stage2/puf_weights.csv.gz: puf_stage2/stage2.py \
                               puf_stage2/solve_lp_for_year.py \
                               puf_data/cps-matched-puf.csv \
                               puf_stage1/Stage_I_factors_transpose.csv \
                               puf_stage1/Stage_II_targets.csv
	cd puf_stage2 ; python stage2.py

puf_stage3/puf_ratios.csv: puf_stage3/stage3.py \
                           puf_stage3/stage3_targets.csv \
                           puf_data/cps-matched-puf.csv \
                           puf_stage1/growfactors.csv \
                           puf_stage2/puf_weights.csv.gz
	cd puf_stage3 ; python stage3.py

.PHONY=cps-files
cps-files: cps_data/cps.csv.gz \
           cps_stage1/stage_2_targets.csv \
           cps_stage2/cps_weights.csv.gz \
           cps_stage4/cps_benefits.csv.gz

cps_data/cps.csv.gz: cps_data/finalprep.py \
                     cps_data/cps_raw.csv.gz \
                     cps_data/adjustment_targets.csv \
                     cps_data/benefitprograms.csv
	cd cps_data ; python finalprep.py

cps_stage1/stage_2_targets.csv: cps_stage1/stage1.py \
                                cps_stage1/SOI_estimates.csv \
                                puf_stage1/Stage_I_factors.csv \
                                puf_stage1/Stage_II_targets.csv
	cd cps_stage1 ; python stage1.py

cps_stage2/cps_weights.csv.gz: cps_stage2/stage2.py \
                               cps_data/cps_raw.csv.gz \
                               puf_stage1/Stage_I_factors.csv \
                               cps_stage1/stage_2_targets.csv
	cd cps_stage2 ; python stage2.py

cps_stage4/cps_benefits.csv.gz: cps_stage4/rename_columns.py \
                                cps_stage4/extrapolation.py \
                                cps_stage4/growth_rates.csv \
                                cps_data/cps_raw.csv.gz \
                                cps_stage2/cps_weights.csv.gz
	cd cps_stage4 ; \
        python rename_columns.py && python extrapolation.py ; \
        rm -f ../cps_data/cps_raw_rename.csv.gz

.PHONY=all
all: puf-files cps-files
