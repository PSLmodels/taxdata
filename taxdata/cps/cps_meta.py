"""
Holds all the CPS file metadata we need. Created to keep create.py clean
"""

C_TAM_YEARS = [2013, 2014, 2015]  # years we have C-TAM imputations for

CPS_META_DATA = {
    2013: {"dat_file": "asec2013_pubuse.dat", "sas_file": "cpsmar2013.sas"},
    2014: {
        "dat_file": "asec2014_pubuse_tax_fix_5x8_2017.dat",
        "sas_file": "cpsmar2014t.sas",
    },
    2015: {"dat_file": "asec2015_pubuse.dat", "sas_file": "cpsmar2015.sas"},
    2016: {"dat_file": "asec2016_pubuse_v3.dat", "sas_file": "cpsmar2016.sas"},
    2017: {"dat_file": "asec2017_pubuse.dat", "sas_file": "cpsmar2017.sas"},
    2018: {"dat_file": "asec2018_pubuse.dat", "sas_file": "cpsmar2018.sas"},
}
