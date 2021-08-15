# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem

def main():
    # gather edges from selection
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

    # Knowledge From Here
    # https://wiki.freecadweb.org/Topological_data_scripting

    # I can get a list of "N" points by calling 'valueAt' on "Arc_Length"
    N_elms_X = 2
    N_elms_Y = 2

    # get the nodes on curve_01
    Nodes_On_Curve_1 = get_nodes_from_curve(Curve_01, N_elms_X)

	# get the nodes on curve_02
    Nodes_On_Curve_2 = get_nodes_from_curve(Curve_02, N_elms_X)
    
    # Make nodes by tracing the streamlines of the surface
    nodes = make_nodes_of_ruled_mesh(Nodes_On_Curve_1, Nodes_On_Curve_2, N_elms_Y)
    
    # Now to make the elements
    E2N = make_elements_of_ruled_mesh(N_elms_X, N_elms_Y)
    
    # Now have E2N and Nodes array
    # Add all of the nodes to a container called "a"
    a = Fem.FemMesh()

    # add all of the nodes to container "a"
    for node in nodes:
        a.addNode(*node)
    # add all of the elements to container "a"
    for E in E2N:
        print(E)
        a.addFace([E[1],E[2],E[3],E[4]],E[0])
    #return
    
    # Making it render correctly
    obj = App.ActiveDocument.addObject("Fem::FemMeshObject", "a")
    obj.FemMesh = a
    obj.Placement.Base = FreeCAD.Vector(0, 0, 0)
    obj.ViewObject.DisplayMode = "Faces, Wireframe & Nodes"
    obj.ViewObject.BackfaceCulling = False

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

def get_nodes_from_curve(Curve_Handle, N_elms): # {{{
    return tuple((n.x, n.y, n.z) for n in Curve_Handle.discretize(N_elms+1))
# }}}

def make_nodes_of_ruled_mesh(Nodes_1, Nodes_2, N_elms_Y): # {{{
    # Make nodes by tracing the streamlines of the surface
    nodes = []
    # first set of nodes will be from Nodes_On_Curve_1
    NID = 0
    for i in range(N_elms_Y+1):
        for j in range(len(Nodes_1)):
            NID = NID + 1
            # Get coordinates of the node on Curve 1
            x1 = Nodes_1[j][0]
            y1 = Nodes_1[j][1]
            z1 = Nodes_1[j][2]
            # Get coordinates of the node on Curve 2
            x2 = Nodes_2[j][0]
            y2 = Nodes_2[j][1]
            z2 = Nodes_2[j][2]
            # get location of current node in ruled surf
            x = (x2-x1)*(i/N_elms_Y) + x1
            y = (y2-y1)*(i/N_elms_Y) + y1
            z = (z2-z1)*(i/N_elms_Y) + z1
            nodes.append([x,y,z,NID])
    return nodes
# }}}

if __name__ == '__main__':
    main()

