# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem
from PySide import QtGui
from copy import copy as copy
import math
import re

class Form(QtGui.QDialog): # {{{
    """ 
    Pick output filename to save
    """

    def __init__(self, initial_filename, file_contents): # {{{
        self.initial_filename = initial_filename
        self.file_contents = file_contents
        super(Form, self).__init__()
        # }}}
        
    def makeUI(self): # {{{
        filename, _ = QtGui.QFileDialog.getSaveFileName(
            self,
            'Save File As',
            self.initial_filename,
            "Nastran Bulk Data Files (*.bdf *.nas *.dat)"
        )
        write_include_file_out(filename, self.file_contents)
        self.close()
    # }}}
# }}}

def write_include_file_out(filename, file_contents): # {{{
    """
    write out the contents of the list of lines in file_contents
    to the file called filename
    """
    with open(filename, mode='wt', encoding='utf-8') as bdf:
        bdf.write('\n'.join(file_contents))
    return
# }}}

def get_optimal_short_form_float(x): # {{{
    """ Get optimal way to print the number in 8 characters
    """
    x_raw_string = "{:50.100f}".format(x)
    # check for zero
    if x == 0.0: 
        x_str = " 0.0    "
        return x_str

    # check for power of 10
    if math.log(abs(round(x,7)),10).is_integer(): 
        x_str = "1." + "+" + str(int(math.log(round(x,7),10)))
        x_str += " " * (8 - len(x_str))
        return x_str

    # get the order of magnitude of the point coordinates
    order = math.ceil(math.log(abs(x),10))
    if order == 0:
        order_of_order = 0
    elif order > 0:
        order_of_order = math.ceil(math.log(abs(order+1),10))
    elif order < 0:
        order_of_order = math.ceil(math.log(abs(order-1),10))

    # get optimal number of data characters allowed
    if x > 0: # positive
        if order >= 7:
            reduced_number = x/(10**(order-1))
            reduced_number = round(reduced_number,6)
            format_string = "{:1." + str(5 - order_of_order) + "f}"
            reduced_number = format_string.format(reduced_number)
            x_str = reduced_number + "+" + str(order)
        elif order < -2:
            reduced_number = x/(10**(order-1))
            reduced_number = round(reduced_number,6)
            format_string = "{:1." + str(5 - order_of_order) + "f}"
            reduced_number = format_string.format(reduced_number)
            x_str = reduced_number + str(order)
        else: # this means just use the raw number
            x = round(x,7)
            format_string = "{:"
            lower_order = math.floor(math.log(abs(x),10))
            format_string += str(max(order,0))
            format_string += "."
            if order == lower_order:
                format_string += str(6 - max(order,0))
            else:
                format_string += str(7 - max(order,0))
            format_string += "f}"
            if order > 0:
                x_str = format_string.format(x)
            else:
                x_str = format_string.format(x)[1:]
    else: # negative
        if order >= 6:
            reduced_number = x/(10**(order-1))
            reduced_number = round(reduced_number,6)
            format_string = "{:1." + str(4 - order_of_order) + "f}"
            reduced_number = format_string.format(reduced_number)
            x_str = reduced_number + "+" + str(order)
        elif order < -2:
            reduced_number = x/(10**(order-1))
            reduced_number = round(reduced_number,6)
            format_string = "{:1." + str(4 - order_of_order) + "f}"
            reduced_number = format_string.format(reduced_number)
            x_str = reduced_number + str(order)
        else:
            format_string = "{:"
            format_string += str(max(order,0))
            format_string += "."
            # check if is a power of 10
            if math.log(abs(x),10).is_integer():
                format_string += str(5 - max(order,0))
            else:
                format_string += str(6 - max(order,0))
            format_string += "f}"
            if order > 0:
                x_str = format_string.format(x)
            else:
                x_str = format_string.format(x)[0] + format_string.format(x)[2:]

    # check that x_str is the right length
    if len(x_str) != 8:
        print(x_str)
        print(x)
        print(math.log(x,10))
        raise ValueError("printed value string is wrong length!")

    return x_str
    # }}}

def is_valid_nastran_real(x): #{{{
    """
    Return True if x is a valid nastran real as a string
    """
    x = re.sub(r"\s", "", x)
    has_number_before_decimal = r"^[+|-]?[0-9]{1,}\.[0-9]{0,}E?[-|+]?[0-9]{0,}$"
    has_number_after_decimal = r"^[+|-]?\.[0-9]{1,}E?[-|+]?[0-9]{0,}$"
    if re.match(has_number_before_decimal,x) is not None:
        return True
    elif re.match(has_number_after_decimal,x) is not None:
        return True
    else:
        return False
#}}}

def main(): #{{{
    """ 
    * User clicks on nodeset
    * detects syntax from name of nodeset
    * opens file save dialog to save inclue with a name to a location
    """
    nodeset_objects = [] 
    for obj in Gui.Selection.getSelectionEx():
        if obj.TypeName == "Fem::FemSetNodesObject":
           nodeset_objects.append(obj.Object)

    if len(nodeset_objects) != 1:
        raise ValueError("as of 2021.10.24, only one nodeset may be selected.")

    nodeset_objects = nodeset_objects[0]
    nodeset_name = nodeset_objects.Label
    nodeset_nodes = nodeset_objects.Nodes

    # see what kind of thing the nodeset wants to be
    if "SPC1" in nodeset_name:
        #{{{
        # The correct format for the name is 
        # Name: SPC1_SID_C
        SPC1_index = nodeset_name.find("SPC1")
        trimmed_string = nodeset_name[SPC1_index:]
        split_name = trimmed_string.split("_")
        # are there three fields?
        if len(split_name) != 3:
            raise ValueError("correct format is Name: SPC1_SID_C")
        # is the second field an integer?
        if re.match(r'[0-9]+$', split_name[1]) is None:
            raise ValueError("SPC Set ID must be an integer")
        # is the third field a unique set of numbers 1, 2, 3, 4, 5, and 6?
        if len(split_name[2]) != len(set(split_name[2])):
            raise ValueError("Repeated component numbers present in field 3")
        if re.match(r'[1-6]*$', split_name[2]) is None:
            raise ValueError("SPC1 components contain values other than 1-6")
        # if we're here, we should be all good
        SID = split_name[1]
        components = split_name[2]
        SPC1_include = []
        for node in nodeset_nodes:
            line = "SPC1," + SID + "," + components + "," + str(node)
            SPC1_include.append(line)
        # get exportable filename
        # does the label contain a ':'
        if ":" in nodeset_name:
            file_name = nodeset_name[:nodeset_name.find(":")]
        else:
            file_name = "constraint_file.bdf"
        form = Form(file_name, SPC1_include)
        form.makeUI()

        # write out file
        #}}}
    elif "FORCE" in nodeset_name:
        # The correct format for the name is 
        # Name: SPC1_SID_C
        FORCE_index = nodeset_name.find("FORCE")
        trimmed_string = nodeset_name[FORCE_index:]
        split_name = trimmed_string.split("_")
        # are there six fields?
        if len(split_name) != 6:
            s = "correct formatn is Name: FORCE_LoadsetID_scale_vx_vy_vz"
            raise ValueError(s)
        if re.match(r"^[0-9]+$",split_name[1]) is None:
            raise ValueError("Force LoadSetID is not an integer")
        if not is_valid_nastran_real(split_name[2]):
            raise ValueError("Force Scaling Factor is not a valid nastran real")
        if not is_valid_nastran_real(split_name[3]):
            raise ValueError("Force COmponent in X is not a valid nastran real")
        if not is_valid_nastran_real(split_name[4]):
            raise ValueError("Force COmponent in Y is not a valid nastran real")
        if not is_valid_nastran_real(split_name[5]):
            raise ValueError("Force COmponent in Z is not a valid nastran real")
        # if we're here, we should be all good
        SID = split_name[1]
        scale = split_name[2]
        vx = split_name[3]
        vy = split_name[4]
        vz = split_name[5]
        FORCE_include = []
        for node in nodeset_nodes:
            line="FORCE,"+SID+","+str(node)+",,"+scale+","+vx+","+vy+","+vz
            FORCE_include.append(line)
        # get exportable filename
        # does the label contain a ':'
        if ":" in nodeset_name:
            file_name = nodeset_name[:nodeset_name.find(":")]
        else:
            file_name = "constraint_file.bdf"
        form = Form(file_name, FORCE_include)
        form.makeUI()
    else:
        s = "Only SPC1 and FORCE cards supported as of 2021.10.14"
        raise ValueError(s)
# }}}

if __name__ == '__main__':
   main() 
