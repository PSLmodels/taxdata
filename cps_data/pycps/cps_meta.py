"""
Holds all the CPS file metadata we need. Created to keep create.py clean
"""
import cpsmar2013
import cpsmar2014
import cpsmar2015
import cpsmar2016
import cpsmar2017
import cpsmar2018

CPS_META_DATA = {
    2013: {
        "dat_file": "asec2013_pubuse.dat",
        "create_func": cpsmar2013.create_cps
    },
    2014: {
        "dat_file": "asec2014_pubuse_tax_fix_5x8_2017.dat",
        "create_func": cpsmar2014.create_cps
    },
    2015: {
        "dat_file": "asec2015_pubuse.dat",
        "create_func": cpsmar2015.create_cps
    },
    2016: {
        "dat_file": "asec2016_pubuse_v3.dat",
        "create_func": cpsmar2016.create_cps
    },
    2017: {
        "dat_file": "asec2017_pubuse.dat",
        "create_func": cpsmar2017.create_cps
    },
    2018: {
        "dat_file": "asec2018_pubuse.dat",
        "create_func": cpsmar2018.create_cps
    }
}
