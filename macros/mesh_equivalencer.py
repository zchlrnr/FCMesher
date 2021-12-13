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

def main(eq_tol):
    '''
    Goal: Take two selected femmeshes, equivalence them together
    - [X] throw error if no FemMeshes are selected
    - [X] throw error if a number other than two FemMeshes is selected
    - [X] store meshes and labels in variables
    - [X] check if any nodes in mesh_A are within tolerance of mesh_B
    - [X] get pairs of matching nodes across meshes
    - [X] throw message if no viable pairs exist
    - [ ] create new unified primitives data (nodes, E2N, and E2T)
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

if __name__ == '__main__':
    form = Form()
