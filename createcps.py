import subprocess
from taxdata import cps
from pathlib import Path


CUR_PATH = Path(__file__).resolve().parent
DATA_PATH = Path(CUR_PATH, "data")

raw_cps = cps.create(
    datapath=DATA_PATH,
    exportcsv=False,
    exportpkl=True,
    exportraw=False,
    validate=False,
    benefits=True,
    verbose=True,
)
print("Exporting raw file")
raw_output_path = Path(DATA_PATH, "cps_raw.csv")
raw_cps.to_csv(raw_output_path)
subprocess.check_call(["gzip", "-nf", str(raw_output_path)])
# clean up and export final file
print("Cleaning file")
final_cps = cps.finalprep(raw_cps)
final_output_path = Path(DATA_PATH, "cps.csv")
final_cps.to_csv(final_output_path, index=False)
subprocess.check_call(["gzip", "-nf", str(final_output_path)])
print("Done!")
