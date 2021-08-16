import re
import math as m
import numpy as np
from solid_mesh_by_thickened_shell_mesh import *
from shell_mesh_loft_between_two_curves import *

# Hard coded Values
# -----------------
# hard code thickness by which to sweep the quads into hexes
thickness = 0.125
# make three points, defining a line 1
L1 = [[0.0, 0.0, 0.0], [1.0, 0.5, 0.0], [2.0, 0.0, 0.0]]
# make three points, defining a line 2
L2 = [[0.0, 0.0, 3.0], [1.0, 1.0, 3.0], [2.0, 0.0, 3.0]]
# There's elements along the curve X, and elements between the curves Y
N_e_X = 2
N_e_Y = 2

# Helper code to make the points along the curves
# -----------------------------------------------
# get the nodes on Line 1
points_on_L1 = get_points_on_3_point_quadratic_fit(N_e_X, L1)
# get the nodes on Line 2
points_on_L2 = get_points_on_3_point_quadratic_fit(N_e_X, L2)

# Calling the star of the show
# ============================
shell_mesh_loft_between_two_curves(points_on_L1, points_on_L2, N_e_X, N_e_Y):

# [nodes, E2N, E2T] = make_shell_mesh_between_curves(N_e_X, N_e_Y, L1, L2)

argument_stack = [thickness, nodes, E2N, E2T]
data_back = solid_mesh_by_thickened_shell_mesh(argument_stack)
print(data_back)
