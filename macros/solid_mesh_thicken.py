# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem
from PySide import QtGui
import os
import sys
import numpy as np
from scipy.spatial import KDTree
current = os.path.dirname(os.path.realpath(__file__)) 
parent = os.path.dirname(current)
sys.path.append(parent)
from mesh_utilities import *

Vector = App.Vector

def get_E2N_nodes_and_E2T(mesh_objects_to_merge): # {{{
    """ takes in FemMesh objects, returns a combined E2N and nodes
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

    return [E2N, E2T, nodes]
#}}}

def main(): # {{{
    # gather FemMeshObject instances from selections
    mesh_objects_to_merge = [] 
    # gather edges from selection
    selected_edges = []
    for obj in Gui.Selection.getSelectionEx():
        if obj.TypeName == "Fem::FemMeshObject":
            mesh_objects_to_merge.append(obj.Object.FemMesh)
        elif obj.TypeName == "Fem::FemMeshObjectPython":
            mesh_objects_to_merge.append(obj.Object.FemMesh)
        elif obj.HasSubObjects:
            for sub in obj.SubObjects:
                if isinstance(sub, Part.Edge):
                    selected_edges.append(sub)
        else:
            obj_edges = obj.Object.Shape.Edges
            if len(obj_edges) == 1:
                selected_edges.append(obj_edges[0])
            
    # if there are no mesh objects selected, raise an error
    if len(mesh_objects_to_merge) == 0:
        raise ValueError("No mesh entities selected.")

    # determine the mode of the shell thickening
    # if there's no selected edges, set mode = 0
    if len(selected_edges) == 0:
        mode = 0
    # if there's one item in selected_edges, set mode = 1
    elif len(selected_edges) == 1:
        mode = 1

    # Throw errors on thicken mode
    if mode == 1:
        raise ValueError("As of 2021.08.29, no support for thicken mode 1")

    [E2N, E2T, nodes] = get_E2N_nodes_and_E2T(mesh_objects_to_merge)

    N_elms = 2
    thickness = 10

    # Thickening the shell mesh into a solid mesh
    argument_stack = [thickness, nodes, E2N, E2T, N_elms]
    # need to figure out where the printed 1 and 2 are coming from
    data_back = solid_mesh_by_thickened_shell_mesh_normals(argument_stack)
    nodes_offset = data_back[0]
    E2N_offset = data_back[1]
    E2T_offset = data_back[2]
# }}}

if __name__ == '__main__':
    main()

