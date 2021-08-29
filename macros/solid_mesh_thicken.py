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

# gather FemMeshObject instances from selections
mesh_objects_to_merge = [] 
for obj in Gui.Selection.getSelectionEx():
    if obj.TypeName == "Fem::FemMeshObject":
        mesh_objects_to_merge.append(obj.Object.FemMesh)
    elif obj.TypeName == "Fem::FemMeshObjectPython":
        mesh_objects_to_merge.append(obj.Object.FemMesh)

# gather edges from selection
selected_edges = []
for obj in Gui.Selection.getSelectionEx():
    if obj.HasSubObjects:
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

N_elms = 10
thickness = 10

# Thickening the shell mesh into a solid mesh
argument_stack = [thickness, nodes, E2N, E2T]
data_back = solid_mesh_by_thickened_shell_mesh(argument_stack)
