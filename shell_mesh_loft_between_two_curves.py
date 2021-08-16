import numpy as np

def shell_mesh_loft_between_two_curves(PL1, PL2, N_e_X, N_e_Y):
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

def make_elements_of_ruled_mesh(N_elms_X, N_elms_Y): # {{{
    """ Create E2N for iso CQUAD4 shell mesh
    Takes in number of elements in X and number of elements in Y
    E2N has node IDs and element Ids that will both start at 1
    """
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
    # unpacking x coord coeficients 
    ax = coefs_1[0][0]
    bx = coefs_1[0][1]
    cx = coefs_1[0][2]
    # unpacking y coord coeficients 
    ax = coefs_1[0][0]
    ay = coefs_1[1][0]
    by = coefs_1[1][1]
    cy = coefs_1[1][2]
    # unpacking y coord coeficients 
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
    """ Get the coeficients for a best fit quadratic
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
