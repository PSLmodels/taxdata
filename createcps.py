from taxdata.cps import create
from pathlib import Path


CUR_PATH = Path(__file__).resolve().parent

create(
    datapath=Path(CUR_PATH, "data"),
    exportcsv=False,
    exportpkl=True,
    exportraw=False,
    validate=False,
    benefits=True,
    verbose=True,
)
