"""
This script creates the initial hashes for each stage 2 file
"""
import json
import hashlib
from pathlib import Path

CUR_PATH = Path(__file__).resolve().parent


def create_hashes(_file):
    """
    Create the hash values for each of the files in the stage 2 process
    """
    hashes = {}
    with open(Path(CUR_PATH, "data", _file), "rb") as f:
        hashes["data"] = hashlib.sha256(f.read()).hexdigest()
    if _file == "cps-matched-puf.csv":
        basepath = Path(CUR_PATH, "puf_stage2")
    else:
        basepath = Path(CUR_PATH, "cps_stage2")
    filenames = ["solver.jl", "dataprep.py", "stage2.py"]
    keynames = ["solver", "dataprep", "stage2"]
    for filename, key in zip(filenames, keynames):
        with open(Path(basepath, filename), "rb") as f:
            hashes[key] = hashlib.sha256(f.read()).hexdigest()
    return hashes


finalhashes = {}
finalhashes["puf"] = create_hashes("cps-matched-puf.csv")
finalhashes["cps"] = create_hashes("cps.csv.gz")
with open(Path(CUR_PATH, "datahashes.json"), "w") as f:
    json.dump(finalhashes, f, indent=4)
