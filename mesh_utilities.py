import re
import math as m
import numpy as np

def solid_mesh_by_thickened_shell_mesh(*args): # {{{
    """ Sweeps shell elements along node normals into CHEXA/CPENTA #{{{
    - [X] 2021.08.14 | Allow definition of 3 point quadratic curves
    - [X] 2021.08.14 | Make shell element E2N rules between curves
    - [X] 2021.08.14 | Make nodes of shell element mesh between curves
    - [X] 2021.08.14 | Compute the element normal vectors
    - [X] 2021.08.14 | Compute the nodal normal vectors
    - [X] 2021.08.14 | Make nodes of new hex elements
    - [X] 2021.08.14 | Make hex element E2N
    - [X] 2021.08.14 | Define concept of E2T (element to type ID)
                       ideally be compliant with MSC Nastran
                       (wasn't compliant with MSC Nastran. No biggie.)
    - [X] 2021.08.14 | Refactor hard coded shell mesh to reside in a function
    - [X] 2021.08.14 | Write out mesh bdf from E2N, nodes, and E2T
    - [X] 2021.08.15 | Be able to receive a mesh instead of making one
    - [X] 2021.08.15 | Improve performance of get_N2NormVec
    - [ ] XXXX.XX.XX | Calibrate to return False if failed. True if works.
    - [ ] XXXX.XX.XX | Make ID offsetting routine that reads arguments in
                       that can offset both element IDs and node IDs
    - [ ] XXXX.XX.XX | Be able to compute E2NormVec for CTRIA elms with 3 nodes
    - [ ] XXXX.XX.XX | Be able to compute N2NormVec for CTRIA elms with 3 nodes
    """ # }}}
    if len(args[0]) == 0:
        print("Error in loft_solid_mesh.")
        print("No arguments passed into loft_solid_mesh function.")
        print("As of 2021.08.14, no behavior defined for this case.")
        return False
    elif len(args[0]) == 4:
        thickness = args[0][0]
        nodes = args[0][1]
        E2N = args[0][2]
        E2T = args[0][3]
    else:
        print("Error in loft_solid_mesh.")
        print("No defined behavior for number of arguments passed in.")
        return False

    # Construct element ID to normal vector data structure
    E2NormVec = get_E2NormVec(nodes, E2N)

    # Construct node ID to normal vector data structure
    N2NormVec = get_N2NormVec(E2NormVec, E2N, nodes)

    # create nodes translated to the correct positions
    nodes_offset = create_thickened_nodes(nodes, thickness, N2NormVec)

    # create E2N on the new nodes
    E2N_offset = create_thickened_E2N(E2N, nodes)

    # create E2T_offset on the new elements
    E2T_offset = {}
    for EID in E2N_offset:
        if len(E2N_offset[EID]) == 8:
            E2T_offset[EID] = 7
        elif len(E2N_offset[EID]) == 6:
            E2T_offset[EID] = 14
        else:
            print("Error in solid_mesh_lofter.")
            print("Unknown solid element type requesting E2T in E2T_offset.")
            return False

    # writing out thickened bdf of solid elements
    did_it_work = write_out_thickened_bdf(nodes_offset, E2N_offset, E2T_offset)
    return did_it_work
# }}}

def write_out_thickened_bdf(nodes_offset, E2N, E2T): # {{{
    """ Write out primitive bdf of thickened solids from mesh
    Void type function. Has no return statement.
    Two element types anticipated are 7 and 14 for CHEXA and PENTA
    """
    E2N_offset = E2N
    E2T_offset = E2T

    # open file to write to
    filename = "thickened_shell_mesh.bdf"
    f = open(filename,"w")
    f.write("BEGIN BULK\n")
    f.close()

    # Write all of the gridpoints
    write_gridpoint_data_to_file(filename, nodes_offset)

    # Writing dummy PSOLID card
    PID = 1
    f = open(filename, "a")
    f.write("PSOLID   " + str(PID) + "       1\n")
    f.close()

    # Writing dummy MAT1 card
    MID = 1
    f = open(filename, "a")
    f.write("MAT1     " + str(MID) + "      10.0E6           0.33    0.1\n")
    f.close()

    # Write all of the elements
    write_hex_and_pent_data(filename, E2N_offset, E2T_offset, MID, PID)

    # Write enddata
    f = open(filename, "a")
    f.write("ENDDATA")
    f.close
# }}}

def write_hex_and_pent_data(filename, E2N, E2T, MID, PID): # {{{
    E2N_offset = E2N
    E2T_offset = E2T
    f = open(filename, "a")
    for EID in list(E2N_offset.keys()):
        t = E2T_offset[EID]
        if t == 7:
            # this is a CHEXA element 
            if len(E2N_offset[EID]) == 8:
                # It's a HEX8
                L = "CHEXA   " 
                L += create_padded_bulkdata_field(EID)
                L += create_padded_bulkdata_field(PID)
                L += create_padded_bulkdata_field(E2N_offset[EID][0])  # N1
                L += create_padded_bulkdata_field(E2N_offset[EID][1])  # N2
                L += create_padded_bulkdata_field(E2N_offset[EID][2])  # N3
                L += create_padded_bulkdata_field(E2N_offset[EID][3])  # N4
                L += create_padded_bulkdata_field(E2N_offset[EID][4])  # N5
                L += create_padded_bulkdata_field(E2N_offset[EID][5])  # N6
                L += "\n"
                L += " " * 8
                L += create_padded_bulkdata_field(E2N_offset[EID][6])  # N7
                L += create_padded_bulkdata_field(E2N_offset[EID][7])  # N8
                L += "\n"
                f.write(L)
            elif len(E2N_offset[EID]) == 20:
                # It's a HEX20
                print("Error in write_out_thickened_bdf")
                print("Have not programmed write_out_thickened_bdf for Hex20")
                return
            else:
                print("Error in write_out_thickened_bdf")
                print("CHEXA encountered with unexpected number of nodes")
                return
        elif t == 14:
            # this is a CPENTA element 
            if len(E2N_offset[EID]) == 6:
                # It's a PENT6
                L = "CPENTA  "
                L += create_padded_bulkdata_field(EID)
                L += create_padded_bulkdata_field(PID)
                L += create_padded_bulkdata_field(E2N_offset[EID][0])  # N1
                L += create_padded_bulkdata_field(E2N_offset[EID][1])  # N2
                L += create_padded_bulkdata_field(E2N_offset[EID][2])  # N3
                L += create_padded_bulkdata_field(E2N_offset[EID][3])  # N4
                L += create_padded_bulkdata_field(E2N_offset[EID][4])  # N5
                L += create_padded_bulkdata_field(E2N_offset[EID][5])  # N6
            elif len(E2N_offset[EID]) == 15:
                # It's A PENT15
                print("Error in write_out_thickened_bdf")
                print("Have not programmed write_out_thickened_bdf for PENT15")
                return
            else:
                print("Error in write_out_thickened_bdf")
                print("CPENTA encountered with unexpected number of nodes")
                return
        else:
            print("Error in write_out_thickened_bdf.")
            print("Unknown element type.")
    f.close()
    return
#}}}

def create_padded_bulkdata_field(field_in): # {{{
    """ Pads a field with spaces till it fits in an 8 character slot
    """
    N_front_pad = min(1,8-len(str(field_in)))
    N_aft_pad = 8 - len(str(field_in)) - N_front_pad
    padded_field = " " * N_front_pad + str(field_in) + " " * N_aft_pad
    return padded_field
#}}}

def write_gridpoint_data_to_file(filename, nodes_offset): # {{{
    # DO NOT JUDGE ME.
    # THIS IS INFINITELY HARDER THAN YOU WOULD THINK IT IS.
    # NASTRAN IS CURSED. NUMBERS AREN'T REAL. THE LETTER E IS INFINITE.
    # EMBRACE THE VOID.
    f = open(filename,"a")
    for NID in list(nodes_offset.keys()):
        # initializing data
        x = nodes_offset[NID][0]
        y = nodes_offset[NID][1]
        z = nodes_offset[NID][2]

        L_x = 6
        L_y = 6
        L_z = 6
        
        x_string = "{x:.{L}e}".format(x=x, L=L_x)
        y_string = "{y:.{L}e}".format(y=y, L=L_y)
        z_string = "{z:.{L}e}".format(z=z, L=L_z)

        # check if has leading "-"
        if x_string.startswith("-"):
            L_x += -1
        if y_string.startswith("-"):
            L_y += -1
        if z_string.startswith("-"):
            L_z += -1

        # shorten the number of sigfigs we can have to accommodate the "-"
        x_string = "{x:.{L}e}".format(x=x, L=L_x)
        y_string = "{y:.{L}e}".format(y=y, L=L_y)
        z_string = "{z:.{L}e}".format(z=z, L=L_z)

        # replacing "e" with "E"
        x_string = x_string.replace("e","E")
        y_string = y_string.replace("e","E")
        z_string = z_string.replace("e","E")

        # replacing "E+00" with ""
        x_string = x_string.replace("E+00","")
        y_string = y_string.replace("E+00","")
        z_string = z_string.replace("E+00","")

        # replacing "E-00" with ""
        x_string = x_string.replace("E-00","")
        y_string = y_string.replace("E-00","")
        z_string = z_string.replace("E-00","")

        # replace "-0" with "-"
        x_string = x_string.replace("-0","-")
        y_string = y_string.replace("-0","-")
        z_string = z_string.replace("-0","-")

        # replace "+0" with "+"
        x_string = x_string.replace("+0","+")
        y_string = y_string.replace("+0","+")
        z_string = z_string.replace("+0","+")

        # if the strings contain E, subtract 1 from L to compensate
        matchx = re.search("E",x_string)
        if matchx:
            L_x += - 1
            front = float(x_string.split("E")[0])
            back = x_string.split("E")[1]
            # Add back 2 and subtract off every exponent term that is needed.
            # Only 2 terms can be in the exponent.
            # For large numbers, this step is cancelled out.
            L_x += 2 - len(back)
            x_string = "{x:.{L}f}".format(x=front, L=L_x - 1) + back

        # if the strings contain E, subtract 1 from L to compensate
        matchy = re.search("E",y_string)
        if matchy:
            L_y += - 1
            front = float(y_string.split("E")[0])
            back = y_string.split("E")[1]
            # Add back 2 and subtract off every exponent term that is needed.
            # Only 2 terms can be in the exponent.
            # For large numbers, this step is cancelled out.
            L_y += 2 - len(back)
            y_string = "{y:.{L}f}".format(y=front, L=L_y - 1) + back

        # if the strings contain E, subtract 1 from L to compensate
        matchz = re.search("E",z_string)
        if matchz:
            L_z += - 1
            front = float(z_string.split("E")[0])
            back = z_string.split("E")[1]
            # Add back 2 and subtract off every exponent term that is needed.
            # Only 2 terms can be in the exponent.
            # For large numbers, this step is cancelled out.
            L_z += 2 - len(back)
            z_string = "{z:.{L}f}".format(z=front, L=L_z - 1) + back

        # Creating GRID card
        Grid_Card = "GRID    "
        # Appending NID as a string
        N_front_pad = min(1,8-len(str(NID)))
        N_aft_pad = 8 - len(str(NID)) - N_front_pad
        NID_string = " " * N_front_pad + str(NID) + " " * N_aft_pad
        Grid_Card += NID_string
        # Assuming no custom coordinate system
        Grid_Card += " " * 8
        # Appending location
        Grid_Card += x_string + y_string + z_string
        f.write(Grid_Card + "\n")
    f.close()
    return
# }}}

def create_thickened_E2N(E2N, nodes): # {{{
    # get highest element ID
    highest_EID = max(list(E2N.keys()))
    # get highest node ID
    NID_offset = list(nodes.keys())[int(len(nodes)/2)-1]
    # create E2N for hex elements
    E2N_offset = {}
    for E in list(E2N.keys()):
        EID = E + highest_EID
        N1 = E2N[E][0]
        N2 = E2N[E][1]
        N3 = E2N[E][2]
        N4 = E2N[E][3]
        N5 = N1 + NID_offset
        N6 = N2 + NID_offset
        N7 = N3 + NID_offset
        N8 = N4 + NID_offset
        E2N_offset[EID] = [N1, N2, N3, N4, N5, N6, N7, N8]
    return E2N_offset
    #}}}

def create_thickened_nodes(nodes, thickness, N2NormVec): # {{{
    """ Create nodes of the to be created hex elements by thickening the
    shell mesh along the nodal normals
    """
    # get highest node ID
    highest_NID = max(list(nodes.keys()))
    # the new hex elements will be equivolenced to the 
    nodes_offset = nodes
    for N in list(nodes.keys()):
        NID = N + highest_NID
        # get the normal vector for this node 
        V_norm = N2NormVec[N]
        # compute the new positions of the new node
        X_new = nodes[N][0] + V_norm[0] * thickness
        Y_new = nodes[N][1] + V_norm[1] * thickness
        Z_new = nodes[N][2] + V_norm[2] * thickness
        nodes_offset[NID] = [X_new, Y_new, Z_new]
    return nodes_offset
    # }}}

def get_N2E(E2N): # {{{
    """ Turns the E2N around, giving a dict of N2E
    """
    for EID, Element in E2N.items():
        # go through nodes in every element
        for NID in Element:
            # if the node's not in N2E yet, prepare for it to be
            if NID not in N2E:
                N2E[NID] = []
            # store the EID with that node ID we're on
            N2E[NID].append(EID)
# }}}

def get_N2NormVec(E2NormVec, E2N, nodes): # {{{
    N2NormVec = {}
    N2E = get_N2E(E2N)
    
    for NID in nodes:
        elms_with_this_node = N2E[NID]
        X_comp = 0
        Y_comp = 0
        Z_comp = 0
        for EID in elms_with_this_node:
            X_comp += E2NormVec[EID][0]
            Y_comp += E2NormVec[EID][1]
            Z_comp += E2NormVec[EID][2]
        mag = ((X_comp**2) + (Y_comp**2) + (Z_comp**2))**0.5
        X = X_comp/mag
        Y = Y_comp/mag
        Z = Z_comp/mag
        N2NormVec[NID] = [X, Y, Z]
    return N2NormVec
# }}}

def get_E2NormVec(nodes, E2N): #{{{
    """ Compute the normal vector elements
    """
    E2NormVec = {}
    for EID in list(E2N.keys()):
        NodeIDs = E2N[EID]
        these_nodes = []
        for N in NodeIDs:
            # get the X coord of this node ID
            for i in list(nodes.keys()):
                if i == N:
                    x = nodes[i][0]
                    y = nodes[i][1]
                    z = nodes[i][2]
                    these_nodes.append([N, x, y, z])
        # compute every normal vector possible
        N = these_nodes
        # Get coordinates of all four points
        P1 = np.array([N[0][1], N[0][2], N[0][3]])
        P2 = np.array([N[1][1], N[1][2], N[1][3]])
        P3 = np.array([N[2][1], N[2][2], N[2][3]])
        P4 = np.array([N[3][1], N[3][2], N[3][3]])
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
        NV = NV/mag
        E2NormVec[EID]= [NV[0], NV[1], NV[2]]
    return E2NormVec
    #}}}

def shell_mesh_loft_between_two_curves(PL1, PL2, N_e_X, N_e_Y): # {{{
    """ returns nodes, E2N, and E2T of the CQUAD4 mesh between curves
    """
    # Make shell elements ruling between the two surfaces
    # Construct E2N [Element ID to Node ID]
    E2N = make_elements_of_ruled_mesh(N_e_X, N_e_Y)

    # Make nodes on shell mesh ruled between lines
    nodes = make_nodes_of_ruled_mesh(PL1, PL2, N_e_Y)

    # Populate E2T for Ruled mesh created between L1 and L2
    E2T = {}
    for E in list(E2N.keys()):
        # CQUAD4 element type is 15
        E2T[E] = 15
    return [nodes, E2N, E2T]
# }}}

def make_elements_of_ruled_mesh(N_elms_X, N_elms_Y): # {{{
    """ Create E2N for iso CQUAD4 shell mesh
    Takes in number of elements in X and number of elements in Y
    E2N has node IDs and element Ids that will both start at 1
    """
    assert isinstance(N_elms_X,int)
    Nx = N_elms_X + 1
    Ny = N_elms_Y + 1
    EID = 0
    E2N = {}
    for j in range(Ny-1):
        for i in range(Nx-1):
            NID = 1 + Nx*j + i
            EID += 1
            N1 = NID
            N2 = 1 + Nx*(j+1) + i
            N3 = N2 + 1
            N4 = N1 + 1
            E2N[EID] = [N1, N2, N3, N4]
    return E2N
# }}}

def make_nodes_of_ruled_mesh(Nodes_1, Nodes_2, N_elms_Y): #{{{
    """ Make nodes by tracing the streamlines of the surface
    """
    nodes = {}
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
            nodes[NID] = [x, y, z]
    return nodes #}}}

def get_points_on_3_point_quadratic_fit(N_elms, points): # {{{
    """ given a number of elements, and 3 points defining a spline,
    compute the nodes on that thingy
    """
    nodes = []
    coefs_1 = get_quadratic_coefs(points)
    # unpacking x coord coefficients 
    ax = coefs_1[0][0]
    bx = coefs_1[0][1]
    cx = coefs_1[0][2]
    # unpacking y coord coefficients 
    ax = coefs_1[0][0]
    ay = coefs_1[1][0]
    by = coefs_1[1][1]
    cy = coefs_1[1][2]
    # unpacking y coord coefficients 
    az = coefs_1[2][0]
    bz = coefs_1[2][1]
    cz = coefs_1[2][2]
    N_nodes = N_elms + 1
    for i in range(N_nodes):
        t = i/N_elms
        x = ax*t**2 + bx*t + cx
        y = ay*t**2 + by*t + cy
        z = az*t**2 + bz*t + cz
        nodes.append([x, y, z])
    return nodes
# }}}

def get_quadratic_coefs(list_input): # {{{
    """ Get the coefficients for a best fit quadratic
    """
    coefs_out = []

    X = list(list(zip(*list_input))[0])
    Y = list(list(zip(*list_input))[1])
    Z = list(list(zip(*list_input))[2])

    # setting parametric parameters
    t1 = 0.0
    t2 = 0.5
    t3 = 1.0

    # getting parametric equation for X coords
    DX_inp = [[t1**2, t2**2, t3**2], [t1, t2, t3], [1, 1, 1]]
    DX = np.linalg.det(np.array(DX_inp))
    D1X_inp = [[X[0], X[1], X[2]], [t1, t2, t3], [1, 1, 1]]
    D1X = np.linalg.det(np.array(D1X_inp))
    D2X_inp = [[t1**2, t2**2, t3**2], [X[0], X[1], X[2]], [1, 1, 1]]
    D2X = np.linalg.det(np.array(D2X_inp))
    D3X_inp = [[t1**2, t2**2, t3**2], [t1, t2, t3], [X[0], X[1], X[2]]]
    D3X = np.linalg.det(np.array(D3X_inp))
    aX = D1X / DX
    bX = D2X / DX
    cX = D3X / DX
    coefs_out.append([aX, bX, cX])

    # getting parametric equation for Y coords
    DY_inp = [[t1**2, t2**2, t3**2], [t1, t2, t3], [1, 1, 1]]
    DY = np.linalg.det(np.array(DY_inp))
    D1Y_inp = [[Y[0], Y[1], Y[2]], [t1, t2, t3], [1, 1, 1]]
    D1Y = np.linalg.det(np.array(D1Y_inp))
    D2Y_inp = [[t1**2, t2**2, t3**2], [Y[0], Y[1], Y[2]], [1, 1, 1]]
    D2Y = np.linalg.det(np.array(D2Y_inp))
    D3Y_inp = [[t1**2, t2**2, t3**2], [t1, t2, t3], [Y[0], Y[1], Y[2]]]
    D3Y = np.linalg.det(np.array(D3Y_inp))
    aY = D1Y / DY
    bY = D2Y / DY
    cY = D3Y / DY
    coefs_out.append([aY, bY, cY])

    # getting parametric equation for Z coords
    DZ_inp = [[t1**2, t2**2, t3**2], [t1, t2, t3], [1, 1, 1]]
    DZ = np.linalg.det(np.array(DZ_inp))
    D1Z_inp = [[Z[0], Z[1], Z[2]], [t1, t2, t3], [1, 1, 1]]
    D1Z = np.linalg.det(np.array(D1Z_inp))
    D2Z_inp = [[t1**2, t2**2, t3**2], [Z[0], Z[1], Z[2]], [1, 1, 1]]
    D2Z = np.linalg.det(np.array(D2Z_inp))
    D3Z_inp = [[t1**2, t2**2, t3**2], [t1, t2, t3], [Z[0], Z[1], Z[2]]]
    D3Z = np.linalg.det(np.array(D3Z_inp))
    aZ = D1Z / DZ
    bZ = D2Z / DZ
    cZ = D3Z / DZ
    coefs_out.append([aZ, bZ, cZ])
    
    return coefs_out
# }}}
