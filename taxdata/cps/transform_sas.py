"""
Scripts to convert the SAS scripts used to process the .DAT format CPS file
to Python
"""
import pickle
from pathlib import Path
from .cps_meta import CPS_META_DATA


CUR_PATH = Path(__file__).resolve().parent


def find_section(sas):
    """
    Keep reading lines in the file until the line 'INPUT' is found.
    below this line is all of the information about where the variable is
    located in the DAT file
    """
    input_line = False
    while not input_line:
        line = sas.readline()
        split_line = line.split()
        # Account for new line values
        newline_check = len(split_line) == 0
        if not newline_check:
            if split_line[0] == "INPUT" and len(split_line) == 1:
                input_line = True


def parse_sas(sas):
    """
    Parse the SAS file to find start and end points for all variables
    """
    lines = {}
    # loop until you hit a blank line
    while True:
        # a value error will be thrown when you try and split the
        # line if you're at a blank line
        try:
            start, var, length = sas.readline().split()
        except ValueError:
            break
        start = int(start[1:]) - 1  # where in the line the variable starts
        split_len = length.split(".")
        try:
            # the actual length will be just the first part
            length = int(split_len[0])
        except ValueError:
            # some length inputs have a $ attached
            length = int(split_len[0][1:])
        end = start + length
        # the SAS scripts we're transforming indicating a float variable by
        # adding an integer after the . in the length variable. e.g. 8.2
        # means that the variable is 8 characters long, and has 2 decimals
        decimals = 0
        if split_len[1]:
            decimals = int(split_len[1])
        lines[var] = (start, end, decimals)

    return lines


def main():
    master_dict = {}
    for year in CPS_META_DATA.keys():
        # read in file text
        sas = Path(CUR_PATH, CPS_META_DATA[year]["sas_file"]).open("r")
        find_section(sas)
        # first section you'll hit is households
        household = parse_sas(sas)
        find_section(sas)
        # next is families
        family = parse_sas(sas)
        find_section(sas)
        # last is persons
        person = parse_sas(sas)
        sas.close()

        master_dict[year] = {"household": household, "family": family, "person": person}

    with Path(CUR_PATH, "master_cps_dict.pkl").open("wb") as f:
        pickle.dump(master_dict, f)


if __name__ == "__main__":
    main()
