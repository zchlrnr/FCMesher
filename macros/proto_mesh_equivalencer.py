"""
TODO:
 - disable existing meshes
 - check to see if mesh already exists...harder
 - add equivalence tolerance to user control
 - don't make it unclear what is being equivalenced
 - support TRI3, QUAD8, TRI6
"""
# App = FreeCAD, Gui = FreeCADGui
#import os
#import sys
from typing import List, Dict
import numpy as np
import FreeCAD, Part, Fem
from PySide import QtGui

import scipy
if scipy.__version__ < '1.6':
    from scipy.spatial import cKDTree as KDTree
else:
    from scipy.spatial import KDTree

#currentdir = os.path.dirname(os.path.realpath(__file__))
#parentdir = os.path.dirname(currentdir)
#sys.path.append(parentdir)
#from mesh_utilities import *
Vector = App.Vector

from PySide.QtGui import QFont, QIntValidator, QDoubleValidator
from PySide.QtGui import QComboBox, QLineEdit,  QGridLayout, QPushButton, QLabel

#class QFloatEdit(QLineEdit):
    #def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)
        #qfloat_validator = QDoubleValidator()
        #self.setValidator(qfloat_validator)


class EquivalenceDialog(QtGui.QDialog): # {{{
    """flip the true in __name__ == '__main__' to bypass the dialogue"""

    def __init__(self): # {{{
        super(EquivalenceDialog, self).__init__()
        self.setModal(True)
        self.makeUI()
        self.show()
    # }}}

    def makeUI(self): # {{{
        label = QLabel('Equivalence Tolerance')
        self.equiv_tol_edit = QLineEdit('0.0')

        run_button = QPushButton('Run')
        run_button.clicked.connect(self.on_run)
        layout = self._make_layout(label, run_button)
        self.setLayout(layout)
    # }}}

    def _make_layout(self, label, run_button): # {{{
        layout = QGridLayout()
        layout.addWidget(label, 0, 0)
        layout.addWidget(self.equiv_tol_edit, 1, 0)
        layout.addWidget(run_button, 2, 1)
        return layout
    #}}}

    def on_run(self): #{{{
        print('on_run')
        value = self.equiv_tol_edit.value()
        try:
            equiv_tol = float(value)
        except ValueError:
            print(f'equiv_tol = {value!r} is invalid')
            return
        if equiv_tol < 0.:
            print('equiv_tol < 0.')
            return
        main(equiv_tol)
        print('finished')
        self.close()
        #}}}
# }}}

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
    nodes_for_bodies_list = []
    for obj in mesh_objects_to_merge:
        nodes_dict = {}
        for n in obj.Nodes:
            x, y, z = obj.getNodeById(n)
            nodes_dict[n] = [x, y, z]
        nodes_for_bodies_list.append(nodes_dict)
    # get element connectivity for all elements
    E2N_for_bodies_list = []
    for obj in mesh_objects_to_merge:
        E2N_dict = {}
        for e in obj.Faces:
            E2N_dict[e] = obj.getElementNodes(e)
        E2N_for_bodies_list.append(E2N_dict)
    # Assembling the new mesh primitives
    # Make lookup table for old NID to new NID
    N_bodies = len(nodes_for_bodies_list)
    # [body ID, old ID, new ID, x, y, z]
    NID = 1
    nodes_lookup_list = []
    for i, nodes_for_body_dicti in enumerate(nodes_for_bodies_list):
        j = 0
        for j, xyz in nodes_for_body_dicti.items():
            x, y, z = xyz
            nodes_lookup_list.append([i+1, j+1, NID, x, y, z])
            NID += 1
    # Make lookup table for old EID to new EID
    # [body ID, old ID, new ID, N1, N2, N3, N4]
    EID = 1
    E2N_lookup_list = []
    for E2N_for_body_dict in E2N_for_bodies_list:
        j = 0
        for elem_nodes in E2N_for_body_dict.values():
            N1, N2, N3, N4 = elem_nodes
            E2N_lookup_list.append([i+1, j+1, EID, N1, N2, N3, N4])
            j += 1
            EID += 1
    new_E2N_list = E2N_lookup_list
    for i in range(N_bodies):
        # get shortened range of nodes to lookup
        shortened_nodes_lookup = []
        for nodes_lookupj in nodes_lookup_list:
            if nodes_lookupj[0] == i+1:
                shortened_nodes_lookup.append(nodes_lookupj)
        # for  each of the shortened node IDs, update the E2N
        for n in shortened_nodes_lookup:
            NID_old = n[1]
            NID_new = n[2]
            for new_E2N_k in new_E2N_list:
                body_ID = new_E2N_k[0]
                NID1 = new_E2N_k[3]
                NID2 = new_E2N_k[4]
                NID3 = new_E2N_k[5]
                NID4 = new_E2N_k[6]
                if body_ID == i + 1:
                    # go through all the nodes and replace them
                    if NID_old == NID1:
                        new_E2N_k[3] = NID_new
                    if NID_old == NID2:
                        new_E2N_k[4] = NID_new
                    if NID_old == NID3:
                        new_E2N_k[5] = NID_new
                    if NID_old == NID4:
                        new_E2N_k[6] = NID_new
    # Populate E2N
    E2N_dict = {}
    for new_E2Ni in new_E2N_list:
        EID = new_E2Ni[2]
        N1 = new_E2Ni[3]
        N2 = new_E2Ni[4]
        N3 = new_E2Ni[5]
        N4 = new_E2Ni[6]
        E2N_dict[EID] = [N1, N2, N3, N4]
    # Populate nodes
    nodes_dict = {}
    for nodes_lookupi in nodes_lookup_list:
        NID = nodes_lookupi[2]
        x = nodes_lookupi[3]
        y = nodes_lookupi[4]
        z = nodes_lookupi[5]
        nodes_dict[NID] = [x, y, z]
    return E2N_dict, nodes_dict
# }}}

def get_node_equivalence_replacement_array(nodes_dict: Dict[int, int], tolerance: float): # {{{
    """ Takes in nodes, and tolerance. Returns node_replacement_array
    node_replacement_array is the lower node ID of the match,
    followed by the higher node ID of the match
    - [ ] Move this to the mesh_utilities.py file
    - [ ] Implement error handling and error reporting with raise ValueError
    """
    # Creating NID to index
    # constructing list of lists of node IDs
    NID2index = {}
    index2NID = {}
    node_coords_list = []
    counter = 0
    for NID, node in sorted(nodes_dict.items()):
        NID2index[NID] = counter
        index2NID[counter] = NID
        node_coords_list.append(node)
        counter += 1
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
    E2N_dict = {}
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
            E2N_dict[EID_new] = new_nodes_in_elm

    # create nodes
    nodes_dict = {}
    for node in nid_transform:
        body_index = node[0] - 1
        old_NID = node[1]
        new_NID = node[2]
        obj = mesh_objects_to_merge[body_index]
        nodes_dict[new_NID] = list(obj.Nodes[old_NID])

    # check that there was only one type of element, and it was 15 (CQUAD4)
    E2T_dict = {}
    if len(mesh_types_expected) == 1 and mesh_types_expected[0] == 15:
        # Populate the E2T
        for e in E2N_dict:
            E2T_dict[e] = 15
    else:
        raise ValueError("Unknown elements passed into mesh equivalencer.")

    return E2N_dict, E2T_dict, nodes_dict
#}}}

def flatten_unique(ids: List[List[int]]) -> List[int]: # {{{
    """Assumes a list of lists as input"""
    ids_flat = []
    for idsi in ids:
        ids_flat.extend(idsi)
    unique_ids = list(set(ids_flat))
    return unique_ids
#}}}


def main(tol: float=0.01): # {{{
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
    - [ ] Make mesh entity from nodes, E2N, and E2T
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
        else:
            print(f'obj.TypeName={obj.TypeName} is not supported')

    # if there is nothing selected, raise an error
    if len(mesh_objects_to_merge) == 0:
        raise ValueError("No mesh entities selected.")

    (E2N_dict, E2T, nodes) = get_E2N_nodes_and_E2T(mesh_objects_to_merge)

    node_replacement_array = get_node_equivalence_replacement_array(nodes, tol)
    # if there's nothing to replace, throw error/message idk
    if len(node_replacement_array) == 0:
        print(f'No nodes within equivolence tolerance of {tol}')
        return

    # get a list of the unique node IDs in node_replacement_array
    unique_replacement_NIDs = []
    for n in node_replacement_array:
        if n[0] not in unique_replacement_NIDs:
            unique_replacement_NIDs.append(n[0])
        if n[1] not in unique_replacement_NIDs:
            unique_replacement_NIDs.append(n[1])

    # replace the node IDs in the E2N
    new_E2N = E2N_dict
    for rep in node_replacement_array:
        old_NID = rep[0]
        new_NID = rep[1]
        # go through E2N, try to replace instances of old_NID with new_NID
        for e in E2N_dict:
            EID = e
            nodes_in_elm = E2N_dict[EID]
            # count how many times old_NID or new_NID occurs in elms
            N_occurances = 0
            for n in nodes_in_elm:
                if n == old_NID:
                    N_occurances += 1
                elif n == new_NID:
                    N_occurances += 1
            if N_occurances == 2: # if node occurs twice, would collapse element
                print(f'A tolerance of {tol} would collapse element {e}')
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
    E2N_dict = new_E2N

    # remake nodes without the nodes that shouldn't exist anymore
    nodes_in_E2N = E2N_dict.values()
    nodes_in_E2N = flatten_unique(nodes_in_E2N)

    # nodes in nodes that aren't in nodes_in_E2N need to be deleted
    new_nodes = {}
    for nid in nodes:
        if nid in nodes_in_E2N:
            new_nodes[nid] = nodes[nid]
    nodes = new_nodes

    # As of 2021.08.26, know that everything here is probably
    # CQUAD4 shell elements.
    print(f'nodes = {nodes}')
    equivalenced_mesh = Fem.FemMesh()
    for nid, node in nodes.items():
        equivalenced_mesh.addNode(*[*node, nid])
    for eid, nodes in E2N_dict.items():
        print(f'nodes={nodes} eid={eid}')
        equivalenced_mesh.addFace(nodes, eid)

    # Making it render correctly
    doc = App.ActiveDocument
    obj = doc.addObject("Fem::FemMeshObject", "equivalenced_mesh")
    obj.FemMesh = equivalenced_mesh
    obj.Placement.Base = FreeCAD.Vector(0, 0, 0)
    obj.ViewObject.DisplayMode = "Faces, Wireframe & Nodes"
    obj.ViewObject.BackfaceCulling = False

    doc.recompute()
# }}}

if __name__ == '__main__':
    tol = 0.01

    if True:
        form = EquivalenceDialog()
    else:
        main(tol)
