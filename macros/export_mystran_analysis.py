# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem
from PySide import QtGui
from copy import copy as copy
import math
import re

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
    if x > 0:
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
    else:
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
            if math.log(x,10).is_integer():
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

    return bulkdata
    # }}}

def get_data_from_mesh_objects(mesh_objects): # {{{
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
        NID = max(nodes.keys(), default=0) # Node ID
        for node in mesh.Nodes:
            NID += 1
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

def is_valid_MAT1_card(material_label): # {{{
    """ Check if material label is of the correct abridged syntax
    """
    # does this contain MAT1?
    if "MAT1" not in material_label:
        raise ValueError("material label does not contain MAT1")

    # does this contain underscores?
    if "_" not in material_label:
        raise ValueError("material label does not contain _")

    split_material_label = material_label.split("_")

    # does the first field contain MAT1?
    if "MAT1" not in split_material_label[0]:
        raise ValueError("material label does not have MAT1 in field before _")
    
    # will allow the user to have a name before the MAT1 card
    split_material_label = ["MAT1", *split_material_label[1:]]

    # is second field a 'real'?
    # magic bullshit nastran 'real' definition that may or may not be perfect
    doom_regex = r'[-|+]{0,1}[0-9]*\.[0-9]*E[-|+]{0,1}[0-9]+'
    doom_regex_2 = r'[0-9]+\.[0-9]+'

    # check that first field is a valid youngs modulus
    if re.match(doom_regex, split_material_label[1]) is not None:
        pass
    elif re.match(doom_regex_2, split_material_label[2]) is not None:
        pass
    else:
        raise ValueError("material label needs a real as youngs modulus")

    # check that second field is nothing, or a valid shear modulus
    if len(split_material_label[2]) == 0:
        pass
    elif re.match(doom_regex, split_material_label[2]) is not None:
        pass
    elif re.match(doom_regex_2, split_material_label[2]) is not None:
        pass
    else:
        raise ValueError("mat label needs a real for shear modulus, or nothing")

    # check that third field is a valid poissons ratio
    if re.match(doom_regex, split_material_label[3]) is not None:
        pass
    elif re.match(doom_regex_2, split_material_label[3]) is not None:
        pass
    else:
        raise ValueError("mat label needs a real for poissons ratio")

    # check that fourth field is a valid density
    if re.match(doom_regex, split_material_label[4]) is not None:
        pass
    elif re.match(doom_regex_2, split_material_label[4]) is not None:
        pass
    else:
        raise ValueError("mat label needs a real for density")

    return True
# }}}

def main():
    """ Click on an Analysis in FreeCAD, save out everything in it to make a run.
    * as of 2021.10.24, shelved. Author is too stupid to think of ways to chunk 
    the state permutations into finite cases, at time of writing.
    """
    selected_objects = [] 
    for obj in Gui.Selection.getSelectionEx():
        selected_objects.append(obj.Object)

    if len(selected_objects) != 1:
        raise ValueError("As of 2021.10.17, only one analysis may be selected.")

    if selected_objects[0].TypeId != "Fem::FemAnalysis":
        raise ValueError("Must be a Fem::FemAnalysis object")

    FEM_objects = selected_objects[0].Group

    # Is there at least one Fem::FemMeshObject or Fem::FemMeshObjectPython?
    MeshObjects = []
    MeshObjectNames = []
    rest_of_FEM_objects = []
    for obj in FEM_objects:
        if obj.TypeId == "Fem::FemMeshObject":
            MeshObjects.append(obj.FemMesh)
            MeshObjectNames.append(obj.Label)
        elif obj.TypeId == "Fem::FemMeshObjectPython":
            MeshObjects.append(obj.FemMesh)
            MeshObjectNames.append(obj.Label)
        else:
            rest_of_FEM_objects.append(obj)

    # If not, abort.
    if len(MeshObjects) == 0:
        raise ValueError("Need at least one FemMesh Object to export")

    data_from_mesh_objects = copy(get_data_from_mesh_objects(MeshObjects))

    # is there exactly one solver object in rest of the FEM objects?
    N_solvers = 0
    solver_objects = []
    misc_objects = []
    for obj in rest_of_FEM_objects:
        if obj.TypeId == "Fem::FemSolverObjectPython":
            N_solvers += 1
            solver_objects.append(obj)
        else:
            misc_objects.append(obj)
    rest_of_FEM_objects = copy(misc_objects)

    if N_solvers != 1:
        s = "Require exactly one solver object in the analysis group"
        raise ValueError(s)

    # check that the solver object is for mystran
    if solver_objects[0].Label != "SolverMystran":
        s = "as of 2021.10.22, only know how to deal with mystran decks"
        raise ValueError(s)

    # check that the analysis type is for a static analysis        
    if solver_objects[0].AnalysisType != "static":
        s = "as of 2021.10.22, only know how to deal with linear static decks"
        raise ValueError(s)

    # get the node sets here
    node_sets = []
    everything_else = []
    for obj in rest_of_FEM_objects:
        if obj.TypeId == "Fem::FemSetNodesObject":
            node_sets.append(obj)
        else:
            everything_else.append(obj)
    rest_of_FEM_objects = copy(everything_else)

    # get the material objects
    material_objects = []
    everything_else = []
    for obj in rest_of_FEM_objects:
        if obj.TypeId == "App::MaterialObjectPython":
            material_objects.append(obj)
        else:
            everything_else.append(obj)
    rest_of_FEM_objects = copy(everything_else)


    # get the FeaturePython objects (really just want the pshell cards)
    feature_objects = []
    everything_else = []
    for obj in rest_of_FEM_objects:
        if obj.TypeId == "Fem::FeaturePython":
            feature_objects.append(obj)
        else:
            everything_else.append(obj)
    
    # if there's anything else here, say I don't know how to handle it.
    if len(everything_else) != 0:
        s = "as of 2021.10.22, don't know how to deal with other things here."
        raise ValueError(s)

    # have now collected some stuff
    # node_sets
    # material_objects
    # feature_objects
    # solver_objects

    # Get the unit system to use for unit conversion, possibly
    App.ParamGet("User parameter:BaseApp/Preferences/Units")

    # get link from feature label to mesh label
    feature_links = []
    for feature in feature_objects:
        references = feature.References
        # it is possible to refer zero, one, or more than one object
        for obj in references:
            mesh_label = obj[0].Label
            feature_links.append([feature.Label, mesh_label])

    # get link from material label to mesh label
    material_links = []
    for material in material_objects:
        references = material.References
        for obj in references:
            mesh_label = obj[0].Label
            material_links.append([material.Label, mesh_label])

    # get link from nodeset label to mesh label
    nodeset_links = []
    for node_set in node_sets:
        mesh_label = node_set.FemMesh.Label
        nodeset_links.append([node_set.Label, mesh_label])

    # for each mesh object, loop through everything else here to see if anything
    # refers to it
    material_cards = []
    property_cards = []
    MID = 1
    PID = 1
    for index, mesh_data in enumerate(data_from_mesh_objects):
        label = MeshObjectNames[index]
        nodes = mesh_data['nodes']
        E2N = mesh_data['E2N']
        E2T = mesh_data['E2T']
        E2P = mesh_data['E2P']
        P2M = mesh_data['P2M']

        # does mesh have a material?
        mesh_has_material = False
        if label in list(zip(*material_links))[1]:
            mesh_has_material = True
            material_label = list(zip(*material_links))[0][0]
            # does it have more than one? 
            if list(zip(*material_links))[1].count(label) > 1:
                s = "meshes cannot have more than one material"
                raise ValueError(s)

        # does mesh have a feature?
        mesh_has_feature = False
        if label in list(zip(*feature_links))[1]:
            mesh_has_feature = True
            mesh_property_label = list(zip(*feature_links))[0][0]
            # does it have more than one?
            if list(zip(*feature_links))[1].count(label) > 1:
                s = "meshes cannot have more than one feature"
                raise ValueError(s)
        
        # if it has a material, make the card
        if mesh_has_material:
            # get the material 
            if is_valid_MAT1_card(material_label):
                pass
            split_material_label = material_label.split("_")
            split_material_label = ["MAT1", *split_material_label[1:]]
            split_material_label.insert(1, str(MID))
            MID += 1
            mat_card = ",".join(split_material_label)
            material_cards.append(mat_card)
            print(material_cards)

        if mesh_has_feature:
            # need to figure out what the hell the feature even is.
            # feature seems like it's a very generic property name
            # I fear the other things that are simply classified as properties
            # that I have no idea about.
            print(mesh_property_label)
            print(vars(feature_objects[0]))

    # Still need to close with an ENDDATA line
    #bulkdata.append("ENDDATA")

if __name__ == '__main__':
   main() 
