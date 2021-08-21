from mesh_utilities import *
#from shell_mesh_loft_between_two_curves import *

# Hard coded Values
# -----------------
# make three points, defining a line 1
L1 = [[0.0, 0.0, 0.0], [1.0, 0.5, 0.0], [2.0, 0.0, 0.0]]
# make three points, defining a line 2
L2 = [[0.0, 0.0, 3.0], [1.0, 1.0, 3.0], [2.0, 0.0, 3.0]]
# There's elements along the curve X, and elements between the curves Y
N_e_X = 2
N_e_Y = 2

# Helper code to make the points along the curves
# -----------------------------------------------
# get the points on Line 1
PL1 = get_points_on_3_point_quadratic_fit(N_e_X, L1)
# get the points on Line 2
PL2 = get_points_on_3_point_quadratic_fit(N_e_X, L2)

# Calling the star of the show
# ============================
[nodes, E2N, E2T] = shell_mesh_loft_between_two_curves(PL1, PL2, N_e_X, N_e_Y)
