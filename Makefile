# GNU Makefile that documents and automates common development operations
#              using the GNU make tool (version >= 3.81)
# USAGE: taxdata$ make [TARGET]

FILES_TO_MAKE = growfactors.csv

.PHONY=help
help:
	@echo "USAGE: make [TARGET]"
	@echo "TARGETS:"
	@echo "help       : show help message"
	@echo "clean      : remove all made files (see 'all' file list)"
	@echo "all        : make each of the following files:"
	@echo "               growfactors.csv"
	@echo "pytest     : generate report for and cleanup after pytest"
	@echo "cstest     : generate coding-style errors with pycodestyle"
	@echo "git-sync   : synchronize local, origin, and upstream Git repos"
	@echo "git-pr N=n : create local pr-n branch containing upstream PR"


.PHONY=clean
clean:
	@find . -name *pyc -exec rm {} \;
	@rm -f $(FILES_TO_MAKE)

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
