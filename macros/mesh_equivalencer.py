import FreeCAD, Part, Fem
from PySide import QtGui
from scipy.spatial import KDTree

class Form(QtGui.QDialog): # {{{
    eq_tol = 1e-4  # equivolence tolerance
    def __init__(self): # {{{
        super(Form, self).__init__()
        self.setModal(True)
        self.makeUI()
    # }}}
    def makeUI(self): # {{{
        label_eq_tolerance = QtGui.QLabel('Equivolencing Tolerance')
       
        eq_tolerance_field = self.eq_tolerance = QtGui.QLineEdit(str(self.eq_tol))

        btn = self.btn = QtGui.QPushButton('Equivolence')
        btn.clicked.connect(self.equivolence)
        
        layout = QtGui.QGridLayout()
        layout.addWidget(label_eq_tolerance, 0, 0)
        layout.addWidget(eq_tolerance_field, 0, 1)
        layout.addWidget(btn, 0, 2)
        
        self.setLayout(layout)
        self.show()
    # }}}
    def equivolence(self): # {{{
        main(self.eq_tol)
        self.close()
    # }}}
#}}}

def main(eq_tol):
    '''
    Goal: Take two selected femmeshes, equivalence them together
    - [X] check that a thing is selected
    - [X] check that there are only two selected things
    - [X] check that the selected thing is a FemMesh or PythonFemMesh Object
    - [X] put the FemMesh object in a variable called original_mesh
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
        s = "Need to select two FemMesh or FemMeshPython objects."
        raise ValueError(s)

    # store the original mesh in a variable original_mesh
    mesh_A_contents = Gui.Selection.getSelectionEx()[0].Object.FemMesh
    mesh_A_label = Gui.Selection.getSelectionEx()[0].Object.Label
    mesh_B_contents = Gui.Selection.getSelectionEx()[1].Object.FemMesh
    mesh_B_label = Gui.Selection.getSelectionEx()[1].Object.Label



if __name__ == '__main__':
    form = Form()
