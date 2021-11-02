import os
import re
import pathlib
from copy import copy as copy
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

    # is it a linear static run? {{{
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
    #}}}

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

    if displacement_out: # {{{
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
    #}}}

    if stress_out: #{{{
        # this will be far harder.
        # results will be different for the different element/property types
        stress_indices = []
        for count, line in enumerate(f06):
            if re.match(r'^.*S T R E S S E S.*$', line):
                stress_indices.append(count)
        # stress_indices are now a list of line numbers at which point we 
        # have S T R E S S E S appear. Need to loop through them
        for stress_begin_index in stress_indices:
            # get line where S T R E S S E S ends
            stress_end_index = copy(stress_begin_index)
            for count, line in enumerate(f06[stress_begin_index:]):
                if '------' in line:
                    stress_end_index = count + stress_end_index
                    break
            stress_data_chunk = f06[stress_begin_index:stress_end_index]
            # need to get the element type
            mode = 'center'
            e_type = ''
            if re.match('^.*Q U A D 4.*$',stress_data_chunk[1]) is not None:
                e_type = 'QUAD4'
            elif re.match('^.*T R I A 3.*$',stress_data_chunk[1]) is not None:
                e_type = 'TRIA3'
            elif re.match('^.*T E T R A.*$',stress_data_chunk[1]) is not None:
                e_type = 'TETRA'
            else:
                s = "Unknown element type produced stress results"
                raise ValueError(s)
            # if the element type is CQUAD
            # edge case will exist if only one element has data out
            # hope that never happens.
            if e_type == 'QUAD4':
                e1_match_stat = re.match('^.*CENTER.*$', stress_data_chunk[6])
                e2_match_stat = re.match('^.*CENTER.*$', stress_data_chunk[9])
                if None == e1_match_stat and None == e2_match_stat:
                    # in corner mode
                    mode = 'corner'
            # write conditions to deal with both corner mode and center mode
            stress_data = []
            if mode == 'center':
                if e_type == 'QUAD4': 
                    for count, line in enumerate(stress_data_chunk):
                        if re.match('^.*CENTER.*$', line) is not None:
                            data_line_1 = re.sub('\s+', ',', line)
                            data_line_1= re.sub('^,', '', data_line_1)
                            data_line_1 = re.sub(',$', '', data_line_1)
                            data_line_1 = data_line_1.split(',')
                            data_line_2 = re.sub('\s+', ',',\
                                          stress_data_chunk[count+1])
                            data_line_2= re.sub('^,', '', data_line_2)
                            data_line_2 = re.sub(',$', '', data_line_2)
                            data_line_2 = data_line_2.split(',')
                            EID = int(data_line_1[0])
                            FD1 = float(data_line_1[2])
                            S_x_1 = float(data_line_1[3])
                            S_y_1 = float(data_line_1[4])
                            S_xy_1 = float(data_line_1[5])
                            FD2 = float(data_line_2[0])
                            S_x_2 = float(data_line_2[1])
                            S_y_2 = float(data_line_2[2])
                            S_xy_2 = float(data_line_2[3])
                            # EID, e_type, Fiber Distance, Sx, Sy, Sxy
                            L1 = [EID, e_type, FD1, S_x_1, S_y_1, S_xy_1]
                            L2 = [EID, e_type, FD2, S_x_2, S_y_2, S_xy_2]
                            stress_data.append(L1)
                            stress_data.append(L2)
                elif e_type == 'TRIA3':
                    for count, line in enumerate(stress_data_chunk):
                        if re.match('^.*CENTER.*$', line) is not None:
                            data_line_1 = re.sub('\s+', ',', line)
                            data_line_1= re.sub('^,', '', data_line_1)
                            data_line_1 = re.sub(',$', '', data_line_1)
                            data_line_1 = data_line_1.split(',')
                            data_line_2 = re.sub('\s+', ',',\
                                          stress_data_chunk[count+1])
                            data_line_2= re.sub('^,', '', data_line_2)
                            data_line_2 = re.sub(',$', '', data_line_2)
                            data_line_2 = data_line_2.split(',')
                            EID = int(data_line_1[0])
                            FD1 = float(data_line_1[2])
                            S_x_1 = float(data_line_1[3])
                            S_y_1 = float(data_line_1[4])
                            S_xy_1 = float(data_line_1[5])
                            FD2 = float(data_line_2[0])
                            S_x_2 = float(data_line_2[1])
                            S_y_2 = float(data_line_2[2])
                            S_xy_2 = float(data_line_2[3])
                            # EID, e_type, Fiber Distance, Sx, Sy, Sxy
                            L1 = [EID, e_type, FD1, S_x_1, S_y_1, S_xy_1]
                            L2 = [EID, e_type, FD2, S_x_2, S_y_2, S_xy_2]
                            stress_data.append(L1)
                            stress_data.append(L2)
                elif e_type == 'TETRA':
                    for count, line in enumerate(stress_data_chunk[4:]):
                        data_line = re.sub('\s+', ',', line)
                        data_line = re.sub('^,', '', data_line)
                        data_line = re.sub(',$', '', data_line)
                        data_line = data_line.split(',')
                        EID = int(data_line[0])
                        Sxx = float(data_line[1])
                        Syy = float(data_line[2])
                        Szz = float(data_line[3])
                        Sxy = float(data_line[4])
                        Syz = float(data_line[5])
                        Szx = float(data_line[6])
                        # EID, e_type, Sxx, Syy, Szz, Sxy, Szx
                        L = [EID, e_type, Sxx, Syy, Szz, Sxy, Sxy]
                        stress_data.append(L)
            else:
                s = "As of 2021.11.02, corner stress reading not written yet."
                raise ValueError(s)
            for i in stress_data:
                print(i)
    #}}}
        
def main():
    testbed_location = "/home/vonbraun/Programs/mystran/FCMesher_F06_testbed"
    # get it able to read centers first
    tet_filename_center = testbed_location +\
    "/TETRA/center_stress/Example_output.F06"
    mystran_f06_reader(tet_filename_center)
    tria_filename_center = testbed_location +\
    "/CTRIA3/centered_stresses/CTRIA3_centered_stress.F06"
    #mystran_f06_reader(tria_filename_center)
    quad_filename_center= testbed_location +\
    "/CQUAD4/centered_stresses/all_together_center_stresses.F06"
    #mystran_f06_reader(quad_filename_center)

    # get it able to read corners (only really does anything for QUAD4 elements
    # (thank GOD)
    tet_filename_center = testbed_location +\
    "/TETRA/corner_stress/Example_output.F06"
    #mystran_f06_reader(tet_filename_center)
    tria_filename_center = testbed_location +\
    "/CTRIA3/corner_stresses/CTRIA3_centered_stress.F06"
    #mystran_f06_reader(tria_filename_center)
    quad_filename_center= testbed_location +\
    "/CQUAD4/corner_stresses/all_together_corner_stress.F06"
    #mystran_f06_reader(quad_filename_center)

if __name__ == "__main__":
    main()

