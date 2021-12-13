# App = FreeCAD, Gui = FreeCADGui
from typing import List
import FreeCAD, Part, Fem
from PySide import QtGui
import numpy as np
from math import ceil
from scipy.spatial import KDTree
Vector = App.Vector

def get_E2N_nodes_and_E2T(mesh_objects_to_merge): # {{{
    """
    Takes in FemMesh objects, returns a combined E2N and nodes
    - [ ] Make it also return an E2T once other element types are supported
    """
    mesh_types_expected = []
    # check all mesh entities for pre-coded types # {{{
    for obj in mesh_objects_to_merge:
        # if there are any edge elements, raise error and abort
        if obj.EdgeCount != 0:
            s = "Edges not supported as of 2021.08.22"
            raise ValueError(s)
        elif obj.TriangleCount != 0:
            s = "Triangles not supported as of 2021.08.22"
            raise ValueError(s)
        elif obj.QuadrangleCount !=0:
            mesh_types_expected.append(15)
        elif obj.HexaCount != 0:
            s = "Hexas not supported as of 2021.08.22"
            raise ValueError(s)
        elif obj.TetraCount != 0:
            s = "Tetras not supported as of 2021.08.22"
            raise ValueError(s)
        elif obj.VolumeCount != 0:
            s = "Volumes not supported as of 2021.08.22"
            raise ValueError(s)
        elif obj.PyramidCount != 0:
            s = "Pyramids not supported as of 2021.08.22"
            raise ValueError(s)
        elif obj.PrismCount != 0:
            s = "Prisms not supported as of 2021.08.22"
            raise ValueError(s)
    # }}}
    mesh_types_expected = list(set(mesh_types_expected))

    # get [body ID, node ID old, node ID new]
    nid_transform = []
    body_ID = 1
    NID = 1
    for obj in mesh_objects_to_merge:
        for n in obj.Nodes:
            nid_transform.append([body_ID, n, NID])
            NID += 1
        body_ID += 1
    # get [body ID, EID old, EID new]
    eid_transform = []
    body_ID = 1
    EID = 1
    for obj in mesh_objects_to_merge:
        for e in obj.Faces:
            eid_transform.append([body_ID, e, EID])
            EID += 1
        body_ID += 1

    # create E2N for the ascending order
    current_body_ID = 0
    EID = 1
    E2N = {}
    for obj in mesh_objects_to_merge:
        current_body_ID += 1
        # get the part of eid transform that's in this body
        eid_transform_relevant = []
        for e in eid_transform:
            if e[0] == current_body_ID:
                eid_transform_relevant.append(e)
        # get the part of nid transform that's in this body
        nid_transform_relevant = []
        for n in nid_transform:
            if n[0] == current_body_ID:
                nid_transform_relevant.append(n)
        # making node ID dictionary [old --> new]
        n_rel = {}
        for n in nid_transform_relevant:
            n_rel[n[1]] = n[2]
        # for the relevant elements, make E2N
        for e in eid_transform_relevant:
            EID_old = e[1]
            EID_new = e[2]
            nodes_in_elm = list(obj.getElementNodes(EID_old))
            # replace nodes in elm with its new node IDs
            new_nodes_in_elm = []
            for n in nodes_in_elm:
                NID_new = n_rel[n]
                new_nodes_in_elm.append(NID_new)
            E2N[EID_new] = new_nodes_in_elm
    # create nodes
    nodes = {}
    for n in nid_transform:
        body_index = n[0] - 1
        old_NID = n[1]
        new_NID = n[2]
        obj = mesh_objects_to_merge[body_index]
        nodes[new_NID] = list(obj.Nodes[old_NID])

    # check that there was only one type of element, and it was 15 (CQUAD4)
    E2T = {}
    if len(mesh_types_expected) == 1 and mesh_types_expected[0] == 15:
        # Populate the E2T
        for e in E2N:
            E2T[e] = 15
    else:
        raise ValueError("Unknown elements passed into mesh equivalencer.")

    return (E2N, E2T, nodes)
#}}}

def get_nodes_within_tolerance(nodes, distance, x, y, z): # {{{
    """Takes in nodes and distance, returns list of node IDs within distance"""
    # Creating NID to index
    NID2index = {}
    index2NID = {}
    counter = 0
    for i in nodes:
        NID2index[i] = counter
        index2NID[counter] = i
        counter += 1

    # constructing list of lists of node IDs
    node_coords_list = []
    for NID, node in nodes.items():
        node_coords_list.append(node)
    # converting node_coords_list to nparray
    node_coords_list = np.array(node_coords_list)

    # Construct the tree containing the nodal data
    tree = KDTree(node_coords_list)

    nodes_within_ball = tree.query_ball_point([x, y, z], distance)
    return nodes_within_ball
    #}}}

def main(): # {{{
    # get all the nodes near the point I hard code here
    x = 12.7
    y = 12.7
    z = 0.0

    # set MPC creation tolerance
    R = 25.4 * 0.125

    # get mesh that's clicked on
    mesh_objects_selected = []
    for obj in Gui.Selection.getSelectionEx():
        if obj.TypeName == "Fem::FemMeshObject":
            mesh_objects_selected.append(obj.Object.FemMesh)
        elif obj.TypeName == "Fem::FemMeshObjectPython":
            mesh_objects_selected.append(obj.Object.FemMesh)

    # if there is nothing selected, raise an error
    if len(mesh_objects_selected) == 0:
        raise ValueError("No mesh entities selected.")

    (E2N, E2T, nodes) = get_E2N_nodes_and_E2T(mesh_objects_selected)

    nodes_to_mpc = get_nodes_within_tolerance(nodes, R, x, y, z)
    if len(nodes_to_mpc) == 0:
        print("No nodes within ",R ," units of [",x,",",y,",",z,"]")
        return

    # making grid ID that we'll be using as the central node
    NID_mpc_start = max(nodes) + 1
    print("GRID,"+str(NID_mpc_start)+",,"+f'{x:.3},{y:.3},{z:.3}')

    # getting highest EID
    EID_mpc_start = max(list(E2N.keys())) + 1
    RBE3_lines = write_rbe3(EID_mpc_start, NID_mpc_start, nodes_to_mpc)
    for l in RBE3_lines:
        print(l)
#}}}

def write_rbe3(eid: int, nid: int, nodes_to_mpc: List[int]): # {{{
    # determine how many lines the RBE3 card would have to be
    if len(nodes_to_mpc) < 3:
        n_rbe3_card_lines = 1
    else:
        n_rbe3_card_lines = 1 + ceil((len(nodes_to_mpc)-2)/8)

    # making rbe3 card string set
    RBE3_line1_string = "RBE3,"
    RBE3_line1_string += str(eid) + ",,"
    RBE3_line1_string += str(nid) + ","
    RBE3_line1_string += "123456,1.0,123,"
    if len(nodes_to_mpc) >= 1:
        RBE3_line1_string += str(nodes_to_mpc[0]) + ","
    if len(nodes_to_mpc) >= 2:
        RBE3_line1_string += str(nodes_to_mpc[1])
    if n_rbe3_card_lines == 1:
        print(RBE3_line1_string)
        return

    RBE3_lines = []
    RBE3_lines.append(RBE3_line1_string)
    nodes_in_line = 0
    construction = ""
    for i in range(len(nodes_to_mpc)-2):
        NID = nodes_to_mpc[i+2]
        construction += "," + str(NID)
        nodes_in_line += 1
        if nodes_in_line == 8:
            RBE3_lines.append(construction)
            nodes_in_line = 0
            construction = ""
        elif i+1 == len(nodes_to_mpc)-2:
            RBE3_lines.append(construction)
    return RBE3_lines
# }}}

if __name__ == '__main__':
    main()

