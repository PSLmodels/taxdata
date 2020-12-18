import pandas as pd
from taxdata import cps
from taxdata import puf
from pathlib import Path

CUR_PATH = Path(__file__).resolve().parent
DATA_PATH = Path(CUR_PATH, "data")
CPS_YEAR = 2016

# create CPS tax units
print("Creating CPS tax units")
raw_cps = cps.create(DATA_PATH, exportpkl=False, cps_files=[CPS_YEAR], benefits=False)
# minor PUF prep
print("Cleaning up PUF")
puf2011 = pd.read_csv(Path(DATA_PATH, "puf2011.csv"))
raw_puf = puf.preppuf(puf2011, 2011)
raw_puf.to_csv(Path(DATA_PATH, "raw_puf.csv"))
print("Done!")
