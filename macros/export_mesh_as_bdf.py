# App = FreeCAD, Gui = FreeCADGui
import FreeCAD, Part, Fem
from PySide import QtGui
from copy import copy as copy

def get_N2E(E2N): # {{{
    """ Turns the E2N around, giving a dict of N2E
    """
    N2E = {}
    for EID, Element in E2N.items():
        # go through nodes in every element
        for NID in Element:
            # if the node's not in N2E yet, prepare for it to be
            if NID not in N2E:
                N2E[NID] = []
            # store the EID with that node ID we're on
            N2E[NID].append(EID)
    return N2E
# }}}
def create_bulkdata_strings(nodes, E2N, E2T, E2P, P2M): #{{{
    """ Create giant list, with each entry being a line 
    """
    bulkdata = []
    bulkdata.append("BEGIN BULK")

    # Properties
    # Materials
    # Elements
    # Grids
    
    bulkdata.append(ENDDATA)
    return bulkdata
    # }}}
def main(): # {{{
    """ GOAL: {{{
    =========
    Export many mesh FemMesh objects as a bdf file with correct numbering
    - [X] Extract nodes per each FemMesh for many FemMeshes
    - [X] Extract E2N per each FemMesh for many FemMeshes
    - [X] Extract E2T per each FemMesh for many FemMeshes
    - [X] Create E2P per each FemMesh for many FemMeshes
          NOTE: Will create a property for each set of elements in each FemMesh
    - [X] Create P2M per each FemMesh for many FemMeshes
          NOTE: Will create a material for each set of elements in each FemMesh
    - [X] Assemble core data structures together, correcting numbering
    - [ ] Un-break Salomes nutty inside out elements
    NOTE: Performance can be improved by sorting "data" from largest to smallest
    }}}"""
    mesh_objects = [] 
    for obj in Gui.Selection.getSelectionEx():
        if obj.TypeName == "Fem::FemMeshObject":
            mesh_objects.append(obj.Object.FemMesh)
        elif obj.TypeName == "Fem::FemMeshObjectPython":
            mesh_objects.append(obj.Object.FemMesh)

    # if there is nothing selected, raise an error
    if len(mesh_objects) == 0:
        raise ValueError("No mesh entities selected.")

    # for each mesh object selected, assemble a master set of data
    # 'data' will comprise the core data structures:[nodes, E2N, E2T, E2P, P2M]

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
        NID = max(nodes.keys(), default=0) # Node ID
        for node in mesh.Nodes:
            NID += 1
            nodes[NID] = list(mesh.getNodeById(node))
        # get E2N, E2T, E2P, and P2M for this mesh
        if mesh.EdgeCount != 0: # {{{
            s = "Edges not supported as of 2021.10.16"
            raise ValueError(s)
            # }}}
        if mesh.TriangleCount != 0: # {{{
            s = "Triangles not supported as of 2021.10.16"
            raise ValueError(s)
            #}}}
        if mesh.QuadrangleCount !=-1: # Type 15 {{{
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
        if mesh.HexaCount != 0:      # Type 7 {{{
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
            # }}}
        if mesh.TetraCount != 0: # {{{
            s = "Tetras not supported as of 2021.10.16"
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
        data[mesh_number]['nodes'] = copy(nodes)
        data[mesh_number]['E2N'] = copy(E2N)
        data[mesh_number]['E2T'] = copy(E2T)
        data[mesh_number]['E2P'] = copy(E2P)
        data[mesh_number]['P2M'] = copy(P2M)

    # Combine contents of data together into singular data structures
    nodes = {}  # Node ID to location
    E2N = {}    # Element to Node ID
    E2T = {}    # Element to Type ID
    E2P = {}    # Element to Property ID
    P2M = {}    # Property to Material ID
    NID = 0
    for i, mesh_data in enumerate(data):
        if i == 0:
            # add first selected mesh to the core data, as it's empty right now
            nodes = copy(mesh_data["nodes"])
            E2N = copy(mesh_data["E2N"])
            E2T = copy(mesh_data["E2T"])
            E2P = copy(mesh_data["E2P"])
            P2M = copy(mesh_data["P2M"])
            continue
        # Add and update element IDs in E2N and E2T
        EID_lookup_table = {}   # returns new EID, given the old EID
        for element in mesh_data["E2N"].keys():
            # check if its ID needs to be updated
            if element in E2N:
                EID_old = element
                EID_new = max(E2N.keys()) + 1
                EID_lookup_table[EID_old] = EID_new
                E2N[EID_new] = mesh_data["E2N"][EID_old]
                E2T[EID_new] = mesh_data["E2T"][EID_old]
                E2P[EID_new] = mesh_data["E2P"][EID_old]
            else:
                EID_lookup_table[element] = element
                E2N[element] = mesh_data["E2N"][element]
                E2T[element] = mesh_data["E2T"][element]
                E2P[element] = mesh_data["E2P"][element]

        # Add and update node IDs in nodes and E2N
        # get N2E to accelerate update of node IDs
        N2E = get_N2E(E2N)
        for node in mesh_data["nodes"].keys():
            if node in nodes.keys():
                NID_old = node
                NID_new = max(nodes.keys()) + 1
                # replace node ID in nodes
                nodes[NID_new] = mesh_data["nodes"][NID_old]
                # replace node ID in E2N
                for EID in N2E[NID_old]:
                    old_nodes_in_this_elm = E2N[EID]
                    new_nodes_in_this_elm = []
                    for N in old_nodes_in_this_elm:
                        if N == NID_old:
                            new_nodes_in_this_elm.append(NID_new)
                        else:
                            new_nodes_in_this_elm.append(N)
                    E2N[EID] = new_nodes_in_this_elm
            else:
                nodes[node] = mesh_data["nodes"][node]

        # Add and update property IDs in E2P and P2M
        props_in_current_E2P = list(set(E2P.values()))
        props_in_current_mesh_data = list(set(mesh_data["E2P"].values()))
        # if there's more than 1 prop in current mesh data, idk what to do yet
        if len(props_in_current_mesh_data) > 1:
            raise ValueError("Not sure how to deal with mutli-prop meshes yet")

        mats_in_current_P2M = list(set(P2M.values()))
        mats_in_current_mesh_data = list(set(mesh_data["P2M"].values()))
        if len(mats_in_current_mesh_data) > 1:
            raise ValueError("Not sure how to deal with mutli-mat meshes yet")

        new_PID = max(props_in_current_E2P) + 1
        new_MID = max(mats_in_current_P2M) + 1
        for old_EID in mesh_data["E2P"].keys():
            # check if the element in E2N needs its PID updated
            new_EID = EID_lookup_table[old_EID]
            E2P[new_EID] = new_PID
            P2M[new_PID] = new_MID


    # As a placeholder for later, two extra structures shall exist
    # Those are the P2T and M2T, Property to type of property, and 

    # Now have nodes, E2N, E2T, E2P, and P2M, for a combined thingy
    # Mystran default supported property cards include
        # 0D: PELAS, PBUSH
        # 1D: PBAR, PBARL, PROD
        # 2D: PSHEAR, PSHELL, PCOMP, PCOMP1
        # 3D: PSOLID
    # Mystran default supported material cards include
        # MAT1, MAT2, MAT8, MAT9, PMASS
    # As of 2021.10.16, now deciding to use, by default
        # for 1D Elements: PBUSH and None
        # for 2D Elements: PSHELL and MAT1
        # for 3D Elements: PSOLID
    
    # Attempting to store bulkdata in giant string now
    bulkdata_strings = create_bulkdata_strings(nodes, E2N, E2T, E2P, P2M)
    #}}}

if __name__ == '__main__':
    main()
