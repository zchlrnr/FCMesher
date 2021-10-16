# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem
from PySide import QtGui

Vector = App.Vector

class Form(QtGui.QDialog): # {{{
    """flip the true in __name__ == '__main__' to bypass the dialogue"""
    N_elms_X = 5
    N_elms_Y = 3
    
    def __init__(self): # {{{
        super(Form, self).__init__()
        self.setModal(True)
        self.makeUI()
    # }}}
        
    def makeUI(self): # {{{
        
        labelx = QtGui.QLabel('X elements')
        spinx = self.spinx = QtGui.QSpinBox()
        spinx.setValue(self.N_elms_X)
        spinx.setRange(1, 500)
        
        labely = QtGui.QLabel('Y elements')
        spiny = self.spiny = QtGui.QSpinBox()
        spiny.setValue(self.N_elms_Y)
        spiny.setRange(1, 500)

        btn = self.btn = QtGui.QPushButton('Mesh')
        btn.clicked.connect(self.make_mesh)
        
        layout = QtGui.QGridLayout()
        layout.addWidget(labelx, 0, 0)
        layout.addWidget(spinx, 1, 0)
        layout.addWidget(labely, 0, 1)
        layout.addWidget(spiny, 1, 1)
        layout.addWidget(btn, 2, 1)
        
        self.setLayout(layout)
        self.show()
    # }}}

    def get_values(self): # {{{
        return self.N_elms_X, self.N_elms_Y
    #}}}

    def make_mesh(self): #{{{
        self.N_elms_X = self.spinx.value()
        self.N_elms_Y = self.spiny.value()
        main(self.N_elms_X, self.N_elms_Y)
        self.close()
        #}}}
# }}}

def main(N_elms_X, N_elms_Y): # {{{
    ## gather edges from selection
    sel_edges = []
    for obj in Gui.Selection.getSelectionEx():
        if obj.HasSubObjects:
            for sub in obj.SubObjects:
                if isinstance(sub, Part.Edge):
                    sel_edges.append(sub)
        else:
            obj_edges = obj.Object.Shape.Edges
            if len(obj_edges) == 1:
                sel_edges.append(obj_edges[0])
    # Check that there are the correct number of selections
    if len(sel_edges) != 2:
        print("Select Two Edges", len(sel_edges))
        return
    Curve_01, Curve_02 = sel_edges

    # get the nodes on curve_01
    N_Curve_1 = get_nodes_from_curve(Curve_01, N_elms_X)

    # get the nodes on curve_02
    N_Curve_2 = get_nodes_from_curve(Curve_02, N_elms_X)
    
    # Make nodes by tracing the streamlines of the surface
    nodes = make_nodes_of_ruled_mesh(N_Curve_1, N_Curve_2, N_elms_Y)
    
    # Now to make the elements
    E2N = make_elements_of_ruled_mesh(N_elms_X, N_elms_Y)
    
    # computing E2Warp
    E2Warp = get_E2Warp(E2N, nodes)

    # assemble package to pass into correct_curve_order_for_warp
    #        1.) N_Curve_1
    #        2.) N_Curve_2
    #        3.) N_elms_Y
    #        4.) E2N
    #        5.) E2Warp
    #        6.) nodes
    warp_correction_pack = [N_Curve_1, N_Curve_2, N_elms_Y, E2N, E2Warp, nodes]
    nodes = correct_curve_order_for_warp(warp_correction_pack)

    # Now have E2N and Nodes array
    # Add all of the nodes to a container called "a"
    a = Fem.FemMesh()

    # add all of the nodes to container "a"
    for node in nodes:
        a.addNode(*node)
    # add all of the elements to container "a"
    for E in E2N:
        print(E)
        a.addFace(E[1:], E[0])
    
    # Making it render correctly
    doc = App.ActiveDocument
    obj = doc.addObject("Fem::FemMeshObject", "a")
    obj.FemMesh = a
    obj.Placement.Base = FreeCAD.Vector(0, 0, 0)
    obj.ViewObject.DisplayMode = "Faces, Wireframe & Nodes"
    obj.ViewObject.BackfaceCulling = False
    
    doc.recompute()
# }}}

def correct_curve_order_for_warp(*args): # {{{
    N_Curve_1 = args[0][0]
    N_Curve_2 = args[0][1]
    N_elms_Y = args[0][2]
    E2N = args[0][3]
    E2Warp = args[0][4]
    nodes = args[0][5]

    N_Curve_1_rev = N_Curve_1[::-1]

    # Make nodes of reversed curve 1 mesh
    nodes_rev = make_nodes_of_ruled_mesh(N_Curve_1_rev, N_Curve_2, N_elms_Y)

    # Make elements of reversed curve 1 mesh
    E2Warp_rev = get_E2Warp(E2N, nodes_rev)

    total_rev_warp = 0
    for E2W_rev in E2Warp_rev:
        total_rev_warp += E2W_rev[1]

    total_warp = 0
    for E2W in E2Warp:
        total_warp += E2W[1]

    # if there's more total warp in rev than regular, return nodes_rev
    if total_warp > total_rev_warp:
        print('reversed edge')
        return nodes_rev
    else:
        return nodes
# }}}

def get_E2Warp(E2N, nodes): # {{{
    """
    compute the warping of each element according to MSC Nastran definition
    According to MSC Nastran 2021 Reference Manual
    Warp Test: This test evaluates how far out of plane the four corner
    grid points are by measuring the distance of each point from a "mean"
    plane passing through the locations of the four points.
    The corner points are alternately H units above and H units below this
    mean plane. If the lengths of the diagonals of the element are denoted
    by D1 and D2, the warping coefficient is obtained from the equation
    WC = H/2*(D1+D2)
    If this value exceeds the tolerance, an informational message is produced.
    """
    # [EID, WarpingConstant]
    E2Warp = []
    # for each element, get the nodes
    for E in E2N:
        EID = E[0]
        NID1 = E[1]
        NID2 = E[2]
        NID3 = E[3]
        NID4 = E[4]
        # scrape out data and get coords of all nodes
        for n in nodes: 
            NID = n[3]
            if NID == NID1:
                n1 = n       # [x1, y1, z1, NID1]
            elif NID == NID2:
                n2 = n       # [x2, y2, z2, NID2]
            elif NID == NID3:
                n3 = n       # [x3, y3, z3, NID3]
            elif NID == NID4:
                n4 = n       # [x4, y4, z4, NID4]
        # need midpoint between n1 and n3
        m13x = (n1[0] + n3[0]) / 2
        m13y = (n1[1] + n3[1]) / 2
        m13z = (n1[2] + n3[2]) / 2
        # need midpoint between n2 and n4
        m24x = (n2[0] + n4[0]) / 2
        m24y = (n2[1] + n4[1]) / 2
        m24z = (n2[2] + n4[2]) / 2
        # "H" is half the distance between these points
        dmx = m24x - m13x
        dmy = m24y - m13y
        dmz = m24z - m13z
        H = 0.5 * (((dmx ** 2) + (dmy ** 2) + (dmz ** 2))**0.5)
        # computing D1
        dD1x = n3[0] - n1[0]
        dD1y = n3[1] - n1[1]
        dD1z = n3[2] - n1[2]
        D1 = ((dD1x ** 2)+(dD1y ** 2)+(dD1z ** 2)) ** 0.5
        # computing D2
        dD2x = n4[0] - n2[0]
        dD2y = n4[1] - n2[1]
        dD2z = n4[2] - n2[2]
        D2 = ((dD2x ** 2)+(dD2y ** 2)+(dD2z ** 2)) ** 0.5
        WC = H / 2 * (D1 + D2)
        # Append EID, WC to E2Warp
        E2Warp.append([EID, WC])
    return E2Warp
# }}}
    
def make_elements_of_ruled_mesh(N_elms_X, N_elms_Y): # {{{
    Nx = N_elms_X + 1
    Ny = N_elms_Y + 1
    EID = 0
    E2N = []
    for j in range(Ny):
        for i in range(Nx):
            NID = 1 + Nx*j + i
            # skip rolling over elements
            if i == (Nx - 1) or j == (Ny - 1):
                continue
            EID += 1
            N1 = NID
            N2 = 1 + Nx*(j+1) + i
            N3 = N2 + 1
            N4 = N1 + 1
            E2N.append([EID, N1, N2, N3, N4])
    return E2N
# }}}

def get_nodes_from_curve(Curve_Handle, N_elms): #{{{
    return tuple((n.x, n.y, n.z) for n in Curve_Handle.discretize(N_elms+1))
# }}}

def make_nodes_of_ruled_mesh(Nodes_1, Nodes_2, N_elms_Y): # {{{
    # Make nodes by tracing the streamlines of the surface
    nodes = []
    # first set of nodes will be from N_Curve_1
    NID = 0
    for i in range(N_elms_Y+1):
        for j in range(len(Nodes_1)):
            NID += 1
            # Get coordinates of the node on Curve 1
            x1, y1, z1 = Nodes_1[j]
            # Get coordinates of the node on Curve 2
            x2, y2, z2 = Nodes_2[j]
            # get location of current node in ruled surf
            x = (x2-x1)*(i/N_elms_Y) + x1
            y = (y2-y1)*(i/N_elms_Y) + y1
            z = (z2-z1)*(i/N_elms_Y) + z1
            nodes.append([x, y, z, NID])
    return nodes
# }}}

if __name__ == '__main__':
    N_elms_X, N_elms_Y = 5, 3

    if True:
        form = Form()
    else:
        main(N_elms_X, N_elms_Y)

