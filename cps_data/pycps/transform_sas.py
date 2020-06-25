"""
Scripts to convert the SAS scripts used to process the .DAT format CPS file
to Python
"""
from pathlib import Path
from jinja2 import Template


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
            if split_line[0] == 'INPUT' and len(split_line) == 1:
                input_line = True


def create_section(sas):
    """
    Create a full section
    """
    line_format = 'record["{}"] = int(rec[{}:{}])\n'
    float_line = 'record["{}"] = float(rec[{}:{}] + "." + rec[{}:{}])\n'
    lines = []
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
        # float variables will have the number of decimals after the .
        float_var = split_len[1] != ""
        if not float_var:
            # file_str += line_format.format(var, start, end)
            lines.append(line_format.format(var, start, end))
        else:
            dem_len = int(split_len[1])
            end2 = end
            end -= dem_len
            lines.append(float_line.format(var, start, end, end, end2))

    # return file_str
    return lines


def main(sas_file, year, dat_file, template_path="template.txt"):

    def write_page(pathout, template_path, **kwargs):
        """
        Render the HTML template with the markdown text
        Parameters
        ----------
        pathout: path where the HTML file will be saved
        template_path: path for the HTML template
        Returns
        -------
        None
        """
        # read and render HTML template
        template_str = Path(template_path).open("r").read()
        template = Template(template_str, trim_blocks=True, lstrip_blocks=True)
        rendered = template.render(**kwargs)
        Path(pathout).write_text(rendered)

    # read in file text
    sas = Path(CUR_PATH, sas_file).open("r")
    find_section(sas)
    # first section you'll hit is households
    household = create_section(sas)

    find_section(sas)
    # next is families
    family = create_section(sas)

    find_section(sas)

    # last is persons
    person = create_section(sas)

    sas.close()

    pathout = Path(CUR_PATH, f"cpsmar{year}.py")  # .write_text(file_str)
    write_page(pathout, template_path, household=household, family=family,
               person=person, year=year, file_name=dat_file)


if __name__ == "__main__":
    main("cpsmar2013.sas", 2013, "asec2013_pubuse.dat")
    main("cpsmar2014t.sas", 2014, "asec2014_pubuse_tax_fix_5x8_2017.dat")
    main("cpsmar2015.sas", 2015, "asec2015_pubuse.dat")
