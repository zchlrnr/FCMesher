# App = FreeCAD, Gui = FreeCADGui
from collections import defaultdict
from typing import List, Dict
import FreeCAD, Part, Fem
from PySide import QtGui
import numpy as np

Vector = App.Vector
ELEMENT_TYPE_QUAD = 15

class Form(QtGui.QDialog): # {{{
    """Set N_layers and total thickness"""
    # savior --> https://doc.qt.io/qtforpython/tutorials/basictutorial/dialog.html
    # https://zetcode.com/gui/pysidetutorial/layoutmanagement/
    N_layers = 3
    thickness = 1

    def __init__(self): # {{{
        super(Form, self).__init__()
        self.setModal(True)
        self.makeUI()
        # }}}

    def makeUI(self): # {{{
        label_layers = QtGui.QLabel('N_layers')
        spin_layers = self.spin_layers = QtGui.QSpinBox()
        spin_layers.setValue(self.N_layers)
        spin_layers.setRange(1, 1000)

        label_thickness = QtGui.QLabel('total thickness')
        thickness_field = self.thickness_field = QtGui.QLineEdit(str(self.thickness))

        btn = self.btn = QtGui.QPushButton('Thicken Shell Mesh')
        btn.clicked.connect(self.make_mesh)

        layout = QtGui.QGridLayout()
        layout.addWidget(label_layers, 0, 0)
        layout.addWidget(spin_layers, 0, 1)
        layout.addWidget(label_thickness, 1, 0)
        layout.addWidget(thickness_field, 1, 1)
        layout.addWidget(btn, 2, 1)

        self.setLayout(layout)
        self.show()
    # }}}

    def get_values(self): # {{{
        return self.N_layers, self.thickness
    # }}}

    def make_mesh(self): # {{{
        self.N_layers = self.spin_layers.value()
        self.thickness = float(self.thickness_field.text())
        main(self.N_layers, self.thickness)
        self.close()
    # }}}
# }}}
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
    if len(mesh_types_expected) == 1 and mesh_types_expected[0] == ELEMENT_TYPE_QUAD:
        # Populate the E2T
        for e in E2N:
            E2T[e] = ELEMENT_TYPE_QUAD
    else:
        raise ValueError("Unknown elements passed into mesh equivalencer.")

    return E2N, E2T, nodes
#}}}

def get_E2NormVec(nodes: Dict[int, List[float]], E2N): #{{{
    """Compute the normal vector elements"""
    E2NormVec = {}
    for EID in E2N:
        NodeIDs = E2N[EID]
        these_nodes = []
        for N in NodeIDs:
            # get the X coord of this node ID
            for nid, node in nodes.items():
                if nid == N:
                    x, y, z = node
                    these_nodes.append([x, y, z])
        # compute every normal vector possible
        N = these_nodes

        # Get coordinates of all four points
        P1 = np.array(N[0])
        P2 = np.array(N[1])
        P3 = np.array(N[2])
        P4 = np.array(N[3])

        # Get vectors encircling the element
        V12 = P2 - P1
        V23 = P3 - P2
        V34 = P4 - P3
        V41 = P1 - P4

        # Get all the cross products
        NV1 = np.cross(V12, V23)
        NV2 = np.cross(V23, V34)
        NV3 = np.cross(V34, V41)
        NV4 = np.cross(V41, V12)

        # Compute average of all these vectors
        NV = NV1 + NV2 + NV3 + NV4

        # Normalize the magnitude
        mag = (NV[0]**2 + NV[1]**2 + NV[2]**2)**0.5
        NV /= mag
        E2NormVec[EID] = [NV[0], NV[1], NV[2]]
    return E2NormVec
    #}}}

def get_N2NormVec(E2NormVec: Dict[int, List[float]],
                  E2N,
                  nodes: Dict[int, List[float]]) -> Dict[int, List[float]]: # {{{
    """
    Bug: 2021.10.24: mag can be zero if normals aren't consistent
    """
    N2NormVec = {}
    N2E = get_N2E(E2N)

    for NID in nodes:
        elms_with_this_node = N2E[NID]
        x = 0.
        y = 0.
        z = 0.
        for EID in elms_with_this_node:
            vector = E2NormVec[EID]
            x += vector[0]
            y += vector[1]
            z += vector[2]
        mag = ((x**2) + (y**2) + (z**2))**0.5
        if mag == 0:
            s = "zero magnitude normal vector. Normals misaligned."
            raise ValueError(s)
        x /= mag
        y /= mag
        z /= mag
        N2NormVec[NID] = [x, y, z]
    return N2NormVec
# }}}

def get_N2E(E2N: Dict[int, List[int]]) -> Dict[int, int]: # {{{
    """Turns the E2N around, giving a dict of N2E"""
    # if the node's not in N2E yet, prepare for it to be
    N2E = defaultdict(list)
    for EID, element in E2N.items():
        # go through nodes in every element
        for NID in element:
            # store the EID with that node ID we're on
            N2E[NID].append(EID)
    return dict(N2E)
# }}}

def get_new_nodes(N_layers: int,
                  thickness: float,
                  nodes: Dict[int, List[float]],
                  N2NormVec: Dict[int, List[float]]) -> Dict[int, List[float]]: # {{{
    # create nodes translated to the correct positions as new_nodes
    new_nodes = {}
    node_ID_offset = 0
    for layer in range(N_layers+1):
        # get vector magnitude
        mag = layer * (thickness / N_layers)
        for nid, node in nodes.items():
            vector = N2NormVec[nid]
            x = node[0] + mag * vector[0]
            y = node[1] + mag * vector[1]
            z = node[2] + mag * vector[2]
            new_nodes[nid + node_ID_offset] = [x, y, z]
        node_ID_offset += len(nodes)
    return new_nodes
# }}}

def get_new_E2N(E2N: Dict[int, List[int]],
                nodes: Dict[int, List[float]],
                N_layers: int) -> Dict[int, List[int]]: # {{{
    new_E2N = {}
    element_ID_offset = 0
    nnodes = len(nodes)
    for layer in range(N_layers):
        offset1 = layer * nnodes
        offset2 = (layer + 1) * nnodes
        for eid, element in E2N.items():
            N1 = element[0] + offset1
            N2 = element[1] + offset1
            N3 = element[2] + offset1
            N4 = element[3] + offset1

            N5 = element[0] + offset2
            N6 = element[1] + offset2
            N7 = element[2] + offset2
            N8 = element[3] + offset2
            new_EID = eid + element_ID_offset
            new_E2N[new_EID] = [N1, N2, N3, N4, N5, N6, N7, N8]
        element_ID_offset += len(E2N)
    return new_E2N
# }}}

def main(N_layers: int, thickness: float): # {{{
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
        raise ValueError("As of 2021.08.29, no support for thicken mode=1")

    E2N, E2T, nodes = get_E2N_nodes_and_E2T(mesh_objects_to_merge)

    # Construct element ID to normal vector data structure
    E2NormVec = get_E2NormVec(nodes, E2N)

    # Construct node ID to normal vector data structure
    N2NormVec = get_N2NormVec(E2NormVec, E2N, nodes)

    # create nodes translated to the correct positions as new_nodes
    new_nodes =  get_new_nodes(N_layers, thickness, nodes, N2NormVec)

    # create elements calling out the new_nodes
    new_E2N = get_new_E2N(E2N, nodes, N_layers)

    # Now have new_E2N and new_nodes

    # create new FemMesh container called thickened
    thickened = Fem.FemMesh()

    # add all of the nodes to new container
    for nid, node in new_nodes.items():
        x, y, z = node
        thickened.addNode(x, y, z, nid)

    # create the elements of this container
    for eid, element in new_E2N.items():
        thickened.addVolume([*element], eid)

    # set graphical object to render correctly
    doc = App.ActiveDocument
    obj = doc.addObject("Fem::FemMeshObject", "thickened")
    obj.FemMesh = thickened
    obj.Placement.Base = FreeCAD.Vector(0, 0, 0)
    obj.ViewObject.DisplayMode = "Faces, Wireframe & Nodes"
    obj.ViewObject.BackfaceCulling = False

    # render object
    doc.recompute()
# }}}

if __name__ == '__main__':
    form = Form()
