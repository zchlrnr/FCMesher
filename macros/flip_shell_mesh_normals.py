import FreeCAD, Part, Fem
from PySide import QtGui
import copy

def check_that_a_FemMesh_object_is_selected(gui_selection): # {{{
    '''
    Check that a thing is selected
    '''
    N_things_selected = 0
    for obj in gui_selection:
        if obj.TypeName == "Fem::FemMeshObject":
            N_things_selected += 1
        elif obj.TypeName == "Fem::FemMeshObjectPython":
            N_things_selected += 1
    if N_things_selected == 0:
        raise ValueError("No FemMeshObjects or FemMeshObjectPythons Selected.")
    return N_things_selected
    # }}}

def get_data_from_mesh_objects(mesh_objects): # {{{
    """
    Bug observed on 2021.10.24:
        If mesh does not have compactly numbered nodes, this crushes its numbering
    """
    # get 'data' from mesh objects
    data = []
    for i in range(len(mesh_objects)):
        data.append({})
    for mesh_number, mesh in enumerate(mesh_objects): 
        # preallocate popualted data structures
        nodes = {}  # Node ID to location
        E2N = {}    # Element to Node ID
        E2T = {}    # Element to Type ID
        E2P = {}    # Element to Property ID
        P2M = {}    # Property to Material ID
        # get nodes for this mesh 
        #NID = max(nodes.keys(), default=0) # Node ID
        # not sure why I was doing that.^^
        # that results in the 2021.10.24 bug.
        for node in mesh.Nodes:
            #NID += 1
            NID = node
            nodes[NID] = list(mesh.getNodeById(node))
        # get E2N, E2T, E2P, and P2M for this mesh
        if mesh.EdgeCount != 0: # {{{
            s = "Edges not supported as of 2021.10.16"
            print(s)
            # }}}
        if mesh.TriangleCount != 0: # Type 20 {{{
            EID = max(E2N.keys(), default=0)        # Element ID
            PID = max(E2P.keys(), default=0) + 1    # Property ID
            MID = max(P2M.keys(), default=0) + 1    # Material ID
            for face in mesh.Faces:
                # if it's 3 noded, it's a TRIA3 element
                if len(mesh.getElementNodes(face)) == 3:
                    EID += 1
                    OG = list(mesh.getElementNodes(face))    # original order
                    E2N[EID] = [OG[0], OG[1], OG[2]]  # correct order?
                    E2N[EID] = list(mesh.getElementNodes(face))
                    E2T[EID] = 20
                    E2P[EID] = PID
                    P2M[PID] = MID
            #}}}
        if mesh.QuadrangleCount != 0: # Type 15 {{{
            EID = max(E2N.keys(), default=0)        # Element ID
            PID = max(E2P.keys(), default=0) + 1    # Property ID
            MID = max(P2M.keys(), default=0) + 1    # Material ID
            for face in mesh.Faces:
                # if it's 4 noded, it's a QUAD4 element
                if len(mesh.getElementNodes(face)) == 4:
                    EID += 1
                    # un-salome'ifying
                    OG = list(mesh.getElementNodes(face))    # original order
                    E2N[EID] = [OG[0], OG[3], OG[2], OG[1]]  # correct order
                    E2N[EID] = list(mesh.getElementNodes(face))
                    E2T[EID] = 15
                    E2P[EID] = PID
                    P2M[PID] = MID
            # }}}
        if mesh.HexaCount != 0:       # Type 7 {{{
            EID = max(E2N.keys(), default=0)        # Element ID
            PID = max(E2P.keys(), default=0) + 1    # Property ID
            MID = max(P2M.keys(), default=0) + 1    # Material ID
            for volume in mesh.Volumes:
                # if it's 8 noded, it's a CHEXA element with 8 nodes
                if len(mesh.getElementNodes(volume)) == 8:
                    EID += 1
                    # un-salome'ifying
                    OG = list(mesh.getElementNodes(volume))
                    E2N[EID] = \
                    [OG[6], OG[7], OG[4], OG[5], OG[2], OG[3], OG[0], OG[1]]
                    E2T[EID] = 7
                    E2P[EID] = PID
                    P2M[PID] = MID
                else:
                    s = "As of 2021.10.17, CHEXA 20 elements are not supported."
                    raise ValueError(s)
            # }}}
        if mesh.TetraCount != 0:      # Type 19 {{{
            EID = max(E2N.keys(), default=0)        # Element ID
            PID = max(E2P.keys(), default=0) + 1    # Property ID
            MID = max(P2M.keys(), default=0) + 1    # Material ID
            for volume in mesh.Volumes:
                # if it's 10 noded, it's a CTETRA element with 10 nodes
                if len(mesh.getElementNodes(volume)) == 10:
                    EID += 1
                    # un-salome'ifying
                    OG = list(mesh.getElementNodes(volume))
                    E2N[EID] = [OG[3], OG[2], OG[0], OG[1], OG[9], OG[6],\
                                OG[7], OG[8], OG[5], OG[4]]
                    E2T[EID] = 19
                    E2P[EID] = PID
                    P2M[PID] = MID
                else:
                    s = "As of 2021.10.17, CTETRA 4 elements are not supported."
                    raise ValueError(s)
            # }}}
        if mesh.PyramidCount != 0: # {{{
            s = "Pyramids not supported as of 2021.10.16"
            raise ValueError(s)
             # }}}
        if mesh.PrismCount != 0: # {{{
            s = "Prisms not supported as of 2021.10.16"
            raise ValueError(s)
            # }}}
        data[mesh_number]['nodes'] = copy.deepcopy(nodes)
        data[mesh_number]['E2N'] = copy.deepcopy(E2N)
        data[mesh_number]['E2T'] = copy.deepcopy(E2T)
        data[mesh_number]['E2P'] = copy.deepcopy(E2P)
        data[mesh_number]['P2M'] = copy.deepcopy(P2M)
    return data
# }}}

def main():
    '''
    Goal: Take the selected femmesh object, and flip the normals
    - [X] check that a FemMesh object is selected
    - [X] check that there is only one selected thing
    - [X] check that the selected thing is a FemMesh or PythonFemMesh Object
    - [X] put the FemMesh object in a variable called original_mesh
    - [X] construct mesh primitives from original mesh
    - [X] check that types present are allowed (15, 16, 20, or 21)
    - [X] make a new E2N with the order of nodes reversed
    - [X] Add and show the FemMesh thing
    '''
    # check that a FemMesh object is selected
    gui_selection = Gui.Selection.getSelectionEx()
    N_things_selected = check_that_a_FemMesh_object_is_selected(gui_selection)

    # check that only one object is selected
    if N_things_selected != 1:
        s = "More than one FemMeshObjects or FemMeshObjectPythons Selected."
        raise ValueError(s)

    # store the original mesh in a variable original_mesh
    original_mesh = Gui.Selection.getSelectionEx()[0].Object
    original_mesh_contents = original_mesh.FemMesh
    original_mesh_label = original_mesh.Label

    # construct mesh primitives from original mesh; recall it's only one mesh
    data = get_data_from_mesh_objects([original_mesh_contents])[0]

    # check that type is 15, 16, 20, or 21 (all the shells in mystran)
    # 15/16 == CQUAD4(K)
    # 20/21 == CTRIA3(K)
    for EID in data['E2T'].keys():
        Type = data['E2T'][EID]
        if Type not in [15, 16, 20, 21]:
            s = "As of 2021.12.11, only types 15(CQUAD4), 16(CQUAD4K), \n"
            s = s + "20(CTRIA3), and 21(CTRIA3K) are supported."
            raise ValueError(s)

    # make new E2N with node order reversed
    flipped_normals_E2N = {}
    for EID in data['E2N'].keys():
        nodes_in_this_element = data['E2N'][EID]
        flipped_node_order = []
        for n in reversed(nodes_in_this_element):
            flipped_node_order.append(n)
        flipped_normals_E2N[EID] = flipped_node_order

    # add new FemMesh Object
    a = Fem.FemMesh()
    for node in data['nodes'].keys():
        a.addNode(*data['nodes'][node], node)

    # add all of the elements 
    for EID in flipped_normals_E2N.keys():
        print(EID)
        print(flipped_normals_E2N[EID])
        print(*flipped_normals_E2N[EID])
        a.addFace([*flipped_normals_E2N[EID]], EID)

    new_mesh_label = original_mesh_label + "_flipped"
    obj = FreeCAD.ActiveDocument.addObject("Fem::FemMeshObject",name=new_mesh_label)
    obj.FemMesh = a
    obj.Placement.Base = FreeCAD.Vector(0, 0, 0)
    obj.ViewObject.DisplayMode = "Faces, Wireframe & Nodes"
    obj.ViewObject.BackfaceCulling = True
    App.ActiveDocument.recompute()

if __name__ == '__main__':
    main()
