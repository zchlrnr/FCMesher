# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem
from PySide import QtGui
import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from mesh_utilities import *
import numpy as np
from scipy.spatial import KDTree

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

"""
GOAL:
- [X] Get a list of clicked mesh entities.
- [X] Get number of nodes
- [X] Get number of elements
- [X] Put the mesh objects all in one new mesh object
- [X] Replace N2E with an N2E in mesh_utilities.py by adding previous
      directory to the module path
- [ ] Implement equivalence routine with KDTree
...
- [ ] Generalize code for multiple element types
"""
mesh_objects_to_merge = [] 
for obj in Gui.Selection.getSelectionEx():
    if obj.TypeName == "Fem::FemMeshObject":
        mesh_objects_to_merge.append(obj.Object.FemMesh)
    elif obj.TypeName == "Fem::FemMeshObjectPython":
        mesh_objects_to_merge.append(obj.Object.FemMesh)

[E2N, nodes] = get_combined_E2N_and_nodes(mesh_objects_to_merge)

print(E2N)
print("")
print(nodes)
