# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem
from PySide import QtGui
import os
import sys
import numpy as np
from scipy.spatial import KDTree
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from mesh_utilities import *
Vector = App.Vector

def get_combined_E2N_and_nodes(mesh_objects_to_merge): # {{{
    """ takes in FemMesh objects, returns a combined E2N and nodes
    - [ ] Add error handling to acknowledge what element types
          still need implementation.
    - [ ] Make it also return an E2T
    """
    # get number of nodes
    N_nodes = 0
    for obj in mesh_objects_to_merge:
        N_nodes += len(obj.Nodes)
    # get number of elements
    N_elms = 0
    for obj in mesh_objects_to_merge:
        # ONLY DOING FACES FOR NOW!!
        N_elms += len(obj.Faces)
    # make nodes for each body
    nodes_for_bodies = []
    for obj in mesh_objects_to_merge:
        nodes = {}
        for n in obj.Nodes:
            v = obj.getNodeById(n)
            x = v[0]
            y = v[1]
            z = v[2]
            nodes[n] = [x, y, z]
        nodes_for_bodies.append(nodes)
    # get element connectivity for all elements
    E2N_for_bodies = []
    for obj in mesh_objects_to_merge:
        E2N = {}
        for e in obj.Faces:
            E2N[e] = obj.getElementNodes(e)
        E2N_for_bodies.append(E2N)
    # Assembling the new mesh primitives
    # Make lookup table for old NID to new NID
    N_bodies = len(nodes_for_bodies)
    # [body ID, old ID, new ID, x, y, z]
    nodes_lookup = []
    NID = 0
    for i in range(N_bodies):
        for j in range(len(nodes_for_bodies[i].keys())):
            NID += 1
            x = list(nodes_for_bodies[i].values())[j][0]
            y = list(nodes_for_bodies[i].values())[j][1]
            z = list(nodes_for_bodies[i].values())[j][2]
            nodes_lookup.append([i+1, j+1, NID, x, y, z])
    # Make lookup table for old EID to new EID
    # [body ID, old ID, new ID, N1, N2, N3, N4]
    E2N_lookup = []
    EID = 0
    for i in range(N_bodies):
        for j in range(len(E2N_for_bodies[i].keys())):
            EID += 1
            N1 = list(E2N_for_bodies[i].values())[j][0]
            N2 = list(E2N_for_bodies[i].values())[j][1]
            N3 = list(E2N_for_bodies[i].values())[j][2]
            N4 = list(E2N_for_bodies[i].values())[j][3]
            E2N_lookup.append([i+1, j+1, EID, N1, N2, N3, N4])
    new_E2N = E2N_lookup
    for i in range(N_bodies):
        # get shortened range of nodes to lookup
        shortened_nodes_lookup = []
        for j in range(len(nodes_lookup)):
            if nodes_lookup[j][0] == i+1:
                shortened_nodes_lookup.append(nodes_lookup[j])
        # for  each of the shortened node IDs, update the E2N
        for j in range(len(shortened_nodes_lookup)):
            n = shortened_nodes_lookup[j]
            NID_old = n[1]
            NID_new = n[2]
            for k in range(len(new_E2N)):
                body_ID = new_E2N[k][0]
                NID1 = new_E2N[k][3]
                NID2 = new_E2N[k][4]
                NID3 = new_E2N[k][5]
                NID4 = new_E2N[k][6]
                if body_ID == i + 1:
                    # go through all the nodes and replace them
                    if NID_old == NID1:
                        new_E2N[k][3] = NID_new
                    if NID_old == NID2:
                        new_E2N[k][4] = NID_new
                    if NID_old == NID3:
                        new_E2N[k][5] = NID_new
                    if NID_old == NID4:
                        new_E2N[k][6] = NID_new
    # Populate E2N
    E2N = {}
    for i in range(len(new_E2N)):
        EID = new_E2N[i][2]
        N1 = new_E2N[i][3]
        N2 = new_E2N[i][4]
        N3 = new_E2N[i][5]
        N4 = new_E2N[i][6]
        E2N[EID] = [N1, N2, N3, N4]
    # Populate nodes
    nodes = {}
    for i in range(len(nodes_lookup)):
        NID = nodes_lookup[i][2]
        x = nodes_lookup[i][3]
        y = nodes_lookup[i][4]
        z = nodes_lookup[i][5]
        nodes[NID] = [x, y, z]
    return [E2N, nodes]
# }}}

def get_node_equivalence_replacement_array(nodes, tolerance): # {{{
    """ Takes in nodes, and tolerance. Returns node_replacement_array
    node_replacement_array is the lower node ID of the match,
    followed by the higher node ID of the match
    - [ ] Move this to the mesh_utilities.py file
    - [ ] Implement error handling and error reporting with raise ValueError
    """
    # Creating NID to index 
    NID2index = {}
    index2NID = {}
    counter = 0
    for i in list(nodes.keys()):
        NID2index[i] = counter
        index2NID[counter] = i
        counter += 1

    # constructing list of lists of node IDs
    node_coords_list = []
    for NID in list(nodes.keys()):
        node_coords_list.append(nodes[NID])
    # converting node_coords_list to nparray
    node_coords_list = np.array(node_coords_list)

    # Construct the tree containing the nodal data
    tree = KDTree(node_coords_list)

    # Query pairs of nodes in KDTree to see if any are within tolerance
    pairs = tree.query_pairs(tolerance)

    # converting pair list to a list of tuples
    pairs = list(pairs)

    # compute node ID replacement array
    node_replacement_array = []
    for p in pairs:
        NID_lower = index2NID[p[0]]
        NID_upper = index2NID[p[1]]
        node_replacement_array.append([NID_lower, NID_upper])
    return node_replacement_array
# }}}

def get_E2N_nodes_and_E2T(mesh_objects_to_merge): # {{{
    """ takes in FemMesh objects, returns a combined E2N and nodes
    - [ ] Make it also return an E2T once other element types are supported
    """

    # check all mesh entities for pre-coded types # {{{
    for obj in mesh_objects_to_merge:
        # if there are any edge elements, raise error and abort
        if obj.EdgeCount != 0:
            s = "Edges not supported as of 2021.08.22"
            raise ValueError(s)
        elif obj.TriangleCount != 0:
            s = "Triangles not supported as of 2021.08.22"
            raise ValueError(s)
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
    return [E2N, nodes]
#}}}

def main(): # {{{
    """
    GOAL:
    - [X] Get a list of clicked mesh entities.
    - [X] Get number of nodes
    - [X] Get number of elements
    - [X] Put the mesh objects all in one new mesh object
    - [X] Replace N2E with an N2E in mesh_utilities.py by adding previous
          directory to the module path
    - [X] Implement equivalence routine with KDTree
    - [X] Implement error handling in get_combined_E2N_and_nodes
          with the explicit goal of capturing elements not supported
    - [X] Rework get_combined_E2N_and_nodes to skip gaps and be correct
    ...
    - [ ] Generalize code for all of the element element types
    - [ ] Deal with fact that coordinates and properties can refer to node IDs
    """
    mesh_objects_to_merge = [] 
    for obj in Gui.Selection.getSelectionEx():
        if obj.TypeName == "Fem::FemMeshObject":
            mesh_objects_to_merge.append(obj.Object.FemMesh)
        elif obj.TypeName == "Fem::FemMeshObjectPython":
            mesh_objects_to_merge.append(obj.Object.FemMesh)

    # if there is nothing selected, raise an error
    if len(mesh_objects_to_merge) == 0:
        raise ValueError("No mesh entities selected.")
    

    [E2N, nodes] = get_E2N_nodes_and_E2T(mesh_objects_to_merge)

    tol = 0.01 

    node_replacement_array = get_node_equivalence_replacement_array(nodes, tol)
    # if there's nothing to replace, throw error/message idk
    if len(node_replacement_array) == 0:
        print("No nodes within equivolence tolerance of ",tol)
        return

    # get a list of the unique node IDs in node_replacement_array
    unique_replacement_NIDs = []
    for n in node_replacement_array:
        if n[0] not in unique_replacement_NIDs:
            unique_replacement_NIDs.append(n[0])
        if n[1] not in unique_replacement_NIDs:
            unique_replacement_NIDs.append(n[1])

    # replace the node IDs in the E2N
    new_E2N = E2N
    for rep in node_replacement_array:
        old_NID = rep[0]
        new_NID = rep[1]
        # go through E2N, try to replace instances of old_NID with new_NID
        for e in list(E2N.keys()):
            EID = e
            nodes_in_elm = E2N[EID]
            # count how many times old_NID or new_NID occurs in elms
            N_occurances = 0
            for n in nodes_in_elm:
                if n == old_NID:
                    N_occurances += 1
                elif n == new_NID:
                    N_occurances += 1
            if N_occurances == 2: # if node occurs twice, would collapse element
                print("A tolerance of ", tol," would collapse element ", e)
                return
            elif N_occurances == 1: # if node occurs once, replace old with new
                new_nodes_in_elm = []
                for n in nodes_in_elm:
                    if n == old_NID:
                        new_nodes_in_elm.append(new_NID)
                    else:
                        new_nodes_in_elm.append(n)
                new_E2N[e] = new_nodes_in_elm
    # update E2N
    E2N = new_E2N

    # remake nodes without the nodes that shouldn't exist anymore
    nodes_in_E2N = E2N.values()
    nodes_in_E2N_flat = []
    for n in nodes_in_E2N:
        for i in n:
            nodes_in_E2N_flat.append(i)
    nodes_in_E2N = list(set(nodes_in_E2N_flat))
    # nodes in nodes that aren't in nodes_in_E2N need to be deleted
    new_nodes = {}
    for n in list(nodes.keys()):
        if (n in nodes_in_E2N):
            new_nodes[n] = nodes[n]
    nodes = new_nodes


# }}}

if __name__ == '__main__':
    main()
