# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem
from PySide import QtGui
from copy import copy as copy
import math

class Form(QtGui.QDialog): # {{{
    """ Pick output filename to save
    """
    def __init__(self): # {{{
        super(Form, self).__init__()
        self.setModal(True)
        self.makeUI()
        # }}}
        
    def makeUI(self): # {{{
        filename, _ = QtGui.QFileDialog.getSaveFileName(
            self,
            'Save File As',
            'Example_output.bdf',
            "Nastran Bulk Data Files (*.bdf *.nas *.dat)"
        )
        main(filename)
        self.close()
    # }}}
# }}}

def get_N2E(E2N): # {{{
    """ Turns the E2N around, giving a dict of N2E
    """
    N2E = {}
    for EID, Element in E2N.items():
        # go through nodes in every element
        for NID in Element:
            # if the node's not in N2E yet, prepare for it to be
            if NID not in N2E:
                N2E[NID] = []
            # store the EID with that node ID we're on
            N2E[NID].append(EID)
    return N2E
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
    print(x)
    print(round(x,7))
    if round(x,7) == 0:
        x_str = " 0.0    "
        return x_str
    elif math.log(abs(round(x,7)),10).is_integer(): 
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

def create_bulkdata_list(nodes, E2N, E2T, E2P, P2M, P2T, M2T): #{{{
    """ Create giant list, with each entry being a line 
    - Assume short format 
    """
    bulkdata = []
    bulkdata.append("BEGIN BULK")
    bulkdata.append("")

    element_type_to_dimension = {1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:3, 8:0,\
    9:0, 10:0, 11:0, 12:0, 13:1, 14:3, 15:2, 16:2, 17:1, 18:2, 19:3, 20:2, 21:2}    

    # Properties
    for PID in P2T.keys(): # {{{
        if P2T[PID] == 0:
            # figure out what kind of element PID is applied to
            # get element IDs with current PID, and their types
            EIDs_with_this_PID = []
            element_types = []
            for element in E2P:
                if E2P[element] == PID:
                    EIDs_with_this_PID.append(element)
                    element_types.append(E2T[element])
            type_IDs = list(set(element_types))
            # if there's only one type, okay
            if len(type_IDs) != 1:
                # if there's more than one type, throw error.
                # I don't want to deal with that right now.
                s = "More than one element type not allowed at a time (yet)"
                raise ValueError(s)
            # get type dimension
            dimension = element_type_to_dimension[type_IDs[0]]
            if dimension == 0:
                s = "Elements of dimension 0 not supported (yet)" 
                raise ValueError(s)
            elif dimension == 1:
                s = "Elements of dimension 1 not supported (yet)" 
                raise ValueError(s)
            elif dimension == 2:
                s = ""
                s += "PSHELL  "
                s += str(int(PID))
                s += " " * (8 - len(str(int(PID))))
                s += str(int(P2M[PID]))
                s += " " * (8 - len(str(int(P2M[PID]))))
                bulkdata.append(s)
            elif dimension == 3:
                s = ""
                s += "PSOLID  "
                s += str(int(PID))
                s += " " * (8 - len(str(int(PID))))
                s += str(int(P2M[PID]))
                s += " " * (8 - len(str(int(P2M[PID]))))
                bulkdata.append(s)
        else:
            s = "As of 2021.10.16, non default property types not supported"
            raise ValueError(s)
    # }}}
    bulkdata.append("")

    # Materials
    for MID in M2T.keys(): # {{{
        if M2T[MID] == 0:
            # figure out what kind of property MID is applied to
            properties_with_this_material = []
            for PID in P2M.keys():
                if MID == P2M[PID]:
                    properties_with_this_material.append(PID)
            # if number of properties with this material is greater than 1, no bueno
            if len(properties_with_this_material) != 1:
                s = "More than one property using a material not allowed at this time"
                raise ValueError(s)
            PID = properties_with_this_material[0]
            # now need to get the elements with this property
            EIDs_with_this_PID = []
            element_types = []
            for element in E2P:
                if E2P[element] == PID:
                    EIDs_with_this_PID.append(element)
                    element_types.append(E2T[element])
            type_IDs = list(set(element_types))
            # if there's only one type, okay
            if len(type_IDs) != 1:
                # if there's more than one type, throw error.
                # I don't want to deal with that right now.
                s = "More than one element type not allowed at a time (yet)"
                raise ValueError(s)
            # get type dimension
            dimension = element_type_to_dimension[type_IDs[0]]
            if dimension == 0:
                s = "Elements of dimension 0 not supported (yet)" 
                raise ValueError(s)
            elif dimension == 1:
                s = "Elements of dimension 1 not supported (yet)" 
                raise ValueError(s)
            elif dimension == 2:
                s = ""
                s += "MAT1    "
                s += str(int(MID))
                s += " " * (8 - len(str(int(MID))))
                bulkdata.append(s)
            elif dimension == 3:
                s = ""
                s += "MAT1    "
                s += str(int(MID))
                s += " " * (8 - len(str(int(MID))))
                bulkdata.append(s)
        else:
            s = "As of 2021.10.16, non default material types not supported"
            raise ValueError(s)
    # }}} 
    bulkdata.append("")

    # Elements (assuming short format for now)
    for e in E2N: # {{{
        e_type = E2T[e]
        property_ID =  E2P[e]
        N_nodes_in_elm = len(E2N[e])
        if e_type == 7:   # CHEXA
            if N_nodes_in_elm == 8:
                s = "CHEXA   "
                s += str(int(e)) + " " * (8 - len(str(int(e))))
                s += str(int(E2P[e])) + " " * (8 - len(str(int(E2P[e]))))
                s += str(int(E2N[e][0])) + " " * (8 - len(str(int(E2N[e][0]))))
                s += str(int(E2N[e][1])) + " " * (8 - len(str(int(E2N[e][1]))))
                s += str(int(E2N[e][2])) + " " * (8 - len(str(int(E2N[e][2]))))
                s += str(int(E2N[e][3])) + " " * (8 - len(str(int(E2N[e][3]))))
                s += str(int(E2N[e][4])) + " " * (8 - len(str(int(E2N[e][4]))))
                s += str(int(E2N[e][5])) + " " * (8 - len(str(int(E2N[e][5]))))
                bulkdata.append(s)
                s = " " * 8
                s += str(int(E2N[e][6])) + " " * (8 - len(str(int(E2N[e][6]))))
                s += str(int(E2N[e][7])) + " " * (8 - len(str(int(E2N[e][7]))))
                bulkdata.append(s)
            else:
                s = "As of 2021.10.16, only 8 noded CHEXA elements supported"
                raise ValueError(s)
        elif e_type == 15:
            # should be impossible to get here without being a 4 noded QUAD.
            # No checks needed
            s = "CQUAD4  "
            s += str(int(e)) + " " * (8 - len(str(int(e))))
            s += str(int(E2P[e])) + " " * (8 - len(str(int(E2P[e]))))
            s += str(int(E2N[e][0])) + " " * (8 - len(str(int(E2N[e][0]))))
            s += str(int(E2N[e][1])) + " " * (8 - len(str(int(E2N[e][1]))))
            s += str(int(E2N[e][2])) + " " * (8 - len(str(int(E2N[e][2]))))
            s += str(int(E2N[e][3])) + " " * (8 - len(str(int(E2N[e][3]))))
            bulkdata.append(s)
        elif e_type == 19:
            if N_nodes_in_elm == 10:
                s = "CTETRA  "
                s += str(int(e)) + " " * (8 - len(str(int(e))))
                s += str(int(E2P[e])) + " " * (8 - len(str(int(E2P[e]))))
                s += str(int(E2N[e][0])) + " " * (8 - len(str(int(E2N[e][0]))))
                s += str(int(E2N[e][1])) + " " * (8 - len(str(int(E2N[e][1]))))
                s += str(int(E2N[e][2])) + " " * (8 - len(str(int(E2N[e][2]))))
                s += str(int(E2N[e][3])) + " " * (8 - len(str(int(E2N[e][3]))))
                s += str(int(E2N[e][4])) + " " * (8 - len(str(int(E2N[e][4]))))
                s += str(int(E2N[e][5])) + " " * (8 - len(str(int(E2N[e][5]))))
                bulkdata.append(s)
                s = " " * 8
                s += str(int(E2N[e][6])) + " " * (8 - len(str(int(E2N[e][6]))))
                s += str(int(E2N[e][7])) + " " * (8 - len(str(int(E2N[e][7]))))
                s += str(int(E2N[e][8])) + " " * (8 - len(str(int(E2N[e][8]))))
                s += str(int(E2N[e][9])) + " " * (8 - len(str(int(E2N[e][9]))))
                bulkdata.append(s)
            else:
                s = "As of 2021.10.17, only 10 noded CTETRA elements supported"
                raise ValueError(s)
        else:
            s = "AS of 2021.10.16, only types 7, 5, and 19 supported."
            raise ValueError(s)
    # }}}
    bulkdata.append("")

    # Grids
    for n in nodes.keys(): # {{{
        s = "GRID    "
        s += str(int(n)) + " " * (8 - len(str(int(n))))
        s += " " * 8
        # get the point coordinates
        x = nodes[n][0]
        y = nodes[n][1]
        z = nodes[n][2]

        # turn these into the most efficient short form numbers
        x_str = get_optimal_short_form_float(x)
        y_str = get_optimal_short_form_float(y)
        z_str = get_optimal_short_form_float(z)

        # append coords to the string
        s += x_str
        s += y_str
        s += z_str

        bulkdata.append(s) 
     # }}}
    bulkdata.append("ENDDATA")
    return bulkdata
    # }}}

def get_data_from_mesh_objects(mesh_objects): # {{{
    """
    Bug observed on 2021.10.24:
        If mesh does not have compactly numbered nodes, this crushes its numbering
    """
    # get 'data' from mesh objects
    data = []
    for i in range(len(mesh_objects)):
        data.append({})
    for mesh_number, mesh in enumerate(mesh_objects): 
        # preallocate popualted data structures
        nodes = {}  # Node ID to location
        E2N = {}    # Element to Node ID
        E2T = {}    # Element to Type ID
        E2P = {}    # Element to Property ID
        P2M = {}    # Property to Material ID
        # get nodes for this mesh 
        #NID = max(nodes.keys(), default=0) # Node ID
        # not sure why I was doing that.^^
        # that results in the 2021.10.24 bug.
        for node in mesh.Nodes:
            #NID += 1
            NID = node
            nodes[NID] = list(mesh.getNodeById(node))
        # get E2N, E2T, E2P, and P2M for this mesh
        if mesh.EdgeCount != 0: # {{{
            s = "Edges not supported as of 2021.10.16"
            print(s)
            # }}}
        if mesh.TriangleCount != 0: # {{{
            s = "Triangles not supported as of 2021.10.16"
            print(s)
            #}}}
        if mesh.QuadrangleCount != 0: # Type 15 {{{
            EID = max(E2N.keys(), default=0)        # Element ID
            PID = max(E2P.keys(), default=0) + 1    # Property ID
            MID = max(P2M.keys(), default=0) + 1    # Material ID
            for face in mesh.Faces:
                # if it's 4 noded, it's a QUAD4 element
                if len(mesh.getElementNodes(face)) == 4:
                    EID += 1
                    # un-salome'ifying
                    OG = list(mesh.getElementNodes(face))    # original order
                    E2N[EID] = [OG[0], OG[3], OG[2], OG[1]]  # correct order
                    E2N[EID] = list(mesh.getElementNodes(face))
                    E2T[EID] = 15
                    E2P[EID] = PID
                    P2M[PID] = MID
            # }}}
        if mesh.HexaCount != 0:       # Type 7 {{{
            EID = max(E2N.keys(), default=0)        # Element ID
            PID = max(E2P.keys(), default=0) + 1    # Property ID
            MID = max(P2M.keys(), default=0) + 1    # Material ID
            for volume in mesh.Volumes:
                # if it's 8 noded, it's a CHEXA element with 8 nodes
                if len(mesh.getElementNodes(volume)) == 8:
                    EID += 1
                    # un-salome'ifying
                    OG = list(mesh.getElementNodes(volume))
                    E2N[EID] = \
                    [OG[6], OG[7], OG[4], OG[5], OG[2], OG[3], OG[0], OG[1]]
                    E2T[EID] = 7
                    E2P[EID] = PID
                    P2M[PID] = MID
                else:
                    s = "As of 2021.10.17, CHEXA 20 elements are not supported."
                    raise ValueError(s)
            # }}}
        if mesh.TetraCount != 0:      # Type 19 {{{
            EID = max(E2N.keys(), default=0)        # Element ID
            PID = max(E2P.keys(), default=0) + 1    # Property ID
            MID = max(P2M.keys(), default=0) + 1    # Material ID
            for volume in mesh.Volumes:
                # if it's 10 noded, it's a CTETRA element with 10 nodes
                if len(mesh.getElementNodes(volume)) == 10:
                    EID += 1
                    # un-salome'ifying
                    OG = list(mesh.getElementNodes(volume))
                    E2N[EID] = [OG[3], OG[2], OG[0], OG[1], OG[9], OG[6],\
                                OG[7], OG[8], OG[5], OG[4]]
                    E2T[EID] = 19
                    E2P[EID] = PID
                    P2M[PID] = MID
                else:
                    s = "As of 2021.10.17, CTETRA 4 elements are not supported."
                    raise ValueError(s)
            # }}}
        if mesh.PyramidCount != 0: # {{{
            s = "Pyramids not supported as of 2021.10.16"
            raise ValueError(s)
             # }}}
        if mesh.PrismCount != 0: # {{{
            s = "Prisms not supported as of 2021.10.16"
            raise ValueError(s)
            # }}}
        data[mesh_number]['nodes'] = copy(nodes)
        data[mesh_number]['E2N'] = copy(E2N)
        data[mesh_number]['E2T'] = copy(E2T)
        data[mesh_number]['E2P'] = copy(E2P)
        data[mesh_number]['P2M'] = copy(P2M)
    return data
# }}}

def main(output_filename): # {{{
    """ GOAL: {{{
    =========
    Export many mesh FemMesh objects as a bdf file with correct numbering
    - [X] Extract nodes per each FemMesh for many FemMeshes
    - [X] Extract E2N per each FemMesh for many FemMeshes
    - [X] Extract E2T per each FemMesh for many FemMeshes
    - [X] Create E2P per each FemMesh for many FemMeshes
          NOTE: Will create a property for each set of elements in each FemMesh
    - [X] Create P2M per each FemMesh for many FemMeshes
          NOTE: Will create a material for each set of elements in each FemMesh
    - [X] Assemble core data structures together, correcting numbering
    - [ ] Un-break Salomes nutty inside out elements
    NOTE: Performance can be improved by sorting "data" from largest to smallest
    }}}"""
    mesh_objects = [] 
    for obj in Gui.Selection.getSelectionEx():
        if obj.TypeName == "Fem::FemMeshObject":
            mesh_objects.append(obj.Object.FemMesh)
        elif obj.TypeName == "Fem::FemMeshObjectPython":
            mesh_objects.append(obj.Object.FemMesh)

    # if there is nothing selected, raise an error
    if len(mesh_objects) == 0:
        raise ValueError("No mesh entities selected.")

    # for each mesh object selected, assemble a master set of data
    # 'data' will comprise the core data structures:[nodes, E2N, E2T, E2P, P2M]
    data = get_data_from_mesh_objects(mesh_objects)

    # Combine contents of data together into singular data structures
    nodes = {}  # Node ID to location
    E2N = {}    # Element to Node ID
    E2T = {}    # Element to Type ID
    E2P = {}    # Element to Property ID
    P2M = {}    # Property to Material ID
    NID = 0
    for i, mesh_data in enumerate(data):
        if i == 0:
            # add first selected mesh to the core data, as it's empty right now
            nodes = copy(mesh_data["nodes"])
            E2N = copy(mesh_data["E2N"])
            E2T = copy(mesh_data["E2T"])
            E2P = copy(mesh_data["E2P"])
            P2M = copy(mesh_data["P2M"])
            continue
        # Add and update element IDs in E2N and E2T
        EID_lookup_table = {}   # returns new EID, given the old EID
        for element in mesh_data["E2N"].keys():
            # check if its ID needs to be updated
            if element in E2N:
                EID_old = element
                EID_new = max(E2N.keys()) + 1
                EID_lookup_table[EID_old] = EID_new
                E2N[EID_new] = mesh_data["E2N"][EID_old]
                E2T[EID_new] = mesh_data["E2T"][EID_old]
                E2P[EID_new] = mesh_data["E2P"][EID_old]
            else:
                EID_lookup_table[element] = element
                E2N[element] = mesh_data["E2N"][element]
                E2T[element] = mesh_data["E2T"][element]
                E2P[element] = mesh_data["E2P"][element]

        # Add and update node IDs in nodes and E2N
        # get N2E to accelerate update of node IDs
        N2E = get_N2E(E2N)
        for node in mesh_data["nodes"].keys():
            if node in nodes.keys():
                NID_old = node
                NID_new = max(nodes.keys()) + 1
                # replace node ID in nodes
                nodes[NID_new] = mesh_data["nodes"][NID_old]
                # replace node ID in E2N
                for EID in N2E[NID_old]:
                    old_nodes_in_this_elm = E2N[EID]
                    new_nodes_in_this_elm = []
                    for N in old_nodes_in_this_elm:
                        if N == NID_old:
                            new_nodes_in_this_elm.append(NID_new)
                        else:
                            new_nodes_in_this_elm.append(N)
                    E2N[EID] = new_nodes_in_this_elm
            else:
                nodes[node] = mesh_data["nodes"][node]

        # Add and update property IDs in E2P and P2M
        props_in_current_E2P = list(set(E2P.values()))
        props_in_current_mesh_data = list(set(mesh_data["E2P"].values()))
        # if there's more than 1 prop in current mesh data, idk what to do yet
        if len(props_in_current_mesh_data) > 1:
            raise ValueError("Not sure how to deal with mutli-prop meshes yet")

        mats_in_current_P2M = list(set(P2M.values()))
        mats_in_current_mesh_data = list(set(mesh_data["P2M"].values()))
        if len(mats_in_current_mesh_data) > 1:
            raise ValueError("Not sure how to deal with mutli-mat meshes yet")

        new_PID = max(props_in_current_E2P) + 1
        new_MID = max(mats_in_current_P2M) + 1
        for old_EID in mesh_data["E2P"].keys():
            # check if the element in E2N needs its PID updated
            new_EID = EID_lookup_table[old_EID]
            E2P[new_EID] = new_PID
            P2M[new_PID] = new_MID

    # Now have nodes, E2N, E2T, E2P, and P2M, for a combined thingy

    # As a placeholder for later, two extra structures shall exist
    # Those are the P2T and M2T:
        # Property to type of property
        # Material to type of material
    # default type value for P2T and M2T will be 0 and 0 
    P2T = {}
    for PID in P2M.keys():
        P2T[PID] = 0
        
    M2T = {}
    for MID in P2M.values():
        M2T[MID] = 0

    # Mystran default supported property cards include
        # 0D: PELAS, PBUSH
        # 1D: PBAR, PBARL, PROD
        # 2D: PSHEAR, PSHELL, PCOMP, PCOMP1
        # 3D: PSOLID
    # Mystran default supported material cards include
        # MAT1, MAT2, MAT8, MAT9, PMASS
    # As of 2021.10.16, now deciding to use, by default
        # for 1D Elements: PBUSH and None
        # for 2D Elements: PSHELL and MAT1
        # for 3D Elements: PSOLID
    
    # Attempting to store bulkdata in giant string now
    bulkdata = create_bulkdata_list(nodes, E2N, E2T, E2P, P2M, P2T, M2T)

    # write resutls out 
    with open(output_filename, mode='wt', encoding='utf-8') as bdf:
        bdf.write('\n'.join(bulkdata))
    #}}}

if __name__ == '__main__':
    form = Form()
