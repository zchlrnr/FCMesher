import os
import re
import pathlib
def mystran_f06_reader(*args):
    """
    It is the goal of this subroutine to read in a f06 file, and return all 
    pertinant results accordingly.
    """
    # look around, get list of the things here
    things_here = []
    basepath = '.'
    with os.scandir(basepath) as entries:
        for entry in entries:
            things_here.append(entry.name)

    # inspect user inputs 
    if len(args) == 0:
        # need to look around for an f06 file in stuff here
        # get f06 files here
        f06_files_here = []
        for name in things_here:
            if re.match(r".*\.f06$", name) is not None:
                f06_files_here.append(name)
        if len(f06_files_here) == 0:
            s = "No f06 files found in" + os.getcwd()
            raise ValueError(s)
    elif len(args) == 1:
        argument = args[0]
        # check that it's a string
        if not isinstance(argument, str):
            raise ValueError("Argument passed in is not a string")
        # check that it ends in f06 or F06
        if not argument.lower().endswith("f06"):
            raise ValueError("argument passed in does not end in f06")
        # check that the file is here
        if not pathlib.Path(argument).is_file():
            raise ValueError("argument passed in isn't a file or doesn't exist")
        # if it passes all these, it's probably okay
        f06_filename = argument
    else:
        s = "Too many arguments passed into mystran_f06_reader"
        raise ValueError(s)

    # read in the f06 file
    with open(f06_filename) as f:
        f06 = f.readlines()

    # is it a linear static run?
    is_linearstatic = False
    # SOL 101, SOL 1, SOL STATIC, SOL STATICS
    for count, line in enumerate(f06):
        if re.match(r'(?i)^SOL 1\s*$', line):
            is_linearstatic = True
            break
        elif re.match(r'(?i)^SOL 101\s*$', line):
            is_linearstatic = True
            break
        elif re.match(r'(?i)^SOL STATIC\s*$', line):
            is_linearstatic = True
            break
        elif re.match(r'(?i)^SOL STATICS\s*$', line):
            is_linearstatic = True
            break
    if is_linearstatic == False:
        raise ValueError("As of 2021.10.31, only know how to do linear statics")

    # what things are requested out?
    acceleration_out = False
    displacement_out = False
    elforce_out = False
    gpforce_out = False
    spcforce_out = False
    stress_out = False
    strain_out = False
    for count, line in enumerate(f06):
        if re.match(r'(?i)^\s*accel(eration)?(\(.*\))?\s*=', line):
            acceleration_out = True
        elif re.match(r'(?i)^\s*displ(acement)?(\(.*\))?\s*=', line):
            displacement_out = True
        elif re.match(r'(?i)^\s*(el)?force(\(.*\))?\s*=', line):
            elforce_out = True
        elif re.match(r'(?i)^\s*gpforce(\(.*\))?\s*=', line):
            gpforce_out = True
        elif re.match(r'(?i)^\s*spcforce(\(.*\))?\s*=', line):
            spcforce_out = True
        elif re.match(r'(?i)^\s*stress(\(.*\))?\s*=', line):
            stress_out = True
        elif re.match(r'(?i)^\s*strain(\(.*\))?\s*=', line):
            strain_out = True

    if displacement_out:
        # get line where D I S P L A C E M E N T S starts
        disp_start_index = 0
        for count, line in enumerate(f06):
            if re.match(r'^.*D I S P L A C E M E N T S.*$', line):
                disp_start_index = count
        # get line where D I S P L A C E M E N T S ends
        disp_end_index = disp_start_index
        for count, line in enumerate(f06[disp_start_index:]):
            if '------' in line:
                disp_end_index = count + disp_start_index
                break
        # consolidate displacement data chunk
        disp_data_chunk = f06[disp_start_index+4:disp_end_index]
        displacement_data = {}
        for line in disp_data_chunk:
            data_line = re.sub('\s+', ',', line)
            data_line = re.sub('^,', '', data_line)
            data_line = re.sub(',$', '', data_line)
            data = data_line.split(",")
            NID = int(data[0])
            CID = int(data[1])
            T1 = float(data[2])
            T2 = float(data[3])
            T3 = float(data[4])
            R1 = float(data[5])
            R2 = float(data[6])
            R3 = float(data[7])
            # Coordinate ID, Displacements in X, Y, Z, Rotations about X, Y, Z
            displacement_data[NID] = (CID, T1, T2, T3, R1, R2, R3)
        print(displacement_data)
        

def main():
    filename =\
    "/home/vonbraun/Programs/mystran/Mystran_Test_Models/"+\
    "Tet10_Training/sol_101/fine_02/Example_output.F06"

    mystran_f06_reader(filename)
    #mystran_f06_reader()

if __name__ == "__main__":
    main()

