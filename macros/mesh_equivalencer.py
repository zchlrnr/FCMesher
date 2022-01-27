import FreeCAD, Part, Fem
from PySide import QtGui
from scipy.spatial import KDTree
import numpy as np

class Form(QtGui.QDialog): # {{{
    """
    Make modal form for equivolencing
    - [ ] Make label for equivolencing tolerance
    - [ ] 
    """
    eq_tol = 1e-4  # equivolence tolerance
    def __init__(self): # {{{
        super(Form, self).__init__()
        self.setModal(True)
        self.makeUI()
    # }}}
    def makeUI(self): # {{{
        # make equivolencing tolerance label and field
        label_eq_tol = QtGui.QLabel('Equivolencing Tolerance')
        eq_tol_field = self.eq_tol_field = QtGui.QLineEdit(str(self.eq_tol))

        # make equivolence button, set it to call equivolence function
        btn = self.btn = QtGui.QPushButton('Equivolence')
        btn.clicked.connect(self.equivolence)

        # get current unit system (there are 9 of them total as of 2021.12.12)
        unit_schema_path = "User parameter:BaseApp/Preferences/Units"
        unit_schema = FreeCAD.ParamGet(unit_schema_path).GetInt("UserSchema")
        unit_schema_as_string = FreeCAD.Units.listSchemas(unit_schema)

        # create layout
        layout = QtGui.QGridLayout()
        layout.addWidget(label_eq_tol, 0, 0)
        layout.addWidget(eq_tol_field, 0, 1)
        layout.addWidget(btn, 0, 2)
        
        self.setLayout(layout)
        self.show()
    # }}}
    def equivolence(self): # {{{
        self.eq_tol = float(self.eq_tol_field.text())
        main(self.eq_tol)
        self.close()
    # }}}
#}}}

def get_NID_replacement_pairs(mesh_A_contents, mesh_B_contents, eq_tol): # {{{
    """
    Goal: return the pairs of nodes between meshes that are within tolerance
    - [X] get number of nodes in A
    - [X] assembly new node IDs into a list
    - [X] construct list of coordinates mapped identically to new IDs
    - [X] convert coords to an nparray
    - [X] construct a tree of the nodal data
    - [X] query pairs of nodes to see if any are in tolerance, convert to list
    - [X] if there's no pairs, return as is
    - [X] if there are some pairs, check that not going to collapse elements
    - [X] return pairs, the hash tables, and the new node ID list
    """
    # get number of nodes in A
    N_nodes_A = len(mesh_A_contents.Nodes) # number of nodes in A

    # get mapping of old IDs to new IDs
    old_ID_to_new_A = {} # hash table of old ID in mesh A to new ID
    for NID in mesh_A_contents.Nodes.keys():
        old_ID_to_new_A[NID] = NID
    old_ID_to_new_B = {} # hash table of old ID in mesh B to new ID
    for NID in mesh_B_contents.Nodes.keys():
        old_ID_to_new_B[NID] = NID + N_nodes_A

    # assemble new node IDs together into a list
    new_NIDs = [*list(old_ID_to_new_A.values()),*list(old_ID_to_new_B.values())]

    # construct list of coordinates mapped identically to new IDs
    node_coords = []
    for i in mesh_A_contents.Nodes.values():
        node_coords.append(list(i))
    for i in mesh_B_contents.Nodes.values():
        node_coords.append(list(i))
    # convert coords to an nparray
    node_coords = np.array(node_coords)

    # construct a tree containing the nodal data
    tree = KDTree(node_coords)

    # query pairs of nodes in tree to see if any are within tolerance
    pairs = tree.query_pairs(eq_tol)

    # convert pair list to list of tuples
    pairs = list(pairs) # (the lower ID will always be on the right)

    # prepare data package to pass back
    data_back = {}
    data_back['old_A'] = old_ID_to_new_A
    data_back['old_B'] = old_ID_to_new_B
    data_back['new_NIDs'] = new_NIDs
    data_back['pairs'] = pairs

    # if pairs is empty, return now
    if len(pairs) == 0:
        return data_back

    # check that no two nodes of each pair are in the same mesh body
    for p in pairs:
        if new_NIDs[p[0]] not in old_ID_to_new_A.values():
            s = "equivolence with tolerance of " + str(eq_tol)
            s = s + " would collapse elements in mesh_B"
            raise ValueError(s)
        if new_NIDs[p[1]] not in old_ID_to_new_B.values():
            s = "equivolence with tolerance of " + str(eq_tol)
            s = s + " would collapse elements in mesh_A"
            raise ValueError(s)

    return data_back

#}}}

def get_nodes_from_FemMesh(mesh_object): # {{{
    """
    Goal: return nodes dict
    """
    nodes = {}
    NIDs = mesh_object.Nodes.keys()
    for N in NIDs:
        nodes[N] = list(mesh_object.Nodes[N])
    return nodes
# }}}

def get_E2N_from_FemMesh(mesh_object): # {{{
    """
    Goal: create and return E2N from a single mesh_object
    """
    E2N = {}    # Element to Node ID
    if mesh_object.EdgeCount != 0: 
        s = "Edges not supported as of 2021.10.16"
        print(s)
    if mesh_object.TriangleCount != 0: 
        EID = max(E2N.keys(), default=0)        # Element ID
        for face in mesh_object.Faces:
            # if it's 3 noded, it's a TRIA3 element
            if len(mesh_object.getElementNodes(face)) == 3:
                EID += 1
                OG = list(mesh_object.getElementNodes(face))    # original order
                E2N[EID] = [OG[0], OG[1], OG[2]]  # correct order?
                E2N[EID] = list(mesh_object.getElementNodes(face))
    if mesh_object.QuadrangleCount != 0: 
        EID = max(E2N.keys(), default=0)        # Element ID
        for face in mesh_object.Faces:
            # if it's 4 noded, it's a QUAD4 element
            if len(mesh_object.getElementNodes(face)) == 4:
                EID += 1
                # un-salome'ifying
                OG = list(mesh_object.getElementNodes(face))    # original order
                E2N[EID] = [OG[0], OG[3], OG[2], OG[1]]  # correct order
                E2N[EID] = list(mesh_object.getElementNodes(face))
    if mesh_object.HexaCount != 0:       
        EID = max(E2N.keys(), default=0)        # Element ID
        for volume in mesh._objectVolumes:
            # if it's 8 noded, it's a CHEXA element with 8 nodes
            if len(mesh_object.getElementNodes(volume)) == 8:
                EID += 1
                # un-salome'ifying
                OG = list(mesh_object.getElementNodes(volume))
                E2N[EID] = \
                [OG[6], OG[7], OG[4], OG[5], OG[2], OG[3], OG[0], OG[1]]
            else:
                s = "As of 2021.10.17, CHEXA 20 elements are not supported."
                raise ValueError(s)
    if mesh_object.TetraCount != 0:      
        EID = max(E2N.keys(), default=0)        # Element ID
        for volume in mesh_object.Volumes:
            # if it's 10 noded, it's a CTETRA element with 10 nodes
            if len(mesh_object.getElementNodes(volume)) == 10:
                EID += 1
                # un-salome'ifying
                OG = list(mesh_object.getElementNodes(volume))
                E2N[EID] = [OG[3], OG[2], OG[0], OG[1], OG[9], OG[6],\
                            OG[7], OG[8], OG[5], OG[4]]
            else:
                EID += 1
                OG = list(mesh_object.getElementNodes(volume))
                E2N[EID] = OG.reverse()
    if mesh_object.PyramidCount != 0: 
        s = "Pyramids not supported as of 2021.10.16"
        raise ValueError(s)
    if mesh_object.PrismCount != 0: 
        s = "Prisms not supported as of 2021.10.16"
        raise ValueError(s)
    return E2N
# }}}

def main(eq_tol): # {{{
    '''
    {{{ Goal: Take two selected femmeshes, equivalence them together
    - [X] throw error if no FemMeshes are selected
    - [X] throw error if a number other than two FemMeshes is selected
    - [X] store meshes and labels in variables
    - [X] check if any nodes in mesh_A are within tolerance of mesh_B
    - [X] get pairs of matching nodes across meshes
    - [X] throw message if no viable pairs exist
    - [X] create nodes of mesh_A and mesh_B
    - [X] create E2N of mesh_A and mesh_B
    - [ ] offset node IDs in nodes_B
    }}}
    '''
    # check that a thing is selected
    N_things_selected = 0
    for obj in Gui.Selection.getSelectionEx():
        if obj.TypeName == "Fem::FemMeshObject":
            N_things_selected += 1
        elif obj.TypeName == "Fem::FemMeshObjectPython":
            N_things_selected += 1
    if N_things_selected == 0:
        raise ValueError("No FemMeshObjects or FemMeshObjectPythons Selected.")

    # check that only two objects are selected
    if N_things_selected != 2:
        s = "As of 2021.12.12, only two FemMesh objects can be selected."
        raise ValueError(s)

    # store the original mesh in a variable original_mesh
    mesh_A_contents = Gui.Selection.getSelectionEx()[0].Object.FemMesh
    mesh_A_label = Gui.Selection.getSelectionEx()[0].Object.Label
    mesh_B_contents = Gui.Selection.getSelectionEx()[1].Object.FemMesh
    mesh_B_label = Gui.Selection.getSelectionEx()[1].Object.Label

    # get pairs, and check if any nodes in mesh_A are within tolerance of mesh_B
    data_back = get_NID_replacement_pairs(mesh_A_contents, mesh_B_contents, eq_tol)
    old_nodes_in_A = data_back['old_A']
    old_nodes_in_B = data_back['old_B']
    new_NIDs = data_back['new_NIDs']
    pairs = data_back['pairs']

    # if no pairs exist, print that no pairs exist, and return 
    if len(pairs) == 0:
        s = "With a tolerance of " + str(eq_tol) + ", no pairs exist."
        print(s)
        return

    # get nodes_A and nodes_B
    nodes_A = get_nodes_from_FemMesh(mesh_A_contents)
    nodes_B = get_nodes_from_FemMesh(mesh_B_contents)

    # get E2N_A and E2N_B
    E2N_A = get_E2N_from_FemMesh(mesh_A_contents)
    E2N_B = get_E2N_from_FemMesh(mesh_B_contents)

    #  offsetting NIDs in nodes_B
    nodes_B_new = {}
    for NID in nodes_B.keys():
        nodes_B_new[NID + max(nodes_A.keys())] = nodes_B[NID]
    nodes_B = nodes_B_new

 # }}}

if __name__ == '__main__':
    form = Form()
